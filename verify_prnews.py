import yaml
from scraper.fetcher import Fetcher
from scraper.parser import Parser

def test_prnews():
    with open('config/sites.yaml', 'r') as f:
        sites_config = yaml.safe_load(f)
        
    pr_config = next((s for s in sites_config['sites'] if s['name'] == 'PRNewswire'), None)
    if not pr_config:
        print("PRNewswire config not found!")
        return

    fetcher = Fetcher()
    parser = Parser()

    print("Fetching list page...")
    list_html = fetcher.fetch(pr_config['url'])
    if not list_html:
        print("Failed to fetch list page")
        return

    soup = parser.parse(list_html)
    all_links = parser.extract_links(soup, pr_config['url'])
    target_urls = [l for l in all_links if "/news-releases/" in l]
    
    if not target_urls:
        print("No target URLs found.")
        return
        
    test_url = target_urls[0]
    print(f"\nFetching article: {test_url}")
    article_html = fetcher.fetch(test_url)
    
    if not article_html:
        print("Failed to fetch article")
        return
        
    article_soup = parser.parse(article_html)
    
    # Extract Title
    title = parser.extract_title(article_soup, pr_config.get('title_selector'))
    print(f"\nExtracted Title: {title}")
    
    # Extract Date
    date_regex = pr_config.get('date_regex')
    date_format = pr_config.get('date_format')
    article_date = parser.extract_date(article_soup, date_regex, date_format, test_url)
    print(f"Extracted Date: {article_date}")
    
    # Extract Content
    selector = pr_config.get('content_selector') or 'p'
    text = parser.extract_text(article_soup, selector)
    print(f"\nExtracted Text ({len(text)} chars):")
    print(text[:300] + "...")

if __name__ == '__main__':
    test_prnews()
