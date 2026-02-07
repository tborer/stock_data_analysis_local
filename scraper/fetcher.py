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
            print("=" * 70)
            print("WARNING: curl_cffi is NOT installed!")
            print("Sites with WAF protection (e.g. SeekingAlpha) WILL return 403 errors.")
            print("Install with: pip install curl_cffi")
            print("=" * 70)
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
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
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
            prime_headers = self.headers.copy()
            prime_headers['Sec-Fetch-Site'] = 'none'
            response = self.session.get(root_url, headers=prime_headers, timeout=15)
            self._primed_domains.add(root_url)
            print(f"Primed session for: {root_url} (status: {response.status_code})")

            # For SeekingAlpha and similar sites, also visit a common intermediate
            # page to build up a realistic cookie/session state
            if 'seekingalpha.com' in parsed_url.netloc:
                self._add_delay()
                nav_headers = self.headers.copy()
                nav_headers['Referer'] = root_url + '/'
                nav_headers['Sec-Fetch-Site'] = 'same-origin'
                self.session.get(root_url + '/market-news', headers=nav_headers, timeout=15)
                print(f"  Navigated to market-news page to build session state")
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

    @staticmethod
    def _clean_url(url):
        """Strip fragment (#...) and fix any pre-encoded characters to avoid double-encoding."""
        # Remove fragment - it's browser-only and should never be sent to the server
        url = url.split('#')[0]
        # Decode any existing percent-encoding first, then let the HTTP library handle encoding
        # This prevents double-encoding (e.g. %3A -> %253A)
        url = urllib.parse.unquote(url)
        return url

    def fetch(self, url):
        """Fetch URL and return response text, with HTTPS upgrade, session priming, and 403 retry."""
        try:
            url = self._ensure_https(url)
            url = self._clean_url(url)
            print(f"Fetching URL: {url}")

            # Prime session before first request to establish cookies
            parsed = urllib.parse.urlparse(url)
            root_url = f"{parsed.scheme}://{parsed.netloc}"
            if root_url not in self._primed_domains:
                self._prime_session(url)
                self._add_delay()

            response = self.session.get(url, headers=self.headers, timeout=15)

            # Retry on 403 with exponential backoff and referer header
            if response.status_code == 403:
                if not HAS_CURL_CFFI:
                    print(f"  NOTE: curl_cffi not installed - 403 is likely due to TLS fingerprint detection.")
                    print(f"  Install curl_cffi to fix: pip install curl_cffi")

                retry_headers = self.headers.copy()
                retry_headers['Referer'] = root_url + '/'
                retry_headers['Sec-Fetch-Site'] = 'same-origin'

                for attempt in range(1, 4):
                    backoff = 2 ** attempt + random.uniform(0, 2)
                    print(f"Received 403 for {url}. Retry {attempt}/3 after {backoff:.1f}s...")
                    time.sleep(backoff)

                    # Re-prime session on second retry to get fresh cookies
                    if attempt == 2:
                        self._primed_domains.discard(root_url)
                        self._prime_session(url)
                        self._add_delay()

                    response = self.session.get(url, headers=retry_headers, timeout=15)
                    if response.status_code != 403:
                        break

            response.raise_for_status()
            self._add_delay()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
