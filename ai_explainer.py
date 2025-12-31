import requests
import json
from config import config
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# 🧠 SMART FALLBACKS (Used if AI is offline/unconfigured)
FALLBACK_KNOWLEDGE = {
    "Content-Security-Policy": (
        "This header prevents Cross-Site Scripting (XSS) attacks by controlling "
        "which resources (scripts, images) the browser is allowed to load. "
        "Without it, attackers can inject malicious scripts to steal user data."
    ),
    "Strict-Transport-Security": (
        "HSTS enforces secure (HTTPS) connections to the server. "
        "Without it, your site is vulnerable to 'Man-in-the-Middle' attacks "
        "where hackers strip away encryption to read sensitive data."
    ),
    "X-Content-Type-Options": (
        "This header stops the browser from 'MIME-sniffing' a response away from "
        "the declared content-type. Without it, a browser might execute a legitimate "
        "image file as a malicious script."
    ),
    "X-Frame-Options": (
        "This header protects against 'Clickjacking' attacks. "
        "It prevents your site from being embedded in an iframe on a malicious site, "
        "tricking users into clicking hidden buttons."
    ),
    "Referrer-Policy": (
        "This controls how much referrer information (previous URL) is included "
        "with requests. Without it, your site might leak sensitive user URLs "
        "to third-party analytics or external links."
    )
}

@lru_cache(maxsize=100)
def _explain_with_cache(issue, severity, reasons):
    # This function expects 'reasons' to be a tuple (hashable)
    if isinstance(reasons, tuple):
        reasons_str = ", ".join(reasons)
    else:
        reasons_str = str(reasons)

    # 1. Try to ask the Real AI (Perplexity API)
    if config.PERPLEXITY_API_KEY:
        try:
            logger.info(f"Attempting AI usage with Key: {config.PERPLEXITY_API_KEY[:4]}...")
            # Perplexity API Documentation: https://docs.perplexity.ai/
            url = "https://api.perplexity.ai/chat/completions"
            
            prompt_text = (
                f"You are a cybersecurity expert. Explain the security risk of '{issue}' "
                f"(Severity: {severity}) briefly for a developer. "
                f"Context: {reasons_str}. "
                "Keep it under 3 sentences."
            )

            payload = {
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful cybersecurity assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt_text
                    }
                ]
            }
            
            headers = {
                'Authorization': f'Bearer {config.PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=config.AI_TIMEOUT)
            
            if response.status_code == 200:
                result = response.json()
                try:
                    return result['choices'][0]['message']['content'].strip()
                except (KeyError, IndexError):
                    logger.error(f"Perplexity Bad Response: {result}")
            elif response.status_code == 429:
                logger.warning(f"Perplexity Rate Limited.")
                return "⚠️ AI service is busy (Rate Limit Reached). Please wait and try again."
            else:
                logger.warning(f"Perplexity Error {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Perplexity API Error: {e}")
            # Fall through to fallback
    
    else:
        logger.warning("AI Key not found in Config. Switching to Offline Mode.")


    # 2. Smart Fallback (Offline Mode or No Key)
    # Look for keywords in the issue string
    for key, explanation in FALLBACK_KNOWLEDGE.items():
        if key in issue:
            return f"💡 (Offline Mode): {explanation}"

    return "Security header configuration is critical for preventing common web attacks like XSS and Clickjacking."

def explain_finding(issue, severity, reasons):
    # Wrapper to handle list->tuple conversion for caching
    if isinstance(reasons, list):
        reasons = tuple(reasons)
    return _explain_with_cache(issue, severity, reasons)
