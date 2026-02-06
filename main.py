from config.settings import settings
from scraper.fetcher import Fetcher
from scraper.parser import Parser
from scraper.sitemap_parser import SitemapParser
from storage.state_manager import StateManager
from processor.analyzer import Analyzer
from notifier.emailer import Emailer
import yaml
import os

def main():
    print("Starting Stock Data Analysis Job...")
    
    # Initialize components
    fetcher = Fetcher()
    parser = Parser()
    sitemap_parser = SitemapParser(fetcher)
    state_manager = StateManager()
    analyzer = Analyzer()
    emailer = Emailer()
    
    # Load sites to scrape
    if not os.path.exists(settings.sites_config_path):
        print(f"Config file not found: {settings.sites_config_path}")
        return

    with open(settings.sites_config_path, 'r') as f:
        sites_config = yaml.safe_load(f)

    all_insights = []

    import datetime

    for site in sites_config.get('sites', []):
        site_name = site.get('name')
        site_type = site.get('type', 'page')
        raw_url = site.get('url')
        max_urls = site.get('max_urls', 50)
        
        # Handle dynamic date formatting
        # Support %Y, %m, %d placeholders
        now = datetime.datetime.utcnow()
        start_url = now.strftime(raw_url)
        
        target_urls = []
        
        if site_type == 'sitemap':
            print(f"Fetching URLs from sitemap: {start_url}")
            target_urls = sitemap_parser.get_article_urls(start_url, max_urls=max_urls)
        else:
            target_urls = [start_url]
            
        print(f"Found {len(target_urls)} URLs to process for {site_name}")

        for url in target_urls:
            if state_manager.is_processed(url):
                # print(f"Skipping: {url}") # Verbose
                continue

            print(f"Processing: {url}")
            html = fetcher.fetch(url)
            if html:
                soup = parser.parse(html)
                
                # Default fallback selector if not specified
                selector = site.get('content_selector') or 'p' 
                text = parser.extract_text(soup, selector)
                
                # Split large text or just pass whole
                texts_to_analyze = [t.strip() for t in text.split('\n') if len(t.strip()) > 50]
                
                if texts_to_analyze:
                    insights = analyzer.analyze(texts_to_analyze)
                    significant_insights = [i for i in insights if abs(i['likelihood_score']) > 0]
                    
                    if significant_insights:
                       print(f"  -> Found {len(significant_insights)} insights")
                       # Attach metadata
                       for i in significant_insights:
                           i['source_url'] = url
                           i['site_name'] = site_name
                           
                       all_insights.extend(significant_insights)

                # Mark as processed
                state_manager.mark_processed(url)

    if all_insights:
        # Sort all findings by magnitude of score
        all_insights.sort(key=lambda x: abs(x['likelihood_score']), reverse=True)
        top_insights = all_insights[:50] # Limit email size
        
        print(f"Sending email with {len(top_insights)} top insights...")
        
        # Format explicitly for better readability with metadata
        body = emailer.format_results(top_insights) 
        emailer.send_email(f"Stock Analysis Report - {len(top_insights)} Items", body)
    else:
        print("No significant insights found during this run.")

    print("Job completed.")

if __name__ == "__main__":
    main()
