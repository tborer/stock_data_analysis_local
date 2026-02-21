from config.settings import settings
from scraper.fetcher import Fetcher
from scraper.parser import Parser
from scraper.sitemap_parser import SitemapParser
from storage.state_manager import StateManager
from processor.analyzer import Analyzer
from notifier.emailer import Emailer
from notifier.webhook import WebhookNotifier
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
    webhook = WebhookNotifier()
    
    # Load sites to scrape
    if not os.path.exists(settings.sites_config_path):
        print(f"Config file not found: {settings.sites_config_path}")
        return

    with open(settings.sites_config_path, 'r') as f:
        sites_config = yaml.safe_load(f)

    all_insights = []
    seen_snippets = set()
    seen_titles = set()

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
                
                # Extract Title
                title_selector = site.get('title_selector')
                title = parser.extract_title(soup, title_selector)
                
                # Extract and Filter by Date
                date_regex = site.get('date_regex')
                date_format = site.get('date_format')
                article_date = parser.extract_date(soup, date_regex, date_format, url)
                
                if article_date:
                    import datetime
                    from dateutil import tz
                    
                    # Determine current time
                    now = datetime.datetime.now()
                    
                    # Handle timezone awareness
                    if article_date.tzinfo:
                        # If article date is aware, make now aware (assume local/system time if not specified, 
                        # but ideally compare in UTC)
                        # dateutil parser often returns aware datetimes if TZ abbr is found.
                        # datetime.now() returns naive local time.
                        # conversion:
                        now = datetime.datetime.now(tz=tz.tzlocal())
                        
                    # Calculate difference
                    time_diff = now - article_date
                    
                    # Filter: Skip if older than 1 hour (3600 seconds)
                    # Use total_seconds() to handle timedelta
                    if time_diff.total_seconds() > 3600:
                        print(f"    Skipping old article ({time_diff.total_seconds()/3600:.1f}h old): {article_date}")
                        state_manager.mark_processed(url)
                        continue
                    else:
                        print(f"    Article is fresh ({time_diff.total_seconds()/60:.1f}m ago): {article_date}")
                else:
                    if date_regex:
                        print("    Warning: Date extraction failed despite configuration.")

                # Paywall CSS selector check
                paywall_selector = site.get('paywall_selector')
                if paywall_selector and parser.has_paywall(soup, paywall_selector):
                    print(f"    Skipping: Paywall detected via selector ({paywall_selector})")
                    state_manager.mark_processed(url)
                    continue

                # Title Extraction & De-duplication
                if title:
                    norm_title = " ".join(title.lower().split())
                    if norm_title in seen_titles:
                        print(f"    Skipping duplicate title: {title[:50]}...")
                        state_manager.mark_processed(url)
                        continue
                    seen_titles.add(norm_title)
                    
                print(f"    Title: {title[:50]}..." if title else "    No title found")
                
                # Check text length before scraping
                # Typical paywall stubs are under 500-1000 characters
                min_chars = site.get('min_chars', 0)
                if len(text) < min_chars:
                    print(f"    Skipping: Content length ({len(text)} chars) is below minimum of {min_chars} (Possible paywall stub)")
                    state_manager.mark_processed(url)
                    continue
                
                # Format text using legacy encapsulation
                # Prepend title to the text for analysis context
                full_text = f"{title}\n\n{text}" if title else text
                
                max_chars = site.get('max_chars', 3000)
                formatted_text = parser.format_for_analysis(full_text, url, max_chars=max_chars)
                texts_to_analyze = [formatted_text] if formatted_text else []
                
                if texts_to_analyze:
                    # Pass the title in metadata if needed, but analyzer works on text list
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
            # 1. Send Email (if enabled)
            if settings.enable_insights_email:
                print(f"Sending email with {len(top_insights)} top insights...")

                # Format explicitly for better readability with metadata
                body = emailer.format_results(top_insights)

                # Subject with Date
                date_str = datetime.datetime.now().strftime("%B %d, %Y")
                subject = f"Stock Analysis Report for {date_str} - {len(top_insights)} Items"
                emailer.send_email(subject, body)
            else:
                print("Insights email is disabled. Skipping.")

            # 2. Watchlist API Integration (if enabled)
            if settings.enable_watchlist_api:
                tickers_to_send = set()
                for insight in top_insights:
                    ticker = insight.get('ticker')
                    if ticker:
                        tickers_to_send.add(ticker)
                
                if tickers_to_send:
                    print(f"Sending {len(tickers_to_send)} unique tickers to Watchlist API...")
                    success, msg = webhook.send_tickers(list(tickers_to_send))
                    
                    if not success:
                        print(f"API Error: {msg}")
                        if settings.enable_api_error_email:
                            print("Sending error notification email...")
                            error_subject = f"Watchlist API Error - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                            error_body = (
                                f"An error occurred while sending tickers to the Watchlist API.\n\n"
                                f"Error Details:\n{msg}\n\n"
                                f"Tickers attempted:\n{', '.join(tickers_to_send)}"
                            )
                            emailer.send_email(error_subject, error_body)
                else:
                    print("No tickers found in top insights to send.")
            else:
                print("Watchlist API integration is disabled. Skipping.")
    else:
        print("No significant insights found during this run.")

    print("Job completed.")

if __name__ == "__main__":
    main()
