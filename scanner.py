import asyncio
import sys
from urllib.parse import urlparse, parse_qs

import aiohttp
from bs4 import BeautifulSoup
from scanners.injection import check_sql_injection, check_xss

from config import config
from crawler import crawl

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


async def _scan_single_page(session, url):
    """
    Helper: Scans a single URL for headers, content, and injections.
    Returns: (findings_list, metadata_dict)
    """
    findings = []
    metadata = {
        "url": url,
        "uses_js": False,
        "uses_forms": False,
        "technologies": [],
        "headers": {}
    }

    # 1. Fetch
    task_generic = fetch_async(session, url)
    task_browser = fetch_async(session, url, headers={"User-Agent": "Mozilla/5.0"})
    task_https = analyze_https_enforcement_async(session, url)

    (resp_generic, text_generic), (resp_browser, text_browser), https_context = (
        await asyncio.gather(task_generic, task_browser, task_https)
    )

    metadata["https_context"] = https_context
    valid_responses = [r for r in [resp_generic, resp_browser] if r]

    if not valid_responses:
        return findings, metadata

    # 2. Content Analysis
    if text_browser:
        soup = BeautifulSoup(text_browser, "html.parser")
        metadata["uses_js"] = bool(soup.find("script"))
        metadata["uses_forms"] = bool(soup.find("form"))

        # Tech Fingerprint
        technologies = set()
        for r in valid_responses:
            if "Server" in r.headers: technologies.add(f"Server: {r.headers['Server']}")
            if "X-Powered-By" in r.headers: technologies.add(f"Powered By: {r.headers['X-Powered-By']}")
        
        scripts = " ".join([s.get("src", "").lower() for s in soup.find_all("script") if s.get("src")])
        if "jquery" in scripts: technologies.add("jQuery")
        if "react" in scripts: technologies.add("React")
        if "bootstrap" in scripts: technologies.add("Bootstrap")
        if "wp-content" in scripts: technologies.add("WordPress")
        
        metadata["technologies"] = list(technologies)

    # 3. Header Analysis
    combined_headers = {}
    for r in valid_responses:
        combined_headers.update(r.headers)
    metadata["headers"] = dict(combined_headers) # Store for debugging

    for header in config.SECURITY_HEADERS:
        val = combined_headers.get(header)
        strength = analyze_header_strength(header, val) if val else "Missing"
        
        if strength == "Missing":
            findings.append({
                "issue": f"Missing {header}",
                "header": header,
                "severity": "Medium",
                "reasons": ["Header not found in any response"],
                "url": url # Tag finding with URL
            })
        elif strength == "Weak":
            findings.append({
                "issue": f"Weak {header}",
                "header": header,
                "severity": "Low",
                "reasons": ["Configuration is not following best practices"],
                "url": url
            })

    # 4. Deep Scan (Injection)
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if params:
        injection_findings = await asyncio.gather(
            check_sql_injection(session, url, params),
            check_xss(session, url, params)
        )
        for f_list in injection_findings:
            # Tag injection findings
            for f in f_list:
                f["url"] = url
            findings.extend(f_list)

    return findings, metadata


async def scan_website(url):
    """
    Main Entry: Crawls the domain and scans discovered pages.
    """
    # 1. Crawl Phase
    print(f"🕷️  Crawling started for {url}...")
    target_urls = await crawl(url, max_pages=10)
    print(f"🕷️  Crawl complete. Found {len(target_urls)} pages.")

    all_findings = []
    
    # Global Metadata Aggregate
    metadata = {
        "reachable": True,
        "scanned_pages": target_urls,
        "scanned_count": len(target_urls),
        "technologies": set(),
        "https_context": {}, 
        "header_consensus": {} # Keep for backward compatibility
    }

    # 2. Port Scan (Domain Level - Run once)
    ports = await scan_ports_async(url)
    if ports:
        risky_ports = [p for p in ports if "HTTP (80)" not in p and "HTTPS (443)" not in p]
        if risky_ports:
            all_findings.append({
                "issue": "Exposed Network Services",
                "severity": "High",
                "reasons": [f"Open ports: {', '.join(risky_ports)}"],
                "recommendation": "Close unused ports."
            })

    # 3. Scan Pages (Concurrently)
    async with aiohttp.ClientSession() as session:
        # Batching could be added here, but for 10 pages, gather is fine.
        tasks = [_scan_single_page(session, target) for target in target_urls]
        results = await asyncio.gather(*tasks)

        for page_findings, page_meta in results:
            all_findings.extend(page_findings)
            
            # Aggregate Tech
            for tech in page_meta.get("technologies", []):
                metadata["technologies"].add(tech)
            
            # Take HTTPS context from the main homepage (or first successful one)
            if page_meta["url"] == url or not metadata["https_context"]:
                metadata["https_context"] = page_meta.get("https_context", {})

    # Final Cleanup
    metadata["technologies"] = list(metadata["technologies"])

    # Deduplication Logic
    # Many headers will be missing on ALL pages. We don't want 10x "Missing X-Frame-Options".
    # Strategy: Group by Issue Name
    unique_findings = {}
    for f in all_findings:
        key = f["issue"]
        if key not in unique_findings:
            unique_findings[key] = f
            unique_findings[key]["affected_urls"] = [f.get("url", url)]
        else:
            if f.get("url") not in unique_findings[key]["affected_urls"]:
                unique_findings[key]["affected_urls"].append(f.get("url"))
    
    # Convert back to list
    final_findings = list(unique_findings.values())

    return final_findings, metadata
