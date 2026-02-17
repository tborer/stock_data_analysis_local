import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_URL = os.getenv("WATCHLIST_API_URL", "https://stock-trader-app-ten.vercel.app/api/watchlist/add")
API_KEY = os.getenv("WATCHLIST_API_KEY")

def debug_api():
    print("--- Starting Watchlist API Debug ---")
    print(f"URL: {API_URL}")
    print(f"API Key Present: {bool(API_KEY)}")
    
    if not API_KEY:
        print("ERROR: No API Key found in environment!")
        return

    # Test Payload
    test_tickers = ["AAPL", "TEST"]
    payload = {"symbols": test_tickers}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    print(f"\nSending payload: {json.dumps(payload)}")
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\nSUCCESS: API accepted the request.")
        else:
            print("\nFAILURE: API rejected the request.")
            
    except Exception as e:
        print(f"\nEXCEPTION: {e}")

if __name__ == "__main__":
    debug_api()
