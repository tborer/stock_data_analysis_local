from scraper.fetcher import Fetcher
from scraper.parser import Parser

fetcher = Fetcher()
parser = Parser()
start_url = "https://finance.yahoo.com/topic/stock-market-news/"
print(f"Fetching {start_url}")
html = fetcher.fetch(start_url)
soup = parser.parse(html)
urls = parser.extract_yahoo_news_links(soup, start_url)
print(f"Found {len(urls)} positive-ticker links.")
for idx, url in enumerate(urls[:3]):
    print(f"[{idx+1}] {url}")
    # text = parser.extract_text(parser.parse(fetcher.fetch(url)), "div.caas-body p, p")
    # print(f"    Excerpt: {text[:100]}...")
