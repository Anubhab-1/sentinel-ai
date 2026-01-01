import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from scanner import scan_website

@pytest.mark.asyncio
async def test_scan_website_reachable():
    # Mock aiohttp.ClientSession
    with patch('aiohttp.ClientSession') as MockSession:
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
            "Server": "nginx"
        }
        mock_response.text.return_value = "<html><head><script src='jquery.js'></script></head><body><h1>Hello</h1></body></html>"
        
        # We need to ensure request() returns this mock_response context manager
        mock_request_ctx = AsyncMock()
        mock_request_ctx.__aenter__.return_value = mock_response
        mock_session_instance.request.return_value = mock_request_ctx
        
        findings, metadata = await scan_website("https://example.com")
        
        # Assertions
        assert metadata["reachable"] is True
        assert "jQuery" in metadata["technologies"]
        assert "Server: nginx" in metadata["technologies"]
        assert len(findings) == 0 # All headers are strong/present

@pytest.mark.asyncio
async def test_scan_website_missing_headers():
    with patch('aiohttp.ClientSession') as MockSession:
        mock_session_instance = MockSession.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {} # No security headers
        mock_response.text.return_value = "<html></html>"
        
        mock_request_ctx = AsyncMock()
        mock_request_ctx.__aenter__.return_value = mock_response
        mock_session_instance.request.return_value = mock_request_ctx
        
        findings, metadata = await scan_website("https://insecure.com")
        
        assert len(findings) > 0
        issues = [f['issue'] for f in findings]
        assert "Missing Content-Security-Policy" in issues
        assert "Missing X-Frame-Options" in issues
