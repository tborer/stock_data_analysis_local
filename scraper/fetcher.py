import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class Fetcher:
    def __init__(self):
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

    def fetch(self, url):
        try:
            # Encode URL to handle special characters as per legacy code
            import urllib.parse
            encoded_url = urllib.parse.quote(url, safe=':/?=&')
            print(f"Encoded URL: {encoded_url}")
            
            response = self.session.get(encoded_url, headers=self.headers, timeout=10)
            
            # Check for 403 and try to prime session
            if response.status_code == 403:
                print(f"Received 403 for {url}. Attempting to prime session...")
                
                # Extract root domain
                parsed_url = urllib.parse.urlparse(url)
                root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                
                # Visit root domain to get cookies
                try:
                    self.session.get(root_url, headers=self.headers, timeout=10)
                    print(f"Visited root URL: {root_url}")
                    
                    # Update headers with Referer and Sec-Fetch-Site
                    retry_headers = self.headers.copy()
                    retry_headers['Referer'] = root_url
                    retry_headers['Sec-Fetch-Site'] = 'same-origin'
                    
                    print(f"Retrying with Referer: {root_url}")
                    # Retry original request
                    response = self.session.get(encoded_url, headers=retry_headers, timeout=10)
                except Exception as e:
                    print(f"Error during session priming: {e}")
                    # Fall through to return the original 403 response or None
            
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
