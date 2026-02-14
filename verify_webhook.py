import unittest
from unittest.mock import patch, MagicMock
from notifier.webhook import WebhookNotifier
from config.settings import settings
import os

class TestWebhook(unittest.TestCase):
    @patch('notifier.webhook.requests.post')
    def test_send_tickers_success(self, mock_post):
        # Setup
        settings.watchlist_api_key = "test_key"
        settings.watchlist_api_url = "http://test.url"
        notifier = WebhookNotifier()
        tickers = ["AAPL", "TSLA"]
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "added": tickers}
        mock_post.return_value = mock_response
        
        # Execute
        notifier.send_tickers(tickers)
        
        # Verify
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json'], {'symbols': ['AAPL', 'TSLA']})
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer test_key')
        print("\nTest Success: requests.post called with correct payload and headers.")

    def test_send_tickers_no_key(self):
        # Setup
        settings.watchlist_api_key = None
        notifier = WebhookNotifier()
        
        # Execute
        notifier.send_tickers(["AAPL"])
        
        # Verify (printed log would show warning, here just ensure no crash)
        print("\nTest Success: Handled missing API key gracefully.")

if __name__ == '__main__':
    unittest.main()
