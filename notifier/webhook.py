import logging
import requests
import json
from config.settings import settings

class WebhookNotifier:
    def __init__(self):
        self.api_url = settings.watchlist_api_url
        self.api_key = settings.watchlist_api_key

    def send_tickers(self, tickers):
        """
        Sends a list of tickers to the watchlist API.
        :param tickers: List of ticker symbols (strings)
        """
        if not tickers:
            logging.info("No tickers to send to watchlist.")
            return

        if not self.api_key:
            logging.warning("WATCHLIST_API_KEY not set. Skipping API call.")
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {"symbols": list(tickers)}
        
        try:
            logging.info(f"Sending {len(tickers)} tickers to {self.api_url}...")
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                msg = f"Successfully sent tickers. Response: {response.json()}"
                logging.info(msg)
                return True, msg
            else:
                msg = f"Failed to send tickers. Status: {response.status_code}, Body: {response.text}"
                logging.error(msg)
                return False, msg
                
        except Exception as e:
            msg = f"Error sending tickers to watchlist API: {e}"
            logging.error(msg)
            return False, msg
