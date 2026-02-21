import sys
import os
import logging

logging.basicConfig(level=logging.INFO)

# Ensure the processor module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from processor.analyzer import Analyzer

text = """On Friday, Lamar Advertising (NASDAQ: LAMR) reported mixed fourth-quarter results, with earnings slightly missing Wall Street expectations even as revenue topped forecasts and management pointed to improving sales trends. The company’s stock edged down -0.41% in pre-market trading after the announcement. For the quarter, Lamar posted earnings per share of $1.50, $0.07 below the consensus estimate of $1.57. Revenue rose 2.8% year over year to $595.9 million, ahead of the $591.9 million analysts had expected. Net income totaled $154.7 million, compared with a net loss in the prior-year period, while adjusted EBITDA increased 3.7% to $288.9 million. For the full year 2025, revenue grew 2.7% to $2.27 billion, with net income climbing to $593.1 million. Adjusted EBITDA reached $1.06 billion for the year. Diluted AFFO per share rose 3.4% to $8.26. “We ended 2025 with encouraging sales momentum, with growth in both local and national in the fourth quarter, even with a tough political comp,” CEO Sean Reilly said. “That strength continued into 2026, and pacings for the balance of the year remain promising.” Looking ahead, Lamar expects fiscal 2026 EPS between $5.72 and $5.83, below the current consensus of $5.91. However, the company guided for diluted AFFO per share of $8.50 to $8.70 for 2026, signaling confidence in cash flow generation. With more than 360,000 displays across North America, including over 5,500 digital billboards, Lamar continues to invest in digital deployment while emphasizing steady organic growth and disciplined capital allocation. Investors will be watching whether the company’s improving sales momentum can offset the slightly softer earnings outlook for 2026."""

analyzer = Analyzer()
result = analyzer._calculate_score(text)

print("\n--- Sentiment Results ---")
print(f"Likelihood Score: {result['likelihood_score']}")
print(f"Sentiment Score (Vader): {result['sentiment_score']}")
print(f"Match Details: {result['match_details']}")
print("-------------------------\n")
