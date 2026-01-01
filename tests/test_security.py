import unittest
from unittest.mock import patch

from security import is_safe_url, sanitize_input


class TestSecurity(unittest.TestCase):

    def test_sanitize_input(self):
        self.assertEqual(sanitize_input("  hello  "), "hello")
        self.assertEqual(sanitize_input(""), "")
        self.assertEqual(sanitize_input(None), None)

    @patch("socket.gethostbyname")
    def test_is_safe_url_public(self, mock_gethostbyname):
        # Mock Google DNS (Public)
        mock_gethostbyname.return_value = "8.8.8.8"
        self.assertTrue(is_safe_url("https://google.com"))

    @patch("socket.gethostbyname")
    def test_is_safe_url_private(self, mock_gethostbyname):
        # Mock Localhost (Private)
        mock_gethostbyname.return_value = "127.0.0.1"
        self.assertFalse(is_safe_url("http://localhost"))

        # Mock Private Network
        mock_gethostbyname.return_value = "192.168.1.1"
        self.assertFalse(is_safe_url("http://internal-admin"))

    @patch("socket.gethostbyname")
    def test_is_safe_url_invalid(self, mock_gethostbyname):
        mock_gethostbyname.side_effect = Exception("DNS Error")
        self.assertFalse(is_safe_url("http://invalid-domain"))


if __name__ == "__main__":
    unittest.main()
