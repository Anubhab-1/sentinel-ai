import asyncio
import sys
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup

from config import config

# Windows: Fix for "Event loop is closed" RuntimeError on exit
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def fetch_async(session, url, method="GET", headers=None, allow_redirects=True):
    try:
        async with session.request(
            method,
            url,
            headers=headers,
            allow_redirects=allow_redirects,
            timeout=aiohttp.ClientTimeout(total=config.SCAN_TIMEOUT),
        ) as response:
            text = await response.text()
            return response, text
    except Exception:
        return None, None


async def check_port(target, port, service_name):
    """
    Checks a single port asynchronously.
    """
    conn = asyncio.open_connection(target, port)
    try:
        reader, writer = await asyncio.wait_for(
            conn, timeout=1.0
        )  # 1s timeout per port
        writer.close()
        await writer.wait_closed()
        return f"{service_name} ({port})"
    except Exception:
        return None


async def scan_ports_async(url):
    if not config.ENABLE_PORT_SCAN:
        return []

    # Robust domain extraction
    parsed = urlparse(url)
    # If no scheme, urlparse might put everything in path.
    # But our validation ensures http/https scheme, so netloc should work.
    target = parsed.netloc.split(":")[0]

    # Fallback if netloc is empty (shouldn't happen with valid URL, but safety first)
    if not target:
        target = (
            url.replace("https://", "")
            .replace("http://", "")
            .split("/")[0]
            .split(":")[0]
        )

    tasks = []
    for port, service in config.COMMON_PORTS.items():
        tasks.append(check_port(target, port, service))

    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


def analyze_header_strength(header, value):
    value = value.lower()
    if header == "Content-Security-Policy":
        return "Strong" if "unsafe-inline" not in value and "*" not in value else "Weak"
    if header == "X-Frame-Options":
        return "Strong" if value in ["deny", "sameorigin"] else "Weak"
    if header == "Strict-Transport-Security":
        return "Strong" if "max-age" in value and "31536000" in value else "Weak"
    return "Strong"


async def analyze_https_enforcement_async(session, url):
    result = {
        "https_only": False,
        "redirects_to_https": False,
        "http_accessible": False,
    }
    parsed = urlparse(url)

    # Check HTTP
    http_url = "http://" + parsed.netloc
    resp_http, _ = await fetch_async(session, http_url, allow_redirects=False)

    if resp_http:
        if resp_http.status in [301, 302, 307, 308]:
            # Check where it redirects to
            location = resp_http.headers.get("Location", "")
            if location.startswith("https://"):
                result["redirects_to_https"] = True
        else:
            result["http_accessible"] = True

    # Check HTTPS
    resp_https, _ = await fetch_async(session, "https://" + parsed.netloc)
    if resp_https:
        result["https_only"] = True

    return result


async def scan_website(url):
    findings = []
    metadata = {
        "reachable": True,
        "uses_js": False,
        "uses_forms": False,
        "https_context": {},
        "header_consensus": {},
    }

    # Run Port Scan in parallel with Web Scan?
    # For now, let's keep them concurrent but managed within this function.

    # 1. Port Scan
    found_ports = await scan_ports_async(url)
    if found_ports:
        # Filter out standard Web ports (80, 443) from being flagged as "High" risk
        risky_ports = [
            p for p in found_ports if "HTTP (80)" not in p and "HTTPS (443)" not in p
        ]

        if risky_ports:
            findings.append(
                {
                    "issue": "Exposed Network Services",
                    "header": "Port Security",
                    "severity": "High",
                    "reasons": [f"Open ports detected: {', '.join(risky_ports)}"],
                    "recommendation": "Close unused ports and use a firewall to restrict access.",
                }
            )

    # 2. Web Scan (Headers & Content)
    async with aiohttp.ClientSession() as session:
        # Launch generic and browser-like requests concurrently
        task_generic = fetch_async(session, url)
        task_browser = fetch_async(session, url, headers={"User-Agent": "Mozilla/5.0"})
        task_https = analyze_https_enforcement_async(session, url)

        (resp_generic, text_generic), (resp_browser, text_browser), https_context = (
            await asyncio.gather(task_generic, task_browser, task_https)
        )

        metadata["https_context"] = https_context

        valid_responses = []
        if resp_generic:
            valid_responses.append(resp_generic)
        if resp_browser:
            valid_responses.append(resp_browser)

        if not valid_responses:
            metadata["reachable"] = False
            return findings, metadata

        # Content Analysis (from browser alias)
        if text_browser:
            soup = BeautifulSoup(text_browser, "html.parser")
            metadata["uses_js"] = bool(soup.find("script"))
            metadata["uses_forms"] = bool(soup.find("form"))

            # Technology Fingerprinting
            technologies = set()

            # 1. From Headers
            for r in valid_responses:
                if "Server" in r.headers:
                    technologies.add(f"Server: {r.headers['Server']}")
                if "X-Powered-By" in r.headers:
                    technologies.add(f"Powered By: {r.headers['X-Powered-By']}")
                if "X-AspNet-Version" in r.headers:
                    technologies.add("ASP.NET")

            # 2. From HTML
            if soup.select('meta[name="generator"]'):
                meta_gen = soup.select_one('meta[name="generator"]').get("content", "")
                if meta_gen:
                    technologies.add(f"Generator: {meta_gen}")

            scripts = [
                s.get("src", "").lower()
                for s in soup.find_all("script")
                if s.get("src")
            ]
            full_scripts = " ".join(scripts)

            if "jquery" in full_scripts:
                technologies.add("jQuery")
            if "react" in full_scripts or "_react" in full_scripts:
                technologies.add("React")
            if "vue" in full_scripts or "vue.js" in full_scripts:
                technologies.add("Vue.js")
            if "bootstrap" in full_scripts:
                technologies.add("Bootstrap")
            if "wp-content" in full_scripts or "wp-includes" in full_scripts:
                technologies.add("WordPress")

            metadata["technologies"] = list(technologies)

        # Header Analysis
        combined_headers = {}
        # Merge headers to be safe (browser headers usually preferred)
        for r in valid_responses:
            combined_headers.update(r.headers)

        for header in config.SECURITY_HEADERS:
            # Check consensus - did we see it in ALL responses or ANY?
            # Let's check strictness: if it's missing in ANY response, it's a potential issue,
            # but usually we care about the main browser response.
            # Let's stick to the previous array logic but adapted.

            obs = []
            for r in valid_responses:
                val = r.headers.get(header)
                if val:
                    obs.append(analyze_header_strength(header, val))
                else:
                    obs.append("Missing")

            metadata["header_consensus"][header] = obs

            if obs.count("Missing") == len(obs):
                findings.append(
                    {
                        "issue": f"Missing {header}",
                        "header": header,
                        "severity": "Medium",
                        "reasons": ["Header not found in any response"],
                    }
                )
            elif obs.count("Weak") > 0:
                findings.append(
                    {
                        "issue": f"Weak {header}",
                        "header": header,
                        "severity": "Low",
                        "reasons": ["Configuration is not following best practices"],
                    }
                )

    return findings, metadata
