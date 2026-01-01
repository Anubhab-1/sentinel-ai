
import pytest
from unittest.mock import MagicMock, AsyncMock
from scanners.injection import check_sql_injection, check_xss

@pytest.mark.asyncio
async def test_check_sql_injection_positive():
    # Setup
    url = "http://example.com/search?q=test"
    params = {"q": "test"}
    
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Syntax error in SQL statement")
    
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Execute
    findings = await check_sql_injection(mock_session, url, params)
    
    # Verify
    assert len(findings) == 1
    assert findings[0]["issue"] == "Potential SQL Injection"
    assert findings[0]["severity"] == "High"

@pytest.mark.asyncio
async def test_check_sql_injection_negative():
    # Setup
    url = "http://example.com/search?q=test"
    params = {"q": "test"}
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="Search results for test")
    
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Execute
    findings = await check_sql_injection(mock_session, url, params)
    
    # Verify
    assert len(findings) == 0

@pytest.mark.asyncio
async def test_check_xss_positive():
    # Setup
    url = "http://example.com/search?q=test"
    params = {"q": "test"}
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="You searched for <script>alert('XSS')</script>")
    
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Execute
    findings = await check_xss(mock_session, url, params)
    
    # Verify
    assert len(findings) == 1
    assert findings[0]["issue"] == "Reflected XSS"
    assert findings[0]["severity"] == "High"
