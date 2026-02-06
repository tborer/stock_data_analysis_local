from config.settings import settings
from scraper.fetcher import Fetcher
from scraper.parser import Parser
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

    for site in sites_config.get('sites', []):
        url = site.get('url')
        if state_manager.is_processed(url):
            print(f"Skipping already processed: {url}")
            continue

        print(f"Processing: {url}")
        html = fetcher.fetch(url)
        if html:
            soup = parser.parse(html)
            
            # Simple Strategy: Extract all text based on selector
            # In pending task "Implement Scraper Foundation", we might iterate over articles
            # For now, let's treat the whole page text as one block or split by paragraphs?
            # Creating a list of texts to analyze. 
            # If selector targets a container of articles, we might want to iterate children.
            # But specific logic depends on site structure.
            # Let's try to extract paragraphs contextually.
            
            # For this 'foundation', let's assume content_selector gives us the main text
            # and we split it into meaningful chunks (e.g., paragraphs) for analysis
            # OR we pass the whole text. The Analyzer iterates.
            
            text = parser.extract_text(soup, site.get('content_selector'))
            
            # If text is huge, we might want to split it.
            # Let's split by newline for now to simulate "items"
            texts_to_analyze = [t.strip() for t in text.split('\n') if len(t.strip()) > 50] # simplistic
            
            if texts_to_analyze:
                insights = analyzer.analyze(texts_to_analyze)
                
                # Filter for "high value" (e.g., score != 0 or > threshold)
                # User didn't specify strict threshold, but let's say abs(score) > 10?
                # Or just keep non-zero.
                significant_insights = [i for i in insights if abs(i['likelihood_score']) > 0]
                
                if significant_insights:
                   all_insights.extend(significant_insights)
                   print(f"Found {len(significant_insights)} insights on {url}")

            # Mark as processed only if successfully handled
            state_manager.mark_processed(url)

    if all_insights:
        # Sort all findings by magnitude of score
        all_insights.sort(key=lambda x: abs(x['likelihood_score']), reverse=True)
        top_insights = all_insights[:50] # Limit email size
        
        print(f"Sending email with {len(top_insights)} top insights...")
        body = emailer.format_results(top_insights)
        emailer.send_email(f"Stock Analysis Report - {len(top_insights)} Items", body)
    else:
        print("No significant insights found during this run.")

    print("Job completed.")

if __name__ == "__main__":
    main()
