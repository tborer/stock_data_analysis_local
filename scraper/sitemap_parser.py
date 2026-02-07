import requests
import gzip
import io
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import logging

class SitemapParser:
    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.max_depth = 3 # Avoid infinite loops
    
    def fetch_content(self, url):
        """Fetches URL content, handling GZIP decompression automatically if needed."""
        try:
            # fetcher.fetch returns text, but for GZIP we might need raw bytes.
            # Let's use requests directly here or modify fetcher to return response object.
            # For simplicity, using requests directly for XML/GZIP fetching as fetcher.fetch returns response.text
            # which might already decode GZIP if Content-Encoding header is set.
            # However, sitemaps often end in .gz and might not have correct headers from some providers.
            
            response = requests.get(url, headers=self.fetcher.headers, timeout=10)
            response.raise_for_status()
            
            if url.endswith('.gz'):
                try:
                    return gzip.decompress(response.content)
                except OSError:
                    # Maybe it wasn't actually gzipped or auto-decoded
                    return response.content
            
            return response.content
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [403, 404]:
                logging.warning(f"Sitemap not found or accessible ({e.response.status_code}): {url}")
            else:
                logging.error(f"HTTP Error fetching sitemap {url}: {e}")
            return None
        except Exception as e:
            logging.error(f"Error fetching sitemap {url}: {e}")
            return None

    def extract_urls(self, xml_content):
        """Parses XML and returns a list of URLs and whether they are sitemaps."""
        urls = []
        try:
            # Register namespaces as per user's legacy code structure
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # ElementTree does not support a global namespace register easily in all versions, 
            # but we can use the dictionary in find/findall.
            
            root = ET.fromstring(xml_content)
            
            # Look for normal url entries
            for url_tag in root.findall('ns:url', namespaces):
                loc = url_tag.find('ns:loc', namespaces)
                if loc is not None and loc.text:
                    urls.append({'url': loc.text.strip(), 'is_sitemap': False})

            # Look for sitemap entries (sitemapindex)
            for sitemap_tag in root.findall('ns:sitemap', namespaces):
                loc = sitemap_tag.find('ns:loc', namespaces)
                if loc is not None and loc.text:
                    urls.append({'url': loc.text.strip(), 'is_sitemap': True})
            
            # Fallback: if no namespaced items found (e.g. different schema or no namespace), 
            # try the iterative approach
            if not urls:
                for elem in root.iter():
                    if 'loc' in elem.tag:
                        url = elem.text.strip()
                        is_sitemap = 'sitemap' in root.tag or url.endswith('.xml') or url.endswith('.gz')
                        urls.append({'url': url, 'is_sitemap': is_sitemap})
                        
        except ET.ParseError as e:
            logging.error(f"Error parsing XML: {e}")
            
        return urls

    def get_article_urls(self, start_url, max_urls=400, include_filters=None):
        """
        Recursively finds article URLs starting from a sitemap index.
        Breadth-first search to find content quickly.
        
        Args:
            start_url (str): The URL of the sitemap to start with.
            max_urls (int): Maximum number of article URLs to return.
            include_filters (list): List of strings. If provided, only URLs containing
                                    at least one of these strings will be included.
        """
        article_urls = []
        to_visit = [start_url]
        visited = set()
        
        while to_visit and len(article_urls) < max_urls:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue
            
            visited.add(current_url)
            print(f"Parsing sitemap: {current_url}")
            
            content = self.fetch_content(current_url)
            if not content:
                continue
                
            found_items = self.extract_urls(content)
            
            for item in found_items:
                if len(article_urls) >= max_urls:
                    break
                
                if item['is_sitemap']:
                    if item['url'] not in visited:
                        to_visit.append(item['url'])
                else:
                    # Apply filters if any
                    if include_filters:
                        # Check if URL contains any of the required substrings
                        if not any(f in item['url'] for f in include_filters):
                            continue
                            
                    article_urls.append(item['url'])
        
        return article_urls[:max_urls]
