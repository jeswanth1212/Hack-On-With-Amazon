import pandas as pd
import numpy as np
import copy
from tabulate import tabulate
import matplotlib.pyplot as plt
from collections import Counter

from src.models.train_models import load_data, train_models
from src.utils.context_utils import get_current_context, get_age_group
from src.models.model import RecommendationEngine

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'=' * 100}")
    print(f"{title.center(100)}")
    print(f"{'=' * 100}")

def compare_recommendations(users_info, recommendations_dict, itemid_to_title, itemid_to_genres):
    """Compare recommendations across different user profiles side by side."""
    # Prepare table data
    table_data = []
    
    # Get the maximum number of recommendations across all users
    max_recs = max(len(recs) for recs in recommendations_dict.values())
    
    # Create headers for the table
    headers = ["#"]
    for user_info in users_info:
        if 'name' in user_info:
            headers.append(f"{user_info['name']} (Age: {user_info['age']})")
        else:
            headers.append(f"User {user_info['user_id']} (Age: {user_info['age']})")
    
    # Add rows for each recommendation
    for i in range(max_recs):
        row = [i+1]
        for user_info in users_info:
            user_id = user_info.get('user_id', user_info.get('name'))
            recs = recommendations_dict[user_id]
            if i < len(recs):
                item_id, score = recs[i]
                title = itemid_to_title.get(item_id, 'Unknown')
                title_short = (title[:25] + '...') if len(title) > 28 else title
                row.append(f"{title_short}\n({item_id}, {score:.2f})")
            else:
                row.append("-")
        table_data.append(row)
    
    # Print the table
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print()

def analyze_genre_differences(users_info, recommendations_dict, itemid_to_genres):
    """Analyze the genre distribution differences between user profiles."""
    user_genres = {}
    
    # Count genres for each user
    for user_info in users_info:
        user_id = user_info.get('user_id', user_info.get('name'))
        recs = recommendations_dict[user_id]
        
        # Count genres
        genres_counter = Counter()
        for item_id, _ in recs:
            genres = itemid_to_genres.get(item_id, '').split('|')
            for genre in genres:
                if genre and genre not in ['', 'NULL', None]:
                    genres_counter[genre] += 1
        
        user_genres[user_id] = genres_counter
    
    # Get all unique genres
    all_genres = set()
    for genres_counter in user_genres.values():
        all_genres.update(genres_counter.keys())
    
    # Create genre comparison table
    table_data = []
    headers = ["Genre"]
    
    for user_info in users_info:
        user_id = user_info.get('user_id', user_info.get('name'))
        if 'name' in user_info:
            headers.append(f"{user_info['name']} (Age: {user_info['age']})")
        else:
            headers.append(f"User {user_info['user_id']} (Age: {user_info['age']})")
    
    # Add percentage column for each user
    for user_info in users_info:
        user_id = user_info.get('user_id', user_info.get('name'))
        headers.append(f"{user_id} %")
    
    # Sort genres by total count across all users
    genre_total_counts = Counter()
    for genres_counter in user_genres.values():
        genre_total_counts.update(genres_counter)
    
    sorted_genres = sorted(all_genres, key=lambda x: -genre_total_counts[x])
    
    # Create rows for each genre
    for genre in sorted_genres:
        row = [genre]
        
        # Add count for each user
        for user_info in users_info:
            user_id = user_info.get('user_id', user_info.get('name'))
            count = user_genres[user_id][genre]
            row.append(count)
        
        # Add percentage for each user
        for user_info in users_info:
            user_id = user_info.get('user_id', user_info.get('name'))
            count = user_genres[user_id][genre]
            total = sum(user_genres[user_id].values())
            percentage = (count / total) * 100 if total else 0
            row.append(f"{percentage:.1f}%")
        
        table_data.append(row)
    
    # Print the table
    print("\nGenre Distribution Comparison:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print()

def test_user_profile_comparison():
    """Test and compare recommendations across different user profiles."""
    print_header("LOADING DATA AND TRAINING MODELS")
    movies_df, users_df, interactions_df = load_data()
    engine = train_models(movies_df, users_df, interactions_df)

    # Build a mapping from item_id to title and genres
    itemid_to_title = dict(zip(movies_df['item_id'], movies_df['title']))
    itemid_to_genres = {}
    if 'genres' in movies_df.columns:
        itemid_to_genres = dict(zip(movies_df['item_id'], movies_df['genres']))

    # Get current context as base
    base_context = get_current_context()
    print(f"Base context: {base_context}")
    
    # Define different age profiles to compare
    age_profiles = [
        {"name": "Child", "age": 10, "age_group": "children", "location": "New York"},
        {"name": "Teen", "age": 16, "age_group": "teen", "location": "Chicago"},
        {"name": "Young Adult", "age": 25, "age_group": "young_adult", "location": "Los Angeles"},
        {"name": "Middle Adult", "age": 45, "age_group": "adult", "location": "Houston"},
        {"name": "Senior", "age": 70, "age_group": "senior", "location": "Boston"}
    ]
    
    # Define context scenarios to test
    context_scenarios = [
        {"name": "Default", "context": {}},
        {"name": "Happy Evening", "context": {"mood": "happy", "time_of_day": "evening"}},
        {"name": "Sad Rainy Day", "context": {"mood": "sad", "weather": "rainy"}},
        {"name": "Excited Weekend", "context": {"mood": "excited", "day_of_week": "Saturday"}},
        {"name": "Relaxed Morning", "context": {"mood": "relaxed", "time_of_day": "morning"}}
    ]
    
    # Use a consistent user_id for testing to isolate the effect of age/profile
    test_user_id = users_df['user_id'].iloc[0]
    
    # Run comparisons for each context scenario
    for scenario in context_scenarios:
        print_header(f"SCENARIO: {scenario['name']}")
        
        # Create context by merging base context with scenario context
        context = copy.deepcopy(base_context)
        for key, value in scenario['context'].items():
            context[key] = value
        
        # Store recommendations for each profile
        recommendations_dict = {}
        
        # Get recommendations for each profile
        for profile in age_profiles:
            # Set age in context
            profile_context = copy.deepcopy(context)
            profile_context['age'] = profile['age']
            
            # Get recommendations
            recommendations = engine.get_recommendations(test_user_id, n=10, context_data=profile_context)
            
            # Store recommendations
            recommendations_dict[profile['name']] = recommendations
        
        # Compare recommendations
        print(f"\nCOMPARING RECOMMENDATIONS FOR DIFFERENT AGE PROFILES:")
        print(f"Context: {', '.join([f'{k}={v}' for k, v in scenario['context'].items()])}")
        compare_recommendations(age_profiles, recommendations_dict, itemid_to_title, itemid_to_genres)
        
        # Analyze genre differences
        analyze_genre_differences(age_profiles, recommendations_dict, itemid_to_genres)
    
    # Test different mood profiles
    print_header("COMPARING MOOD PROFILES")
    
    # Define different mood profiles to compare
    mood_profiles = [
        {"name": "Happy", "age": 30, "mood": "happy"},
        {"name": "Sad", "age": 30, "mood": "sad"},
        {"name": "Excited", "age": 30, "mood": "excited"},
        {"name": "Relaxed", "age": 30, "mood": "relaxed"},
        {"name": "Neutral", "age": 30, "mood": "neutral"}
    ]
    
    # Store recommendations for each mood
    mood_recommendations = {}
    
    # Get recommendations for each mood
    for profile in mood_profiles:
        # Set mood in context
        mood_context = copy.deepcopy(base_context)
        mood_context['age'] = profile['age']
        mood_context['mood'] = profile['mood']
        
        # Get recommendations
        recommendations = engine.get_recommendations(test_user_id, n=10, context_data=mood_context)
        
        # Store recommendations
        mood_recommendations[profile['name']] = recommendations
    
    # Compare recommendations
    print(f"\nCOMPARING RECOMMENDATIONS FOR DIFFERENT MOODS:")
    compare_recommendations(mood_profiles, mood_recommendations, itemid_to_title, itemid_to_genres)
    
    # Analyze genre differences
    analyze_genre_differences(mood_profiles, mood_recommendations, itemid_to_genres)
    
    # Test real users with different profiles
    print_header("COMPARING REAL USERS WITH DIFFERENT PROFILES")
    
    # Try to find users with different age groups
    real_users = []
    if 'age' in users_df.columns and len(users_df) > 10:
        # Find users with different ages
        age_ranges = [(0, 12), (13, 17), (18, 30), (31, 60), (61, 100)]
        for min_age, max_age in age_ranges:
            matching_users = users_df[(users_df['age'] >= min_age) & (users_df['age'] <= max_age)]
            if len(matching_users) > 0:
                user = matching_users.iloc[0]
                age_group = get_age_group(user['age']) if 'age' in user else None
                real_users.append({
                    'user_id': user['user_id'],
                    'age': user['age'],
                    'age_group': age_group,
                    'location': user['location'] if 'location' in user else None
                })
    
    # If we found enough real users with different age groups
    if len(real_users) >= 3:
        # Store recommendations for each real user
        real_user_recommendations = {}
        
        # Get recommendations for each real user
        for user_info in real_users:
            # Set age in context
            user_context = copy.deepcopy(base_context)
            user_context['age'] = user_info['age']
            
            # Get recommendations for this user
            recommendations = engine.get_recommendations(user_info['user_id'], n=10, context_data=user_context)
            
            # Store recommendations
            real_user_recommendations[user_info['user_id']] = recommendations
        
        # Compare recommendations
        print(f"\nCOMPARING RECOMMENDATIONS FOR {len(real_users)} REAL USERS WITH DIFFERENT AGES:")
        compare_recommendations(real_users, real_user_recommendations, itemid_to_title, itemid_to_genres)
        
        # Analyze genre differences
        analyze_genre_differences(real_users, real_user_recommendations, itemid_to_genres)
    else:
        print("\nNot enough real users with different age groups found for comparison.")

if __name__ == "__main__":
    test_user_profile_comparison() 