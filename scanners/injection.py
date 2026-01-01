
import aiohttp
import asyncio
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# --- PAYLOADS ---
SQLI_PAYLOADS = [
    "' OR 1=1--",
    "' UNION SELECT 1,2,3--",
    "admin' --",
    "' OR '1'='1"
]

XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "javascript:alert(1)",
    "<img src=x onerror=alert(1)>"
]

async def check_sql_injection(session, url, params):
    """
    Fuzzes URL parameters with SQLi payloads.
    Returns list of findings.
    """
    findings = []
    parsed = urlparse(url)
    
    # Analyze query params
    # We iterate over each param and inject payloads
    for param_name in params:
        for payload in SQLI_PAYLOADS:
            # Construct injected URL
            injected_params = params.copy()
            injected_params[param_name] = payload
            query_string = urlencode(injected_params, doseq=True)
            
            target_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path, 
                parsed.params, query_string, parsed.fragment
            ))

            try:
                async with session.get(target_url, timeout=5) as resp:
                    text = await resp.text()
                    
                    # Heuristic Detection
                    if resp.status == 500 or "syntax error" in text.lower() or "mysql" in text.lower():
                        findings.append({
                            "issue": "Potential SQL Injection",
                            "severity": "High",
                            "reasons": [
                                f"Input '{payload}' caused 500 error or DB error message.",
                                f"Vulnerable Parameter: {param_name}"
                            ],
                            "recommendation": "Use Prepared Statements/Parameterized Queries."
                        })
                        # Stop fuzzing this param if found
                        break
            except Exception:
                pass
                
    return findings

async def check_xss(session, url, params):
    """
    Fuzzes URL parameters with Reflected XSS payloads.
    Returns list of findings.
    """
    findings = []
    parsed = urlparse(url)
    
    for param_name in params:
        for payload in XSS_PAYLOADS:
            injected_params = params.copy()
            injected_params[param_name] = payload
            query_string = urlencode(injected_params, doseq=True)
            
            target_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path, 
                parsed.params, query_string, parsed.fragment
            ))

            try:
                async with session.get(target_url, timeout=5) as resp:
                    text = await resp.text()
                    
                    # Check reflection
                    if payload in text:
                        findings.append({
                            "issue": "Reflected XSS",
                            "severity": "High",
                            "reasons": [
                                f"Payload '{payload}' was reflected in response body without escaping.",
                                f"Vulnerable Parameter: {param_name}"
                            ],
                            "recommendation": "Implement Content Security Policy (CSP) and context-aware output encoding."
                        })
                        break
            except Exception:
                pass
                
    return findings
