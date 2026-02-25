from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

sia = SentimentIntensityAnalyzer()

text = """Company X reports Strong demand and Increase in revenue. Positive outlook for Q4.
The company has seen a significant uptick in user engagement over the last month.
We are very happy and excited about the future prospects.
Our new product launch was a massive success, bringing in unprecedented sales numbers.
Investors are highly optimistic and the market reaction has been overwhelmingly positive."""

doc_score = sia.polarity_scores(text)['compound']

# Sentence level
sentences = re.split(r'(?<=[.!?]) +', text.replace('\n', ' '))
sent_scores = [sia.polarity_scores(s)['compound'] for s in sentences if s.strip()]
avg_score = sum(sent_scores) / len(sent_scores) if sent_scores else 0.0

print(f"Document Score: {doc_score}")
print(f"Sentence Average Score: {avg_score}")
print(f"Details: {sent_scores}")

