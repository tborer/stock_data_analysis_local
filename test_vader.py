import sys
print("Starting up...")
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    print("Imported vaderSentiment")
    sia = SentimentIntensityAnalyzer()
    print("Initialized SIA")
    scores = sia.polarity_scores("hello world")
    print(f"Scores: {scores}")
except Exception as e:
    print(f"Error: {e}")
print("Done.")
