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
            root = ET.fromstring(xml_content)
            
            # Namespaces are annoying in XML parsing. Strip them or handle them.
            # Simple approach: iterate all elements and look for 'loc'
            
            for elem in root.iter():
                if 'loc' in elem.tag:
                    url = elem.text.strip()
                    # Check if it looks like a sitemap (often in <sitemap> tag or ends in .xml/.gz)
                    # But simpler to just check parent tag
                    parent = None 
                    # ElementTree doesn't support getparent easily without iterparse or lxml
                    # Let's rely on basic suffix logic or tag name if possible?
                    # or better, iterate specific tags if strict.
                    # Standard sitemaps: <urlset><url><loc>...</loc>...</url></urlset> -> Page
                    # Sitemap index: <sitemapindex><sitemap><loc>...</loc>...</sitemap></sitemapindex> -> Sitemap
                    
                    is_sitemap = False
                    if 'sitemapindex' in root.tag or url.endswith('.xml') or url.endswith('.gz'):
                        is_sitemap = True
                        
                    urls.append({'url': url, 'is_sitemap': is_sitemap})
                    
        except ET.ParseError as e:
            logging.error(f"Error parsing XML: {e}")
            
        return urls

    def get_article_urls(self, start_url, max_urls=400):
        """
        Recursively finds article URLs starting from a sitemap index.
        Breadth-first search to find content quickly.
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
                    article_urls.append(item['url'])
        
        return article_urls[:max_urls]
