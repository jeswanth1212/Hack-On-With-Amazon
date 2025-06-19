import pandas as pd
import numpy as np
import os
import copy
from tabulate import tabulate
from pathlib import Path

from src.models.train_models import load_data, train_models
from src.utils.context_utils import get_current_context, get_age_group
from src.models.model import RecommendationEngine

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'=' * 80}")
    print(f"{title.center(80)}")
    print(f"{'=' * 80}")

def print_recommendations(user_id, recommendations, itemid_to_title, itemid_to_genres, user_info=None, context=None):
    """Print recommendations in a formatted way."""
    if user_info:
        user_str = []
        if 'age' in user_info and user_info['age']:
            user_str.append(f"Age: {user_info['age']}")
        if 'age_group' in user_info and user_info['age_group']:
            user_str.append(f"Age Group: {user_info['age_group']}")
        if 'location' in user_info and user_info['location']:
            user_str.append(f"Location: {user_info['location']}")
        
        print(f"USER PROFILE: {', '.join(user_str)}")
    
    if context:
        ctx_str = []
        if 'mood' in context and context['mood']:
            ctx_str.append(f"Mood: {context['mood']}")
        if 'time_of_day' in context and context['time_of_day']:
            ctx_str.append(f"Time: {context['time_of_day']}")
        if 'day_of_week' in context and context['day_of_week']:
            ctx_str.append(f"Day: {context['day_of_week']}")
        if 'weather' in context and context['weather']:
            ctx_str.append(f"Weather: {context['weather']}")
        
        print(f"CONTEXT: {', '.join(ctx_str)}")
    
    # Create a table for recommendations
    table_data = []
    for i, (item_id, score) in enumerate(recommendations):
        title = itemid_to_title.get(item_id, 'Unknown')
        genres = itemid_to_genres.get(item_id, '')
        table_data.append([i+1, title, item_id, f"{score:.4f}", genres])
    
    headers = ["#", "Title", "ID", "Score", "Genres"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print()

def analyze_genre_distribution(recommendations, itemid_to_genres):
    """Analyze the genre distribution in recommendations."""
    all_genres = []
    genre_counts = {}
    
    for item_id, _ in recommendations:
        genres = itemid_to_genres.get(item_id, '').split('|')
        for genre in genres:
            if genre and genre not in ['', 'NULL', None]:
                all_genres.append(genre)
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    # Sort by count
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Print distribution
    print("Genre Distribution:")
    table_data = []
    for genre, count in sorted_genres:
        percentage = (count / len(all_genres)) * 100 if all_genres else 0
        table_data.append([genre, count, f"{percentage:.1f}%"])
    
    headers = ["Genre", "Count", "Percentage"]
    print(tabulate(table_data, headers=headers, tablefmt="simple"))
    print()

def test_user_profiles():
    """Test how different user profiles affect recommendations."""
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
    
    # Define different user profile types
    user_profiles = [
        # Child profiles
        {"name": "Young Child", "age": 8, "age_group": "children", "location": "New York"},
        {"name": "Older Child", "age": 12, "age_group": "children", "location": "Chicago"},
        
        # Teen profiles
        {"name": "Young Teen", "age": 14, "age_group": "teen", "location": "Los Angeles"},
        {"name": "Older Teen", "age": 17, "age_group": "teen", "location": "Houston"},
        
        # Young Adult profiles
        {"name": "College Student", "age": 20, "age_group": "young_adult", "location": "Boston"},
        {"name": "Young Professional", "age": 28, "age_group": "young_adult", "location": "San Francisco"},
        
        # Adult profiles
        {"name": "Middle-aged Adult", "age": 42, "age_group": "adult", "location": "Seattle"},
        {"name": "Older Adult", "age": 55, "age_group": "adult", "location": "Denver"},
        
        # Senior profiles
        {"name": "Young Senior", "age": 65, "age_group": "senior", "location": "Phoenix"},
        {"name": "Elderly", "age": 78, "age_group": "senior", "location": "Miami"},
    ]
    
    # Use either real users from the database or these test profiles
    real_users = []
    try:
        # Try to get users with different age groups
        if 'age' in users_df.columns and 'age_group' in users_df.columns:
            # Group users by age_group
            age_groups = users_df['age_group'].unique()
            for age_group in age_groups:
                group_users = users_df[users_df['age_group'] == age_group]
                if len(group_users) > 0:
                    # Take the first user from each age group
                    real_users.append({
                        'user_id': group_users['user_id'].iloc[0],
                        'age': group_users['age'].iloc[0],
                        'age_group': age_group,
                        'location': group_users['location'].iloc[0] if 'location' in group_users.columns else None
                    })
        
        # If we found users with different age groups, use them
        if len(real_users) >= 3:
            print(f"Using {len(real_users)} real users with different age groups")
            test_subjects = real_users
        else:
            # Not enough diverse real users, fall back to test profiles
            print("Not enough diverse real users found, using test profiles")
            test_subjects = user_profiles
    except Exception as e:
        print(f"Error getting real users: {e}, using test profiles")
        test_subjects = user_profiles
    
    # Define context scenarios to test
    context_scenarios = [
        {"name": "Default", "context": {}},
        {"name": "Happy Evening", "context": {"mood": "happy", "time_of_day": "evening"}},
        {"name": "Sad Rainy Day", "context": {"mood": "sad", "weather": "rainy"}},
        {"name": "Excited Weekend", "context": {"mood": "excited", "day_of_week": "Saturday"}},
        {"name": "Relaxed Morning", "context": {"mood": "relaxed", "time_of_day": "morning"}}
    ]
    
    # Keep track of common movies across different user profiles
    common_recommendations = {}
    all_recommended_movies = set()
    
    # Test each profile
    for subject in test_subjects:
        if 'user_id' in subject:
            # This is a real user
            print_header(f"REAL USER: {subject['user_id']} - {subject['age_group'].upper()} (Age: {subject['age']})")
            user_id = subject['user_id']
            user_info = subject
        else:
            # This is a test profile
            print_header(f"TEST PROFILE: {subject['name']} - {subject['age_group'].upper()} (Age: {subject['age']})")
            # Use a fixed user_id for testing
            user_id = users_df['user_id'].iloc[0]
            user_info = subject
        
        # Store recommendations for this user
        user_recommendations = []
        
        for scenario in context_scenarios:
            print(f"\n--- Scenario: {scenario['name']} ---")
            
            # Create context by merging base context with scenario context
            context = copy.deepcopy(base_context)
            for key, value in scenario['context'].items():
                context[key] = value
            
            # Set age in context
            context['age'] = subject['age']
            
            # Get recommendations
            recommendations = engine.get_recommendations(user_id, n=10, context_data=context)
            
            # Store all recommended movies
            for item_id, _ in recommendations:
                all_recommended_movies.add(item_id)
            
            # Store recommendations for this user and scenario
            for item_id, _ in recommendations:
                if item_id not in common_recommendations:
                    common_recommendations[item_id] = 0
                common_recommendations[item_id] += 1
            
            # Store for user-specific analysis
            user_recommendations.extend([item_id for item_id, _ in recommendations])
            
            # Print recommendations
            print_recommendations(user_id, recommendations, itemid_to_title, itemid_to_genres, user_info, context)
            
            # Analyze genre distribution
            analyze_genre_distribution(recommendations, itemid_to_genres)
    
    # Calculate overall recommendation statistics
    print_header("RECOMMENDATION ANALYSIS")
    
    # Find most common recommendations across all profiles
    sorted_common = sorted(common_recommendations.items(), key=lambda x: x[1], reverse=True)
    
    print("Most Common Recommendations Across All Profiles:")
    table_data = []
    for item_id, count in sorted_common[:10]:  # Top 10
        title = itemid_to_title.get(item_id, 'Unknown')
        genres = itemid_to_genres.get(item_id, '')
        percentage = (count / (len(test_subjects) * len(context_scenarios))) * 100
        table_data.append([title, item_id, count, f"{percentage:.1f}%", genres])
    
    headers = ["Title", "ID", "Times Recommended", "% of Tests", "Genres"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    print(f"\nTotal unique movies recommended: {len(all_recommended_movies)}")
    print(f"Number of test scenarios: {len(test_subjects) * len(context_scenarios)}")

if __name__ == "__main__":
    test_user_profiles() 