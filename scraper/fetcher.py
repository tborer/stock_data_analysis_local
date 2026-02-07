import requests
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib.parse

class Fetcher:
    def __init__(self):
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Cache-Control': 'max-age=0'
        }
        self._primed_domains = set()

    @staticmethod
    def _ensure_https(url):
        """Convert http:// URLs to https:// to avoid 403 from sites that require HTTPS."""
        if url.startswith('http://'):
            return 'https://' + url[7:]
        return url

    def _prime_session(self, url):
        """Visit the root domain to establish cookies and session state."""
        parsed_url = urllib.parse.urlparse(url)
        root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        if root_url in self._primed_domains:
            return root_url

        try:
            self.session.get(root_url, headers=self.headers, timeout=10)
            self._primed_domains.add(root_url)
            print(f"Primed session for: {root_url}")
        except Exception as e:
            print(f"Error priming session for {root_url}: {e}")

        return root_url

    def _add_delay(self):
        """Add a random delay between requests to avoid rate limiting."""
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)

    def fetch(self, url):
        try:
            url = self._ensure_https(url)
            encoded_url = urllib.parse.quote(url, safe=':/?=&')
            print(f"Encoded URL: {encoded_url}")

            # Prime session before first request to establish cookies
            parsed = urllib.parse.urlparse(url)
            root_url = f"{parsed.scheme}://{parsed.netloc}"
            if root_url not in self._primed_domains:
                self._prime_session(url)
                self._add_delay()

            response = self.session.get(encoded_url, headers=self.headers, timeout=15)

            # Retry on 403 with exponential backoff and referer header
            if response.status_code == 403:
                retry_headers = self.headers.copy()
                retry_headers['Referer'] = root_url + '/'
                retry_headers['Sec-Fetch-Site'] = 'same-origin'

                for attempt in range(1, 4):
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    print(f"Received 403 for {url}. Retry {attempt}/3 after {backoff:.1f}s...")
                    time.sleep(backoff)

                    response = self.session.get(encoded_url, headers=retry_headers, timeout=15)
                    if response.status_code != 403:
                        break

            response.raise_for_status()
            self._add_delay()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
