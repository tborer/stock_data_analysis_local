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
        import re
        
        # 0. Clean Text
        # Strip encapsulation format: ++{URL} content++,
        # Remove leading ++{...} prefix (URL metadata) and trailing ++,
        text = re.sub(r'^\+\+\{[^}]*\}\s*', '', text)
        text = re.sub(r'^\+\+\s*', '', text)  # Fallback for ++ without URL
        text = re.sub(r'\+\+,?\s*$', '', text)
        
        # 1. Metadata Extraction
        ticker = None
        exchange = None
        company = None
        
        # Define patterns for ticker extraction
        # Heuristic: Priority to explicit exchanges, then generic parens
        exchange_patterns = [
            (r'(?:NYSE|New York Stock Exchange)\s*:\s*([A-Z]+)', 'NYSE'),
            (r'(?:NASDAQ|Nasdaq)\s*:\s*([A-Z]+)', 'NASDAQ'),
            (r'(?:TSX|Toronto Stock Exchange)\s*:\s*([A-Z]+)', 'TSX'),
            (r'(?:LSE|London Stock Exchange|LN)\s*:\s*([A-Z]+)', 'LN'),
            (r'(?:SIX)\s*:\s*([A-Z]+)', 'SIX'), # Added from user example "SIX: RO"
            (r'\(([A-Z]{3,5})\)', 'NA') # Generic Fallback
        ]
        
        for pattern_str, ex_name in exchange_patterns:
            pattern = re.compile(pattern_str)
            match = pattern.search(text)
            if match:
                ticker = match.group(1).strip()
                exchange = ex_name
                
                # Attempt to extract Company Name
                # Look at the text immediately preceding the match start
                # We want consecutive capitalized words.
                match_start = match.start()
                preceding_text = text[:match_start].strip()
                
                # Split by non-word chars (keeping spaces) to analyze words
                # Working backwards:
                words = preceding_text.split()
                company_words = []
                for w in reversed(words):
                    # Clean punctuation first
                    clean_w = w.strip("(),.")
                    
                    if not clean_w:
                        continue

                    # Check if word starts with uppercase (and isn't just a tiny stop word if we want to be strict, but mainly check Case)
                    if clean_w[0].isupper():
                        # If we have existing words and this is a Capitalized word, add it
                        company_words.insert(0, clean_w)
                    elif clean_w.lower() in ['inc', 'ltd', 'corp', 'group', 'holdings'] and not company_words:
                         # Allow these suffix words even if lowercase in some sloppy text, but usually they are Cap.
                         pass 
                    else:
                        # Stop if we hit a lowercase word (likely "announced", "that", "the")
                        # Exception: "of" in "Bank of America"
                        if clean_w.lower() == 'of' and company_words:
                            company_words.insert(0, w) # keep original w for "of"
                            continue
                        break
                
                if company_words:
                    company = " ".join(company_words)
                
                break

        # 1. VaderSentiment analysis (General Tone) - Sentence Level Averaging
        # Split by common sentence terminators (. ! ?)
        sentences = re.split(r'(?<=[.!?]) +', text.replace('\n', ' '))
        
        sent_scores = []
        for s in sentences:
            if s.strip():
                # Get compound score for each sentence
                score = self.sia.polarity_scores(s)['compound']
                sent_scores.append(score)
        
        if sent_scores:
            vader_score = sum(sent_scores) / len(sent_scores)
        else:
            # Fallback if no valid sentences found
            sentiment_scores = self.sia.polarity_scores(text)
            vader_score = sentiment_scores['compound']

        logging.info(f"VADER Average Score: {vader_score:.3f} (over {len(sent_scores)} sentences)")
        
        # 2. Keyword Matching with enhancements
        text_lower = text.lower()
        headline_limit = 150 # First 150 chars treated as headline
        headline_text = text_lower[:headline_limit]
        body_text = text_lower[headline_limit:]
        
        # Single-word negation terms
        negation_words = {"not", "no", "never", "unlikely", "refuse", "deny", "denied",
                          "reject", "rejected", "without", "lack", "lacking", "fails",
                          "failed", "unable", "hardly", "barely", "neither", "nor"}
        # Multi-word negation phrases (checked via substring match on preceding context)
        negation_phrases = [
            "failed to", "unable to", "lack of", "fell short of", "falls short of",
            "did not", "does not", "do not", "has not", "have not", "had not",
            "will not", "would not", "could not", "cannot", "can not",
            "no longer", "not yet", "far from", "anything but",
        ]
        
        # Pre-compile word-boundary patterns for each keyword
        def _build_keyword_pattern(keyword_lower):
            """Build a regex pattern with word boundaries for a keyword."""
            escaped = re.escape(keyword_lower)
            return re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)

        keyword_patterns = {}
        for kw in self.positive_keywords + self.negative_keywords:
            keyword_patterns[kw] = _build_keyword_pattern(kw.lower())

        def calculate_keyword_impact(keywords, weights, is_positive):
            total_impact = 0.0
            found_matches = []

            for keyword in keywords:
                pattern = keyword_patterns[keyword]

                for match in pattern.finditer(text_lower):
                    idx = match.start()

                    # Context Check: Look at up to 5 words / ~50 chars before keyword
                    context_start = max(0, idx - 50)
                    preceding_text = text_lower[context_start:idx]
                    preceding_words = set(preceding_text.split()[-5:])

                    # Check single-word negation terms
                    is_negated = bool(preceding_words & negation_words)
                    # Check multi-word negation phrases in the preceding context
                    if not is_negated:
                        for phrase in negation_phrases:
                            if phrase in preceding_text:
                                is_negated = True
                                break

                    weight = weights.get(keyword, 0)

                    # Headline Multiplier
                    if idx < headline_limit:
                        weight *= 2.0

                    # Negation Logic
                    if is_negated:
                        # Flip impact: Positive -> Negative, Negative -> Positive
                        # Reduce weight slightly as negated sentiment is often softer
                        weight *= -0.8

                    total_impact += weight
                    found_matches.append(f"{keyword}{'(H)' if idx < headline_limit else ''}{'(NEG)' if is_negated else ''}")

            return total_impact, found_matches

        pos_impact, pos_matches = calculate_keyword_impact(self.positive_keywords, self.positive_weights, True)
        neg_impact, neg_matches = calculate_keyword_impact(self.negative_keywords, self.negative_weights, False)
        
        logging.info(f"Positive Matches: {pos_matches}, Impact: {pos_impact}")
        logging.info(f"Negative Matches: {neg_matches}, Impact: {neg_impact}")
        
        # Net Keyword Score
        raw_keyword_score = pos_impact - neg_impact
        
        # Normalize Keyword Score using tanh to squeeze into -1.0 to 1.0
        # Scaling factor of 5.0 allows better differentiation across a wider range
        # of signal strengths (tanh saturates ~0.96 at raw_score=9, ~0.76 at raw_score=5)
        keyword_norm = math.tanh(raw_keyword_score / 5.0)
        
        # 3. Final Combined Score
        # Formula: 30% VADER, 70% Keywords
        combined_score = (0.3 * vader_score) + (0.7 * keyword_norm)
        
        # Map -1.0..1.0 to 0..100
        # -1 -> 0 (Bearish), 0 -> 50 (Neutral), 1 -> 100 (Bullish)
        final_score = (combined_score + 1) * 50
        
        logging.info(f"Raw Keyword: {raw_keyword_score}, Norm Keyword: {keyword_norm}, Combined: {combined_score}, Final: {final_score}")

        # Prepare info string
        info_str = ""
        if ticker:
            info_str = f" [{exchange}: {ticker}]"
            if company:
                info_str = f" [{company} ({exchange}: {ticker})]"
        
        snippet = text[:200] + "..." if len(text) > 200 else text
        if info_str:
            snippet += info_str

        return {
            'likelihood_score': round(final_score, 2),
            'sentiment_score': round(vader_score, 2),
            'positive_matches': len(pos_matches),
            'negative_matches': len(neg_matches),
            'match_details': f"Pos: {pos_matches}, Neg: {neg_matches}",
            'company_text': text,
            'full_text': f"Score: {final_score:.1f} - {text}{info_str}",
            'snippet': snippet,
            'ticker': ticker,
            'exchange': exchange,
            'company': company
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
