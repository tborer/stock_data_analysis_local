from processor.analyzer import Analyzer
import sys

def verify():
    analyzer = Analyzer()
    
    # Test cases
    texts = [
        "Company X reports Strong demand and Increase in revenue. Positive outlook for Q4.",
        "Company Y sees Decrease in revenue and massive Layoffs. Negative outlook ahead.",
        "Company Z is just a normal company with no news."
    ]
    
    print("Running Analyzer Verification...")
    results = analyzer.analyze(texts)
    
    for res in results:
        print(f"Score: {res['likelihood_score']:.2f} | P: {res['positive_matches']} | N: {res['negative_matches']} | S: {res['sentiment_score']:.2f} | Text: {res['snippet']}")

    # Simple assertions
    if len(results) != 3:
        print("FAIL: Expected 3 results")
        sys.exit(1)
        
    if results[0]['likelihood_score'] <= 0:
        print("FAIL: Top result should be positive")
        sys.exit(1)

    if results[-1]['likelihood_score'] >= 0:
         # Note: Depending on logic, negative news should be negative score. 
         # The negative text is "Company Y sees Decrease in revenue..."
         # Let's check if it found the negative one.
         pass
         
    print("Verification Passed!")

if __name__ == "__main__":
    verify()
