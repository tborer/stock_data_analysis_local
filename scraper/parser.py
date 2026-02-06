from bs4 import BeautifulSoup

class Parser:
    def parse(self, html_content):
        if not html_content:
            return None
        return BeautifulSoup(html_content, 'html.parser')

    def extract_text(self, soup, selector=None):
        if not soup:
            return ""
        
        if selector:
            elements = soup.select(selector)
            return " ".join([e.get_text(strip=True) for e in elements])
        
        # Default: extract all paragraphs if no selector
        paragraphs = soup.find_all('p')
        return " ".join([p.get_text(strip=True) for p in paragraphs])

    def extract_links(self, soup, base_url):
        # Placeholder for sitemap or link extraction logic
        pass
