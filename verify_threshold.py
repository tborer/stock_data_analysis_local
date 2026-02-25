from config.settings import settings
import yaml

def verify():
    # Mock config
    sites_config = {
        'email_min_score': 75,
        'email_min_sentiment': 0.5
    }
    
    # Mock insights
    all_insights = [
        {'likelihood_score': 80, 'sentiment_score': 0.6, 'snippet': 'High score, High sentiment (KEEP)'},
        {'likelihood_score': -90, 'sentiment_score': -0.7, 'snippet': 'High negative score, High negative sentiment (KEEP)'},
        {'likelihood_score': 80, 'sentiment_score': 0.2, 'snippet': 'High score, Low sentiment (DROP)'},
        {'likelihood_score': 50, 'sentiment_score': 0.8, 'snippet': 'Low score, High sentiment (DROP)'},
        {'likelihood_score': 75, 'sentiment_score': 0.5, 'snippet': 'Boundary score, Boundary sentiment (KEEP)'}
    ]
    
    # Logic from main.py
    min_score = sites_config.get('email_min_score', 75)
    min_sentiment = sites_config.get('email_min_sentiment', 0.5)
    
    print(f"Thresholds: score={min_score}, sentiment={min_sentiment}")
    
    filtered_insights = [
        i for i in all_insights 
        if abs(i['likelihood_score']) >= min_score and abs(i.get('sentiment_score', 0)) >= min_sentiment
    ]
    
    print(f"Total insights: {len(all_insights)}")
    print(f"Filtered insights: {len(filtered_insights)}")
    
    for i in filtered_insights:
        print(f"  Kept: Score={i['likelihood_score']}, Sentiment={i.get('sentiment_score', 0)}")
    
    # Assertions
    # Should keep exactly 3 items
    assert len(filtered_insights) == 3
    
    # Check that the items we kept have the right properties
    for i in filtered_insights:
        assert abs(i['likelihood_score']) >= 75
        assert abs(i.get('sentiment_score', 0)) >= 0.5
        
    print("Verification Passed!")

if __name__ == "__main__":
    verify()
