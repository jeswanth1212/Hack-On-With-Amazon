import requests
import json

def get_recommendations(user_id, n=5, mood=None):
    """
    Get recommendations for a user through the API
    """
    # Prepare URL with parameters
    url = f"http://localhost:8000/recommend?user_id={user_id}&n={n}"
    if mood:
        url += f"&mood={mood}"
    
    try:
        # Make the request with timeout
        response = requests.get(url, timeout=10)
        recommendations = response.json()
        
        print(f"Found {len(recommendations)} recommendations for user {user_id}")
        
        # Print each recommendation
        for i, item in enumerate(recommendations):
            print(f"{i+1}. {item.get('title')} (Score: {item.get('score'):.2f})")
            print(f"   Genre: {item.get('genres')}")
            print(f"   Year: {item.get('release_year')}")
            if item.get('overview'):
                print(f"   Overview: {item.get('overview')[:100]}...")
            print("")
    except requests.exceptions.Timeout:
        print(f"Request timed out for user {user_id}")
    except Exception as e:
        print(f"Error getting recommendations for user {user_id}: {e}")

# Test with a specific user
user_id = "1"
print(f"\nRECOMMENDATIONS FOR USER {user_id}")
print("="*60)

# Get recommendations with default context
get_recommendations(user_id, n=3)

# Test with different moods
moods = ["happy", "sad", "relaxed"]
for mood in moods:
    print(f"\nWith mood: {mood}")
    print("-"*40)
    get_recommendations(user_id, n=2, mood=mood)

print("\nDone!") 