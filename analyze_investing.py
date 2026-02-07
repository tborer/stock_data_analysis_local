import sys
import os
import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Add project root to path
sys.path.append(os.getcwd())

from scraper.fetcher import Fetcher
from scraper.parser import Parser

def test_investing_parser():
    # Use the URL configured in sites.yaml
    url = "https://www.investing.com/news/latest-news"
    
    print(f"Initializing Fetcher/Parser...")
    fetcher = Fetcher()
    parser = Parser()
    
    print(f"Fetching {url}...")
    content = fetcher.fetch(url)
    
    if not content:
        print("Failed to fetch content.")
        return

    print(f"Fetched {len(content)} bytes.")
    soup = parser.parse(content)
    
    # 1. Test Next.js Data Extraction
    print("\n--- Testing Next.js Data Extraction ---")
    nextjs_data = parser.extract_nextjs_data(soup)
    if nextjs_data:
        print("SUCCESS: Found and parsed __NEXT_DATA__ JSON.")
        
        # quick check for newsStore
        try:
             news_store = nextjs_data.get('props', {}).get('pageProps', {}).get('state', {}).get('newsStore', {})
             news_items = news_store.get('_news', [])
             print(f"Found {len(news_items)} news items in JSON state.")
        except Exception as e:
             print(f"Error inspecting JSON structure: {e}")

    else:
        print("FAILURE: Could not find or parse __NEXT_DATA__ JSON.")
        
    # 2. Test Link Extraction
    print("\n--- Testing Link Extraction ---")
    links = parser.extract_links(soup, url)
    print(f"Found {len(links)} total unique links.")
    
    # Filter for relevant article links to test scraping
    investing_links = [l for l in links if "/news/" in l and l != url]
    print(f"Found {len(investing_links)} potential article links.")
    
    if investing_links:
        article_url = investing_links[0]
        print(f"\n--- Testing Article Extraction from: {article_url} ---")
        article_content = fetcher.fetch(article_url)
        
        if article_content:
            article_soup = parser.parse(article_content)
            
            # Check JSON data for article
            article_json = parser.extract_nextjs_data(article_soup)
            
            if article_json:
                 print("SUCCESS: Found Next.js data on article page.")
                 
                 # Try to extract text using the new logic
                 # We don't pass a selector to force it to try the JSON/default path
                 text = parser.extract_text(article_soup, selector=None)
                 
                 print(f"Extracted Text Length: {len(text)}")
                 if len(text) > 100:
                     print(f"Sample Text Start: {text[:100]}...")
                 else:
                     print("WARNING: Extracted text is strangely short.")
            else:
                print("FAILURE: No Next.js data on article page.")
        else:
            print("Failed to fetch article page.")
    else:
        print("WARNING: No specific news links found to test article extraction.")

if __name__ == "__main__":
    test_investing_parser()
