from config.settings import settings
import yaml

def verify():
    # Mock config
    sites_config = {
        'email_min_score': 75,
        'email_min_sentiment': 0.5,
        'email_max_negative_score': 25,
        'email_max_negative_sentiment': -0.5
    }
    
    # Mock insights
    all_insights = [
        {'likelihood_score': 80, 'sentiment_score': 0.6, 'snippet': 'High score, High sentiment (KEEP POS)'},
        {'likelihood_score': 20, 'sentiment_score': -0.7, 'snippet': 'Low score, High negative sentiment (KEEP NEG)'},
        {'likelihood_score': 80, 'sentiment_score': 0.2, 'snippet': 'High score, Low sentiment (DROP)'},
        {'likelihood_score': 50, 'sentiment_score': -0.8, 'snippet': 'Mid score, High negative sentiment (DROP)'},
        {'likelihood_score': 75, 'sentiment_score': 0.5, 'snippet': 'Boundary score, Boundary sentiment (KEEP POS)'},
        {'likelihood_score': 25, 'sentiment_score': -0.5, 'snippet': 'Boundary score neg, Boundary sentiment neg (KEEP NEG)'}
    ]
    
    # Logic from main.py
    min_pos_score = sites_config.get('email_min_score', 75)
    min_pos_sentiment = sites_config.get('email_min_sentiment', 0.5)
    max_neg_score = sites_config.get('email_max_negative_score', 25)
    max_neg_sentiment = sites_config.get('email_max_negative_sentiment', -0.5)
    
    print(f"Pos Thresholds: score>={min_pos_score}, sentiment>={min_pos_sentiment}")
    print(f"Neg Thresholds: score<={max_neg_score}, sentiment<={max_neg_sentiment}")
    
    positive_insights = [
        i for i in all_insights 
        if i['likelihood_score'] >= min_pos_score and i.get('sentiment_score', 0) >= min_pos_sentiment
    ]
    
    negative_insights = [
        i for i in all_insights 
        if i['likelihood_score'] <= max_neg_score and i.get('sentiment_score', 0) <= max_neg_sentiment
    ]
    
    print(f"Total insights: {len(all_insights)}")
    print(f"Filtered POS insights: {len(positive_insights)}")
    print(f"Filtered NEG insights: {len(negative_insights)}")
    
    for i in positive_insights:
        print(f"  POS Kept: Score={i['likelihood_score']}, Sentiment={i.get('sentiment_score', 0)}")
        
    for i in negative_insights:
        print(f"  NEG Kept: Score={i['likelihood_score']}, Sentiment={i.get('sentiment_score', 0)}")
    
    # Assertions
    assert len(positive_insights) == 2
    assert len(negative_insights) == 2
    
    for i in positive_insights:
        assert i['likelihood_score'] >= 75
        assert i.get('sentiment_score', 0) >= 0.5
        
    for i in negative_insights:
        assert i['likelihood_score'] <= 25
        assert i.get('sentiment_score', 0) <= -0.5
        
    print("Verification Passed!")

if __name__ == "__main__":
    verify()
