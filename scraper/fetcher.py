import time
import random
import urllib.parse

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    HAS_CURL_CFFI = False

class Fetcher:
    def __init__(self):
        if HAS_CURL_CFFI:
            # curl_cffi impersonates a real Chrome TLS fingerprint,
            # bypassing WAF bot detection that blocks Python requests.
            self.session = curl_requests.Session(impersonate="chrome")
        else:
            print("Warning: curl_cffi not installed. Using requests (may get 403 from protected sites).")
            print("Install with: pip install curl_cffi")
            self.session = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
            self.session.mount('http://', HTTPAdapter(max_retries=retries))
            self.session.mount('https://', HTTPAdapter(max_retries=retries))

        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
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
            self.session.get(root_url, headers=self.headers, timeout=15)
            self._primed_domains.add(root_url)
            print(f"Primed session for: {root_url}")
        except Exception as e:
            print(f"Error priming session for {root_url}: {e}")

        return root_url

    def _add_delay(self):
        """Add a random delay between requests to avoid rate limiting."""
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)

    def fetch_raw(self, url, timeout=15):
        """Fetch URL and return the raw response object (for sitemap binary content)."""
        try:
            response = self.session.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Error fetching raw {url}: {e}")
            return None

    def fetch(self, url):
        """Fetch URL and return response text, with HTTPS upgrade, session priming, and 403 retry."""
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
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
