import sys
from processor.analyzer import Analyzer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def test_comparison():
    text = """Company X reports Strong demand and Increase in revenue. Positive outlook for Q4.
The company has seen a significant uptick in user engagement over the last month.
We are very happy and excited about the future prospects.
Our new product launch was a massive success, bringing in unprecedented sales numbers.
Investors are highly optimistic and the market reaction has been overwhelmingly positive.
There is strong confidence in the ability of the team to deliver amazing results going forward."""

    # Old way (Document level)
    sia = SentimentIntensityAnalyzer()
    old_score = sia.polarity_scores(text)['compound']
    
    # New way (Analyzer)
    analyzer = Analyzer()
    result = analyzer._calculate_score(text)
    new_score = result['sentiment_score']
    
    print("--- Sentiment Score Comparison ---")
    print(f"Old Score (Document-level VADER): {old_score:.3f}")
    print(f"New Score (Sentence-level Average): {new_score:.3f}")
    
    if old_score > 0.95 and new_score < 0.90:
        print("\nSUCCESS: Score saturation is prevented. Granularity improved.")
        sys.exit(0)
    else:
        print("\nFAIL: Scores did not differentiate as expected.")
        sys.exit(1)

if __name__ == "__main__":
    test_comparison()
