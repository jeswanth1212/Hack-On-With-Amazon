import requests

# Get recommendations for a specific user
user_id = '1'
num_recs = 3

url = f'http://localhost:8000/recommend?user_id={user_id}&n={num_recs}'
try:
    print(f"Getting recommendations for user {user_id}...")
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        recs = response.json()
        print(f"Found {len(recs)} recommendations:")
        for i, item in enumerate(recs):
            print(f"{i+1}. {item.get('title')} (Score: {item.get('score'):.2f})")
            print(f"   Genres: {item.get('genres')}")
            print(f"   Year: {item.get('release_year')}")
            print("")
    else:
        print(f"Error: Status code {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error making request: {e}") 