from config.settings import settings
import yaml

def verify_logic():
    # Mock config
    sites_config = {'email_min_score': 75}
    
    # Mock insights
    all_insights = [
        {'likelihood_score': 0.8, 'snippet': 'High score'},
        {'likelihood_score': -0.9, 'snippet': 'High negative score'},
        {'likelihood_score': 0.5, 'snippet': 'Low score'},
        {'likelihood_score': 0.74, 'snippet': 'Boundary score'}
    ]
    
    # Logic from main.py
    min_score = sites_config.get('email_min_score', 75)
    if min_score > 1:
        min_score /= 100.0
        
    print(f"Threshold: {min_score}")
    
    filtered_insights = [i for i in all_insights if abs(i['likelihood_score']) >= min_score]
    
    print(f"Original count: {len(all_insights)}")
    print(f"Filtered count: {len(filtered_insights)}")
    
    for i in filtered_insights:
        print(f"  Kept: {i['likelihood_score']}")
        
    # Assertions
    assert len(filtered_insights) == 2
    assert any(i['likelihood_score'] == 0.8 for i in filtered_insights)
    assert any(i['likelihood_score'] == -0.9 for i in filtered_insights)
    assert not any(i['likelihood_score'] == 0.5 for i in filtered_insights)
    
    print("Verification Passed!")

if __name__ == "__main__":
    verify_logic()
