from bs4 import BeautifulSoup
from urllib.parse import urljoin

class Parser:
    def parse(self, html_content):
        if not html_content:
            return None
        return BeautifulSoup(html_content, 'html.parser')

    def extract_text(self, soup, selector=None):
        if not soup:
            return ""
        
        # Default to legacy behavior: find all 'p' if selector is 'p' or None
        if not selector or selector == 'p':
            paragraphs = soup.find_all('p')
            if not paragraphs:
                return ""
                
            webpage_text = ""
            for paragraph in paragraphs:
                # Legacy code used get_text() + " "
                webpage_text += paragraph.get_text() + " "
            return webpage_text
            
        # Support for other selectors if configured
        elements = soup.select(selector)
        return " ".join([e.get_text(strip=True) for e in elements])

    def extract_links(self, soup, base_url):
        """Extracts all links from the soup, resolving relative URLs."""
        links = []
        if not soup:
            return links
            
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            links.append(full_url)
            
        return list(set(links)) # Return unique links

    def format_for_analysis(self, text, url, max_chars=3000):
        if not text:
            return None
            
        cleaned_text = ' '.join(text.split())
        encapsulated_text = f"++{{{url}}} {cleaned_text}++,"
        
        # Truncate text if it exceeds max chars
        if len(encapsulated_text) > max_chars:
            encapsulated_text = encapsulated_text[:max_chars]
        
        # Ensure text ends with "++,"
        if not encapsulated_text.endswith("++,"):
            encapsulated_text += "++,"
        
        # Remove extra "++,)" if doubled - legacy code check
        if encapsulated_text.endswith("++,++,"):
            encapsulated_text = encapsulated_text[:-4]   
        
        # Strip unwanted special characters at the end of the text
        special_chars = ['\n']
        while encapsulated_text[-1] in special_chars:
            encapsulated_text = encapsulated_text[:-1]
        
        # Append ending characters if missing
        if not encapsulated_text.endswith("++,"):
            encapsulated_text += "++,"
            
        return encapsulated_text
