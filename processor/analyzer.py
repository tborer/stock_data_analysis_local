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
        import math
        
        # 1. VaderSentiment analysis (General Tone)
        sentiment_scores = self.sia.polarity_scores(text)
        vader_score = sentiment_scores['compound']  # -1.0 to 1.0
        logging.info(f"VADER Score: {vader_score}")
        
        # 2. Keyword Matching with enhancements
        text_lower = text.lower()
        headline_limit = 150 # First 150 chars treated as headline
        headline_text = text_lower[:headline_limit]
        body_text = text_lower[headline_limit:]
        
        negation_words = {"not", "no", "never", "unlikely", "refuse", "deny", "denied", "reject", "rejected"}
        
        def calculate_keyword_impact(keywords, weights, is_positive):
            total_impact = 0.0
            found_matches = []
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Simple check first for performance
                if keyword_lower not in text_lower:
                    continue
                    
                # Find all occurrences to check context
                start = 0
                while True:
                    idx = text_lower.find(keyword_lower, start)
                    if idx == -1:
                        break
                        
                    # Context Check: Look at 3-5 words before the keyword for negation
                    # Extract preceding text snippet (up to 30 chars approx)
                    context_start = max(0, idx - 30)
                    preceding_text = text_lower[context_start:idx]
                    preceding_words = set(preceding_text.split()[-3:]) # Last 3 words
                    
                    is_negated = bool(preceding_words & negation_words)
                    
                    weight = weights.get(keyword, 0)
                    
                    # Headline Multiplier
                    if idx < headline_limit:
                        weight *= 2.0
                        
                    # Negation Logic
                    if is_negated:
                        # Flip impact: Postive -> Negative, Negative -> Positive
                        # Reduce weight slightly as negated sentiment is often softer
                        weight *= -0.8 
                    
                    total_impact += weight
                    found_matches.append(f"{keyword}{'(H)' if idx < headline_limit else ''}{'(NEG)' if is_negated else ''}")
                    
                    start = idx + len(keyword_lower)
            
            return total_impact, found_matches

        pos_impact, pos_matches = calculate_keyword_impact(self.positive_keywords, self.positive_weights, True)
        neg_impact, neg_matches = calculate_keyword_impact(self.negative_keywords, self.negative_weights, False)
        
        logging.info(f"Positive Matches: {pos_matches}, Impact: {pos_impact}")
        logging.info(f"Negative Matches: {neg_matches}, Impact: {neg_impact}")
        
        # Net Keyword Score
        raw_keyword_score = pos_impact - neg_impact
        
        # Normalize Keyword Score using tanh to squeeze into -1.0 to 1.0
        # Scaling factor: assuming ~5.0 is a "strong" score (e.g., 5 keywords w/ weight 1.0)
        keyword_norm = math.tanh(raw_keyword_score / 3.0) 
        
        # 3. Final Combined Score
        # Formula: 30% VADER, 70% Keywords
        combined_score = (0.3 * vader_score) + (0.7 * keyword_norm)
        
        # Map -1.0..1.0 to 0..100
        # -1 -> 0 (Bearish), 0 -> 50 (Neutral), 1 -> 100 (Bullish)
        final_score = (combined_score + 1) * 50
        
        logging.info(f"Raw Keyword: {raw_keyword_score}, Norm Keyword: {keyword_norm}, Combined: {combined_score}, Final: {final_score}")

        return {
            'likelihood_score': round(final_score, 2),
            'sentiment_score': round(vader_score, 2),
            'positive_matches': len(pos_matches),
            'negative_matches': len(neg_matches),
            'match_details': f"Pos: {pos_matches}, Neg: {neg_matches}",
            'company_text': text,
            'full_text': f"Score: {final_score:.1f} - {text}",
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
