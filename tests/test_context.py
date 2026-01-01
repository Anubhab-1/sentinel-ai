import pytest
from context import adjust_severity

def test_adjust_severity_csp_no_js():
    finding = {"header": "Content-Security-Policy", "severity": "High", "reasons": []}
    metadata = {"uses_js": False}
    severity = adjust_severity(finding, metadata)
    assert severity == "Low"
    assert "No JavaScript detected" in finding["reasons"][0]

def test_adjust_severity_csp_https_only():
    finding = {"header": "Content-Security-Policy", "severity": "High", "reasons": []}
    metadata = {"uses_js": True, "https_context": {"https_only": True}}
    severity = adjust_severity(finding, metadata)
    assert severity == "Medium"
    assert "HTTPS enforced" in finding["reasons"][0]

def test_adjust_severity_xfo_no_interactive():
    finding = {"header": "X-Frame-Options", "severity": "Medium", "reasons": []}
    metadata = {"uses_js": False, "uses_forms": False}
    severity = adjust_severity(finding, metadata)
    assert severity == "Low"
    assert "No interactive UI detected" in finding["reasons"][0]

def test_adjust_severity_xfo_https_only():
    finding = {"header": "X-Frame-Options", "severity": "Medium", "reasons": []}
    metadata = {"uses_js": True, "uses_forms": True, "https_context": {"https_only": True}}
    # Should reduce to Low
    severity = adjust_severity(finding, metadata)
    assert severity == "Low"

def test_adjust_severity_hsts_http_accessible():
    finding = {"header": "Strict-Transport-Security", "severity": "Medium", "reasons": []}
    metadata = {"https_context": {"http_accessible": True}}
    severity = adjust_severity(finding, metadata)
    assert severity == "High"
    assert "Site accessible over HTTP" in finding["reasons"][0]

def test_adjust_severity_hsts_redirects():
    finding = {"header": "Strict-Transport-Security", "severity": "High", "reasons": []}
    metadata = {"https_context": {"redirects_to_https": True, "http_accessible": False}}
    severity = adjust_severity(finding, metadata)
    assert severity == "Medium"
    assert "HTTP redirects to HTTPS" in finding["reasons"][0]

def test_adjust_severity_referrer_policy():
    finding = {"header": "Referrer-Policy", "severity": "Medium", "reasons": []}
    metadata = {}
    severity = adjust_severity(finding, metadata)
    assert severity == "Low"

def test_adjust_severity_unknown_header():
    finding = {"header": "Unknown-Header", "severity": "Critical", "reasons": []}
    metadata = {}
    severity = adjust_severity(finding, metadata)
    assert severity == "Critical"
