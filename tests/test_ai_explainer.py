import pytest
from unittest.mock import patch, MagicMock
from ai_explainer import explain_finding, _explain_with_cache

# Clear lru_cache before each test to ensure fresh runs
@pytest.fixture(autouse=True)
def clear_cache():
    _explain_with_cache.cache_clear()

def test_explain_finding_offline_mode():
    """Test that the explainer returns fallback text when no API key is present."""
    with patch('config.config.PERPLEXITY_API_KEY', None):
        issue = "Missing Content-Security-Policy"
        explanation = explain_finding(issue, "Medium", ["Header missing"])
        assert "Offline Mode" in explanation
        assert "Cross-Site Scripting (XSS)" in explanation

def test_explain_finding_generic_offline():
    """Test generic fallback if issue is not in known fallback keys."""
    with patch('config.config.PERPLEXITY_API_KEY', None):
        issue = "Unknown Issue"
        explanation = explain_finding(issue, "Low", [])
        assert "Security header configuration is critical" in explanation

def test_explain_finding_api_success():
    """Test successful API call to Perplexity."""
    with patch('config.config.PERPLEXITY_API_KEY', 'test-key'):
        with patch('requests.post') as mock_post:
            # Mock a successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "AI Explanation"}}]
            }
            mock_post.return_value = mock_response

            explanation = explain_finding("Weak Header", "Low", ["Test"])
            
            assert explanation == "AI Explanation"
            mock_post.assert_called_once()
            assert "Bearer test-key" in mock_post.call_args[1]['headers']['Authorization']

def test_explain_finding_api_rate_limit():
    """Test handling of 429 Rate Limit."""
    with patch('config.config.PERPLEXITY_API_KEY', 'test-key'):
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_post.return_value = mock_response

            explanation = explain_finding("Weak Header", "Low", ["Test"])
            
            assert "Rate Limit Reached" in explanation

def test_explain_finding_api_error_fallback():
    """Test fallback when API returns 500 or raises exception."""
    with patch('config.config.PERPLEXITY_API_KEY', 'test-key'):
        with patch('requests.post') as mock_post:
            # Case 1: Exception
            mock_post.side_effect = Exception("Network Error")
            
            issue = "Missing X-Frame-Options"
            explanation = explain_finding(issue, "Medium", [])
            
            # Should fall back to offline dictionary
            assert "Clickjacking" in explanation
            
            # Case 2: 500 Error (should fall through to fallback inside the logic?)
            # The current logic only logs 500 and returns None explicitly? 
            # No, it falls out of the if/else block if status != 200 and != 429?
            # Let's check the code: 
            # if 200 -> return
            # elif 429 -> return warning
            # else -> log warning. Then what?
            # It falls out of the 'if config.PERPLEXITY_API_KEY' block? 
            # No, it's inside. It logs and then exits the if/try/else?
            # Actually, `fetch_async` (wait, this is ai_explainer)
            
            # Code Review of ai_explainer.py:
            # if config.PERPLEXITY_API_KEY:
            #    try: 
            #       ... 
            #       if 200: return ...
            #       elif 429: return ...
            #       else: log warning
            #    except Exception: log error
            # else: log no key
            
            # Point is: if 500, it falls out of the if/elif/else chain and proceeds to "2. Smart Fallback"
            
            mock_post.side_effect = None
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response
            
            explanation_500 = explain_finding(issue, "Medium", [])
            assert "Clickjacking" in explanation_500
