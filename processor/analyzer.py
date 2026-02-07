import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import concurrent.futures
import os

class Analyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        
        # Load keywords from config
        self.keywords_config_path = "config/keywords.yaml"
        self.positive_keywords = []
        self.negative_keywords = []
        self.positive_weights = {}
        self.negative_weights = {}
        
        self.load_keywords()

    def load_keywords(self):
        if not os.path.exists(self.keywords_config_path):
            logging.error(f"Keywords config file not found: {self.keywords_config_path}")
            return
            
        try:
            import yaml
            with open(self.keywords_config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            positive_data = config.get('positive_keywords', [])
            self.positive_keywords = [item['name'] for item in positive_data]
            self.positive_weights = {item['name']: item['weight'] for item in positive_data}
            
            negative_data = config.get('negative_keywords', [])
            self.negative_keywords = [item['name'] for item in negative_data]
            self.negative_weights = {item['name']: item['weight'] for item in negative_data}
            
            logging.info(f"Loaded {len(self.positive_keywords)} positive and {len(self.negative_keywords)} negative keywords.")
            
        except Exception as e:
            logging.error(f"Error loading keywords config: {e}")

    def _calculate_score(self, text):
        # VaderSentiment analysis
        sentiment_scores = self.sia.polarity_scores(text)
        sentiment_score = sentiment_scores['compound']
        logging.info(f"Sentiment score: {sentiment_score}")
        
        # Weighted keyword matching
        positive_matches = sum(text.count(keyword) * self.positive_weights.get(keyword, 0) for keyword in self.positive_keywords)
        logging.info(f"Positive matches: {positive_matches}")
        
        negative_matches = sum(text.count(keyword) * self.negative_weights.get(keyword, 0) for keyword in self.negative_keywords)
        logging.info(f"Negative matches: {negative_matches}")
        
        # Combine sentiment score and keyword matching
        denominator = positive_matches + negative_matches + 1
        logging.info(f"Denominator: {denominator}")
        
        likelihood_score = 0
        if denominator != 0:
            # Formula: (sentiment_score + (positive_matches - negative_matches) / denominator) / 2 * 100
            likelihood_score = (sentiment_score + (positive_matches - negative_matches) / denominator) / 2 * 100
        else:
            logging.warning("Denominator is zero!")
            
        logging.info(f"Likelihood score: {likelihood_score}")
        
        if likelihood_score == 0:
            logging.info("Likelihood score is zero!")
        
        return {
            'likelihood_score': likelihood_score,
            'positive_matches': positive_matches,
            'negative_matches': negative_matches,
            'sentiment_score': sentiment_score,
            'company_text': text,
            'full_text': f"Score: {likelihood_score} - {text}",
            'snippet': text[:200] + "..." if len(text) > 200 else text
        }

    def analyze(self, texts):
        """
        Analyze a list of texts (articles/paragraphs).
        Returns a sorted list of insights.
        """
        results = []
        
        # Use ThreadPool logic
        # Note: ThreadPoolExecutor works fine with instance methods in Python 3
        num_workers = os.cpu_count() or 4
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Create a dictionary to map futures to texts if needed, or just iterate results
            future_to_text = {executor.submit(self._calculate_score, text): text for text in texts}
            
            for future in concurrent.futures.as_completed(future_to_text):
                text = future_to_text[future]
                try:
                    score_data = future.result()
                    results.append(score_data)
                except Exception as e:
                    logging.error(f"Error analyzing text: {e}")
        
        # Sort by likelihood score descending
        results.sort(key=lambda x: x['likelihood_score'], reverse=True)
        return results
