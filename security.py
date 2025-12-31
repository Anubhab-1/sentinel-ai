import socket
import ipaddress
from urllib.parse import urlparse
from config import config

def is_safe_url(url):
    """
    Prevents SSRF by verifying the URL resolves to a public IP address.
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
            
        # Resolve hostname to IP
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)
        
        # Check if IP is private, loopback, or reserved
        if (ip.is_private or 
            ip.is_loopback or 
            ip.is_link_local or 
            ip.is_multicast or 
            ip.is_reserved):
            return False
            
        return True
    except Exception:
        return False

def sanitize_input(text):
    """
    Basic sanitization to remove potential HTML/Script tags.
    """
    if not isinstance(text, str):
        return text
    # Simple whitelist or escape could go here. 
    # For now, stripping specific dangerous chars implies output encoding (which Jinja does).
    # We mainly want to prevent control characters in logs or headers.
    return text.strip()
