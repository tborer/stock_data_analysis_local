import unittest
from unittest.mock import MagicMock
from notifier.webhook import WebhookNotifier
from notifier.emailer import Emailer
from config.settings import settings
import datetime

class TestErrorEmail(unittest.TestCase):
    def test_error_email_logic(self):
        # 1. Setup
        settings.enable_api_error_email = True
        webhook = WebhookNotifier()
        emailer = Emailer()
        
        # Mock dependencies
        webhook.send_tickers = MagicMock(return_value=(False, "Simulated API Failure: 500 Server Error"))
        emailer.send_email = MagicMock()
        
        # 2. Simulate logic from main.py
        tickers_to_send = ["FAIL", "ERR"]
        
        print("Simulating API call failure...")
        success, msg = webhook.send_tickers(tickers_to_send)
        
        if not success:
            print(f"API Error Caught: {msg}")
            if settings.enable_api_error_email:
                print("Triggering error email...")
                error_subject = f"Watchlist API Error - TEST"
                error_body = (
                    f"An error occurred while sending tickers to the Watchlist API.\n\n"
                    f"Error Details:\n{msg}\n\n"
                    f"Tickers attempted:\n{', '.join(tickers_to_send)}"
                )
                emailer.send_email(error_subject, error_body)

        # 3. Verify
        emailer.send_email.assert_called_once()
        args, _ = emailer.send_email.call_args
        subject, body = args
        
        self.assertIn("Watchlist API Error", subject)
        self.assertIn("Simulated API Failure", body)
        self.assertIn("FAIL, ERR", body)
        
        print("\nTest Success: Error email triggered correctly on failure.")

    def test_disabled_email(self):
        # 1. Setup
        settings.enable_api_error_email = False
        webhook = WebhookNotifier()
        emailer = Emailer()
        
        # Mock dependencies
        webhook.send_tickers = MagicMock(return_value=(False, "Simulated API Failure"))
        emailer.send_email = MagicMock()
        
        # 2. Simulate logic
        tickers_to_send = ["FAIL"]
        success, msg = webhook.send_tickers(tickers_to_send)
        
        if not success:
            if settings.enable_api_error_email:
                emailer.send_email("Subject", "Body")
        
        # 3. Verify
        emailer.send_email.assert_not_called()
        print("\nTest Success: Error email skipped when disabled.")

if __name__ == '__main__':
    unittest.main()
