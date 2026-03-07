from bs4 import BeautifulSoup
from urllib.parse import urljoin

import json

class Parser:
    def parse(self, html_content):
        if not html_content:
            return None
        return BeautifulSoup(html_content, 'html.parser')

    def extract_nextjs_data(self, soup):
        """Extracts JSON data from Next.js __NEXT_DATA__ script tag."""
        if not soup:
            return None
        
        script = soup.find('script', id='__NEXT_DATA__', type='application/json')
        if script:
            try:
                return json.loads(script.string)
            except json.JSONDecodeError:
                return None
        return None

    def extract_text(self, soup, selector=None):
        if not soup:
            return ""
        
        # Check for Next.js data first (Investing.com specific)
        nextjs_data = self.extract_nextjs_data(soup)
        if nextjs_data:
            try:
                # Try to find article body in common locations within Next.js state
                news_store = nextjs_data.get('props', {}).get('pageProps', {}).get('state', {}).get('newsStore', {})
                article = news_store.get('_article')
                
                # Check articleStore as fallback
                if not article:
                    article_store = nextjs_data.get('props', {}).get('pageProps', {}).get('state', {}).get('articleStore', {})
                    # Sometimes article content might be here, though less common for the inspected pages
                    pass

                if article and 'body' in article:
                    # Clean up HTML entities and strip tags
                    import html
                    raw_html = html.unescape(article['body'])
                    # Use BeautifulSoup to strip tags
                    clean_text = BeautifulSoup(raw_html, 'html.parser').get_text(separator=' ', strip=True)
                    return clean_text
            except Exception as e:
                print(f"Error extracting text from Next.js data: {e}")

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

    def extract_title(self, soup, selector=None):
        """Extracts the title from the soup using the selector or defaults."""
        if not soup:
            return ""

        title = ""
        
        # Check for Next.js data first (likely for Investing.com)
        nextjs_data = self.extract_nextjs_data(soup)
        if nextjs_data:
            try:
                # Try to find headline in newsStore or articleStore
                news_store = nextjs_data.get('props', {}).get('pageProps', {}).get('state', {}).get('newsStore', {})
                article = news_store.get('_article')
                if article and 'headline' in article:
                     return article['headline']
            except Exception:
                pass

        if selector:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
        
        # Fallback to standard <title> or <h1>
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
            elif soup.title:
                title = soup.title.get_text(strip=True)
                
        return title

    def extract_date(self, soup, date_regex=None, date_format=None, url=None):
        """Extracts date from the page content or URL using regex and format."""
        if not date_regex:
            return None
            
        import re
        from datetime import datetime
        from dateutil import parser as date_parser
        
        # Helper to parse date string
        def parse_date_str(d_str, d_fmt):
            try:
                # Try explicit format if provided
                if d_fmt:
                    return datetime.strptime(d_str, d_fmt)
                # Fallback to dateutil
                return date_parser.parse(d_str, fuzzy=True)
            except Exception as e:
                print(f"Error parsing date '{d_str}': {e}")
                return None

        # 1. Try regex on text content
        if soup:
            text = soup.get_text()
            match = re.search(date_regex, text)
            if match:
                date_str = match.group(1).strip()
                dt = parse_date_str(date_str, date_format)
                if dt: return dt

        # 2. Try regex on URL if provided
        if url:
            match = re.search(date_regex, url)
            if match:
                date_str = match.group(1).strip()
                dt = parse_date_str(date_str, date_format)
                if dt: return dt
        
        return None

    def extract_yahoo_news_links(self, soup, base_url):
        """Extracts unique news links from Yahoo Finance that have positive ticker stock price movements."""
        links = []
        if not soup:
            return links
        
        # Yahoo Finance news items can be sections or list items
        tiles = soup.find_all('section', {'data-testid': 'storyitem'}) + soup.find_all('li', class_='stream-item')
        
        for tile in tiles:
            # Look for the anchor tag holding the actual news link
            link_elem = tile.find('a', class_='subtle-link') or tile.find('a', class_='js-content-viewer') or tile.find('a')
            if not link_elem or 'href' not in link_elem.attrs:
                continue
                
            href = link_elem['href']
            
            # Check for stock ticker symbol
            ticker_elem = tile.find('a', class_='ticker') or tile.find('span', class_='ticker-wrapper') or tile.find('div', class_='ticker-wrapper')
            if not ticker_elem:
                # No stock symbol associated, skip since we want stock-specific news
                continue
                
            # Check the age of the news article, skip if "days ago"
            pub_elem = tile.find('div', class_='publishing')
            if pub_elem:
                pub_text = pub_elem.get_text(strip=True).lower()
                if 'd ago' in pub_text or 'days ago' in pub_text:
                    continue
            
            # Extract price change and ensure it is positive
            # Yahoo often uses fin-streamer for live quotes, with various classes or data-fields. It might also use bg-positive / bg-negative classes.
            price_change = tile.find('fin-streamer', {'data-field': 'regularMarketChangePercent'})
            if not price_change:
                price_change = tile.find('fin-streamer', {'data-field': 'regularMarketChange'})
                
            change_text = price_change.get_text(strip=True) if price_change else ""
            
            # If we don't find it via fin-streamer, check for specific classes containing the text
            if not change_text:
                positive_badge = tile.find(class_=lambda c: c and ('bg-positive' in c or 'fin-pos' in c or 'Fin(c-pos)' in c))
                negative_badge = tile.find(class_=lambda c: c and ('bg-negative' in c or 'fin-neg' in c or 'Fin(c-neg)' in c))
                if negative_badge:
                    continue # It's negative
                elif positive_badge:
                    # Proceed, it's definitely positive
                    pass
                else:
                    # Try to just find a span that contains a % sign within the ticker wrapper context
                    percent_spans = tile.find_all('span', string=lambda t: t and '%' in t)
                    for ps in percent_spans:
                        if '-' in ps.get_text():
                            change_text = ps.get_text()
                            break
                        elif '+' in ps.get_text() or any(char.isdigit() for char in ps.get_text()):
                            change_text = ps.get_text()
                            break

            # If the change text contains a minus sign, it's negative movement, so skip
            if change_text and '-' in change_text:
                continue
                
            # If we reached here, the ticker is positive (or we couldn't parse the negative movement, cautiously include)
            full_url = urljoin(base_url, href)
            links.append(full_url)
            
        return list(set(links))

    def extract_links(self, soup, base_url):
        """Extracts all links from the soup, resolving relative URLs."""
        links = []
        if not soup:
            return links
            
        # Check for Next.js data (Investing.com specific)
        nextjs_data = self.extract_nextjs_data(soup)
        if nextjs_data:
            try:
                news_store = nextjs_data.get('props', {}).get('pageProps', {}).get('state', {}).get('newsStore', {})
                # Check various lists where news might appear
                news_lists = [
                    news_store.get('_news', []),
                    news_store.get('_mostPopularNews', []),
                    news_store.get('_topArticles', []),
                    news_store.get('_breakingNews', [])
                ]
                
                for news_list in news_lists:
                    if news_list:
                        for item in news_list:
                            if isinstance(item, dict) and 'link' in item:
                                full_url = urljoin(base_url, item['link'])
                                links.append(full_url)
            except Exception as e:
                print(f"Error extracting links from Next.js data: {e}")

        # Always fallback/supplement with standard anchor tag extraction
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

    def has_paywall(self, soup, paywall_selector=None):
        """Checks if the page contains a paywall using the optionally configured CSS selectors."""
        if not soup or not paywall_selector:
            return False
            
        # Selectors can be comma-separated in the yaml config
        selectors = [s.strip() for s in paywall_selector.split(',')]
        for selector in selectors:
            try:
                if soup.select_one(selector):
                    return True
            except Exception as e:
                print(f"Error checking paywall selector '{selector}': {e}")
                
        return False
