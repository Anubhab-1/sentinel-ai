from unittest.mock import AsyncMock, patch

import pytest

from scanner import scan_website


@pytest.mark.asyncio
async def test_scan_website_reachable():
    # Mock aiohttp.ClientSession
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session_instance = MockSession.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance

        # Mock responses
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {
            "Content-Security-Policy": "default-src 'self'",
            "Strict-Transport-Security": "max-age=31536000",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin",
            "Server": "nginx",
        }
        mock_response.text.return_value = "<html><head><script src='jquery.js'></script></head><body><h1>Hello</h1></body></html>"

        # We need to ensure request() returns this mock_response context manager
        mock_request_ctx = AsyncMock()
        mock_request_ctx.__aenter__.return_value = mock_response
        mock_session_instance.request.return_value = mock_request_ctx

        # Mock port scan to return nothing safe
        with patch("scanner.scan_ports_async", return_value=[]) as mock_ports:
            findings, metadata = await scan_website("https://example.com")

        # Assertions
        assert metadata["reachable"] is True
        assert "jQuery" in metadata["technologies"]
        assert "Server: nginx" in metadata["technologies"]
        assert len(findings) == 0  # All headers are strong/present


@pytest.mark.asyncio
async def test_scan_website_missing_headers():
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session_instance = MockSession.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}  # No security headers
        mock_response.text.return_value = "<html></html>"

        mock_request_ctx = AsyncMock()
        mock_request_ctx.__aenter__.return_value = mock_response
        mock_session_instance.request.return_value = mock_request_ctx

        # Mock port scan
        with patch("scanner.scan_ports_async", return_value=[]):
            findings, metadata = await scan_website("https://insecure.com")

        assert len(findings) > 0
        issues = [f["issue"] for f in findings]
        assert "Missing Content-Security-Policy" in issues
        assert "Missing X-Frame-Options" in issues


@pytest.mark.asyncio
async def test_scan_website_open_ports():
    with patch("aiohttp.ClientSession") as MockSession:
        # Minimal mock for the web part
        mock_session = MockSession.return_value
        mock_session.__aenter__.return_value = mock_session
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.headers = {"Content-Security-Policy": "default-src 'self'"} # Minimal safe header
        mock_resp.text.return_value = ""
        mock_req = AsyncMock()
        mock_req.__aenter__.return_value = mock_resp
        mock_session.request.return_value = mock_req

        # Test Finding Open Ports
        with patch("scanner.scan_ports_async", return_value=["FTP (21)", "SSH (22)"]):
             findings, metadata = await scan_website("https://vulnerable-ports.com")
        
        issues = [f["issue"] for f in findings]
        assert "Exposed Network Services" in issues
        risk = next(f for f in findings if f["issue"] == "Exposed Network Services")
        assert "FTP (21)" in risk["reasons"][0]
        assert "High" == risk["severity"]


from scanner import analyze_header_strength

def test_analyze_header_strength():
    assert analyze_header_strength("Content-Security-Policy", "default-src 'self'") == "Strong"
    assert analyze_header_strength("Content-Security-Policy", "unsafe-inline") == "Weak"
    assert analyze_header_strength("X-Frame-Options", "DENY") == "Strong"
    assert analyze_header_strength("X-Frame-Options", "ALLOW-FROM foo") == "Weak"
    assert analyze_header_strength("Strict-Transport-Security", "max-age=31536000") == "Strong"
    assert analyze_header_strength("Strict-Transport-Security", "max-age=300") == "Weak"

