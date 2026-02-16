import os
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        self.email_sender = os.getenv("EMAIL_SENDER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_recipient = os.getenv("EMAIL_RECIPIENT")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        
        # Watchlist API
        self.watchlist_api_url = os.getenv("WATCHLIST_API_URL", "https://stock-trader-app-ten.vercel.app/api/watchlist/add")
        self.watchlist_api_key = os.getenv("WATCHLIST_API_KEY")
        self.enable_api_error_email = os.getenv("ENABLE_API_ERROR_EMAIL", "true").lower() == "true"
        
        self.sites_config_path = "config/sites.yaml"

    def load_sites_config(self):
        with open(self.sites_config_path, 'r') as f:
            return yaml.safe_load(f)

settings = Settings()
