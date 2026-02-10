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
    seen_snippets = set()

    import datetime

    for site in sites_config.get('sites', []):
        site_name = site.get('name')
        site_type = site.get('type', 'page')
        raw_url = site.get('url')
        max_urls = site.get('max_urls', 50)
        
        # Handle dynamic date formatting
        # Support %Y, %m, %d placeholders
        now = datetime.datetime.now()
        start_url = now.strftime(raw_url)
        
        target_urls = []
        
        if site_type == 'sitemap':
            print(f"Fetching URLs from sitemap: {start_url}")
            include_filters = site.get('include_filters', [])
            target_urls = sitemap_parser.get_article_urls(start_url, max_urls=max_urls, include_filters=include_filters)
        elif site_type == 'page':
            print(f"Fetching URLs from page: {start_url}")
            html = fetcher.fetch(start_url)
            if html:
                soup = parser.parse(html)
                all_links = parser.extract_links(soup, start_url)
                
                include_filters = site.get('include_filters', [])
                target_urls = []
                for link in all_links:
                    if len(target_urls) >= max_urls:
                        break
                    
                    # Apply filters
                    if include_filters:
                        if any(f in link for f in include_filters):
                            target_urls.append(link)
                    else:
                        target_urls.append(link)
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
                
                # Format text using legacy encapsulation
                max_chars = site.get('max_chars', 3000)
                formatted_text = parser.format_for_analysis(text, url, max_chars=max_chars)
                texts_to_analyze = [formatted_text] if formatted_text else []
                
                if texts_to_analyze:
                    insights = analyzer.analyze(texts_to_analyze)
                    significant_insights = [i for i in insights if abs(i['likelihood_score']) > 0]
                    
                    if significant_insights:
                        print(f"  -> Found {len(significant_insights)} insights")
                        # Attach metadata and de-duplicate
                        for i in significant_insights:
                            i['source_url'] = url
                            i['site_name'] = site_name
                            
                            # De-duplication: Check if snippet is already seen
                            # Using a simple hash of the snippet text to identify duplicates
                            snippet_hash = hash(i.get('snippet', ''))
                            if snippet_hash not in seen_snippets:
                                seen_snippets.add(snippet_hash)
                                all_insights.append(i)
                            else:
                                # print(f"    Duplicate insight skipped.") # Verbose
                                pass

                # Mark as processed
                state_manager.mark_processed(url)

    if all_insights:
        # Get threshold from config (default 75)
        min_score = sites_config.get('email_min_score', 75)
            
        print(f"Filtering insights with minimum score: {min_score}")
        
        # Filter insights
        filtered_insights = [i for i in all_insights if abs(i['likelihood_score']) >= min_score]
        
        # Sort all findings by magnitude of score
        filtered_insights.sort(key=lambda x: abs(x['likelihood_score']), reverse=True)
        top_insights = filtered_insights[:50] # Limit email size
        
        if not top_insights:
            print(f"No insights met the minimum score threshold of {min_score}")
        else:
            print(f"Sending email with {len(top_insights)} top insights...")
            
            # Format explicitly for better readability with metadata
            body = emailer.format_results(top_insights) 
            
            # Subject with Date
            date_str = datetime.datetime.now().strftime("%B %d, %Y")
            subject = f"Stock Analysis Report for {date_str} - {len(top_insights)} Items"
            emailer.send_email(subject, body)
    else:
        print("No significant insights found during this run.")

    print("Job completed.")

if __name__ == "__main__":
    main()
