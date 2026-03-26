import os
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        self.email_sender = os.getenv("EMAIL_SENDER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
        recipient_str = os.getenv("EMAIL_RECIPIENT", "")
        self.email_recipients = [r.strip() for r in recipient_str.split(',')] if recipient_str else []
        
        bcc_str = os.getenv("EMAIL_BCC", "")
        self.email_bcc = [b.strip() for b in bcc_str.split(',')] if bcc_str else []
        
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        
        # Feature Flags
        self.enable_insights_email = os.getenv("ENABLE_INSIGHTS_EMAIL", "true").lower() == "true"
        self.enable_watchlist_api = os.getenv("ENABLE_WATCHLIST_API", "false").lower() == "true"

        # Watchlist API
        self.watchlist_api_url = os.getenv("WATCHLIST_API_URL", "https://stock-trader-app-ten.vercel.app/api/watchlist/add")
        self.watchlist_api_key = os.getenv("WATCHLIST_API_KEY")
        self.enable_api_error_email = os.getenv("ENABLE_API_ERROR_EMAIL", "true").lower() == "true"
        
        self.sites_config_path = "config/sites.yaml"

    def load_sites_config(self):
        with open(self.sites_config_path, 'r') as f:
            return yaml.safe_load(f)

settings = Settings()
