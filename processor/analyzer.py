import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import concurrent.futures
import os

class Analyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.positive_keywords = [
            "Growth", "Increase in revenue", "Expansion into new markets", "Strong demand",
            "Positive outlook", "Increased guidance", "Beats expectations", "Exceeds forecasts",
            "Strong leadership", "Innovation", "Progress", "Achievement", "Outperform",
            "Upswing", "Recovery", "Strength", "Momentum", "Optimistic", "Confidence",
            "Success", "Record high", "All-time high", "Surge in sales", "Jump in profits",
            "Increase in earnings", "Strong financials", "Robust growth", "Favorable trends",
            "Bullish sentiment", "New Product", "Product Launch", "Higher than expected",
            "Revenue growth acceleration", "Expanding customer base", "Increasing market share",
            "Backlog of orders", "Growing demand", "Positive earnings surprise",
            "Upward revision in guidance", "Beating analyst estimates",
            "Exceeding industry expectations", "Leadership team expansion",
            "Strategic partnerships", "Innovative products", "Patent approval",
            "Regulatory approval", "Product upgrades", "Service expansions",
            "Geographic expansion", "Entry into new industries",
            "Diversification of revenue streams", "Cost savings initiatives",
            "Operational efficiency improvements", "Margin expansion",
            "Return on investment (ROI) growth", "Cash flow growth", "Debt reduction",
            "Share buybacks", "Dividend increases", "Analyst upgrades",
            "Price target increases", "Institutional investment", "Insider buying",
            "Short squeeze", "Trend reversal", "Relative strength index (RSI) improvement",
            "Moving average convergence divergence (MACD) crossover", "Bullish chart patterns",
            "Sector outperformance", "Industry recognition", "Awards and accolades",
            "Thought leadership", "Partnership announcements", "Joint ventures",
            "Licensing agreements", "Distribution deals"
        ]

        self.negative_keywords = [
            "Decline", "Loss", "Weakness", "Decrease in revenue", "Downsize", "Layoffs",
            "Negative outlook", "Decreased guidance", "Misses expectations",
            "Disappoints forecasts", "Poor leadership", "Setback", "Pullback", "Correction",
            "Downgrade", "Selloff", "Plummet", "Collapse", "Bankruptcy", "Record low",
            "All-time low", "Slump in sales", "Dip in profits", "Decrease in earnings",
            "Weak financials", "Slow growth", "Unfavorable trends", "Bearish sentiment",
            "Market downturn", "Revenue decline acceleration", "Contracting customer base",
            "Loss of market share", "Weak order book", "Cancellation of orders",
            "Decreasing demand", "Negative earnings surprise", "Downward revision in guidance",
            "Missing analyst estimates", "Falling short of industry expectations",
            "Leadership team departures", "Strategic partnership terminations",
            "Product recalls", "Regulatory issues", "Litigation risks", "Compliance concerns",
            "Operational inefficiencies", "Margin compression",
            "Return on investment (ROI) decline", "Cash flow decrease", "Debt increase",
            "Share dilution", "Dividend cuts", "Analyst downgrades",
            "Price target decreases", "Institutional selling", "Insider selling",
            "Short interest increase", "Trend reversal to the downside",
            "Relative strength index (RSI) deterioration",
            "Moving average convergence divergence (MACD) crossover to the downside",
            "Bearish chart patterns", "Sector underperformance", "Industry decline",
            "Reputation damage", "Public relations crisis", "Executive scandals",
            "Workforce reductions", "Facility closures", "Discontinued operations",
            "Impairment charges", "Restructuring costs", "Asset write-downs"
        ]

        self.positive_weights = {
            "Growth": 0.8, "Increase in revenue": 0.9, "Expansion into new markets": 0.9,
            "Strong demand": 0.7, "Positive outlook": 0.6, "Increased guidance": 0.8,
            "Beats expectations": 0.9, "Exceeds forecasts": 0.9, "Strong leadership": 0.7,
            "Innovation": 0.8, "Progress": 0.6, "Achievement": 0.7, "Outperform": 0.8,
            "Upswing": 0.7, "Recovery": 0.6, "Strength": 0.7, "Momentum": 0.8,
            "Optimistic": 0.6, "Confidence": 0.7, "Success": 0.8, "Record high": 0.9,
            "All-time high": 0.9, "Surge in sales": 0.9, "Jump in profits": 0.9,
            "Increase in earnings": 0.8, "Strong financials": 0.8, "Robust growth": 0.9,
            "Favorable trends": 0.7, "Bullish sentiment": 0.8, "New Product": 0.7,
            "Product Launch": 0.8, "Higher than expected": 0.7,
            "Revenue growth acceleration": 0.9, "Expanding customer base": 0.8,
            "Increasing market share": 0.8, "Backlog of orders": 0.7, "Growing demand": 0.7,
            "Positive earnings surprise": 0.9, "Upward revision in guidance": 0.8,
            "Beating analyst estimates": 0.9, "Exceeding industry expectations": 0.9,
            "Leadership team expansion": 0.7, "Strategic partnerships": 0.8,
            "Innovative products": 0.8, "Patent approval": 0.7, "Regulatory approval": 0.7,
            "Product upgrades": 0.6, "Service expansions": 0.7, "Geographic expansion": 0.8,
            "Entry into new industries": 0.8, "Diversification of revenue streams": 0.8,
            "Cost savings initiatives": 0.6, "Operational efficiency improvements": 0.6,
            "Margin expansion": 0.7, "Return on investment (ROI) growth": 0.8,
            "Cash flow growth": 0.8, "Debt reduction": 0.7, "Share buybacks": 0.6,
            "Dividend increases": 0.7, "Analyst upgrades": 0.8,
            "Price target increases": 0.8, "Institutional investment": 0.8,
            "Insider buying": 0.7, "Short squeeze": 0.6, "Trend reversal": 0.7,
            "Relative strength index (RSI) improvement": 0.7,
            "Moving average convergence divergence (MACD) crossover": 0.7,
            "Bullish chart patterns": 0.7, "Sector outperformance": 0.8,
            "Industry recognition": 0.7, "Awards and accolades": 0.6,
            "Thought leadership": 0.7, "Partnership announcements": 0.7,
            "Joint ventures": 0.7, "Licensing agreements": 0.6, "Distribution deals": 0.6
        }

        self.negative_weights = {
            "Decline": 0.8, "Loss": 0.9, "Weakness": 0.8, "Decrease in revenue": 0.8,
            "Downsize": 0.7, "Layoffs": 0.8, "Negative outlook": 0.7, "Decreased guidance": 0.8,
            "Misses expectations": 0.9, "Disappoints forecasts": 0.9, "Poor leadership": 0.7,
            "Setback": 0.6, "Pullback": 0.6, "Correction": 0.6, "Downgrade": 0.7,
            "Selloff": 0.8, "Plummet": 0.9, "Collapse": 0.9, "Bankruptcy": 0.9,
            "Record low": 0.9, "All-time low": 0.9, "Slump in sales": 0.9,
            "Dip in profits": 0.8, "Decrease in earnings": 0.8, "Weak financials": 0.8,
            "Slow growth": 0.6, "Unfavorable trends": 0.7, "Bearish sentiment": 0.8,
            "Market downturn": 0.8, "Revenue decline acceleration": 0.9,
            "Contracting customer base": 0.8, "Loss of market share": 0.8,
            "Weak order book": 0.7, "Cancellation of orders": 0.8, "Decreasing demand": 0.7,
            "Negative earnings surprise": 0.9, "Downward revision in guidance": 0.8,
            "Missing analyst estimates": 0.9, "Falling short of industry expectations": 0.9,
            "Leadership team departures": 0.7, "Strategic partnership terminations": 0.8,
            "Product recalls": 0.8, "Regulatory issues": 0.8, "Litigation risks": 0.8,
            "Compliance concerns": 0.7, "Operational inefficiencies": 0.6,
            "Margin compression": 0.7, "Return on investment (ROI) decline": 0.8,
            "Cash flow decrease": 0.8, "Debt increase": 0.7, "Share dilution": 0.6,
            "Dividend cuts": 0.7, "Analyst downgrades": 0.8, "Price target decreases": 0.8,
            "Institutional selling": 0.8, "Insider selling": 0.7,
            "Short interest increase": 0.6, "Trend reversal to the downside": 0.8,
            "Relative strength index (RSI) deterioration": 0.7,
            "Moving average convergence divergence (MACD) crossover to the downside": 0.7,
            "Bearish chart patterns": 0.7, "Sector underperformance": 0.8,
            "Industry decline": 0.7, "Reputation damage": 0.8,
            "Public relations crisis": 0.8, "Executive scandals": 0.8,
            "Workforce reductions": 0.7, "Facility closures": 0.7,
            "Discontinued operations": 0.7, "Impairment charges": 0.7,
            "Restructuring costs": 0.6, "Asset write-downs": 0.7
        }

    def _calculate_score(self, text):
        # VaderSentiment analysis
        sentiment_scores = self.sia.polarity_scores(text)
        sentiment_score = sentiment_scores['compound']
        
        # Weighted keyword matching
        positive_matches = sum(text.count(keyword) * self.positive_weights.get(keyword, 0) for keyword in self.positive_keywords)
        
        negative_matches = sum(text.count(keyword) * self.negative_weights.get(keyword, 0) for keyword in self.negative_keywords)
        
        # Combine sentiment score and keyword matching
        denominator = positive_matches + negative_matches + 1
        
        # Formula: (sentiment_score + (positive_matches - negative_matches) / denominator) / 2 * 100
        likelihood_score = (sentiment_score + (positive_matches - negative_matches) / denominator) / 2 * 100
        
        return {
            'likelihood_score': likelihood_score,
            'positive_matches': positive_matches,
            'negative_matches': negative_matches,
            'sentiment_score': sentiment_score,
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
