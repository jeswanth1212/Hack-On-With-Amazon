import pandas as pd
import numpy as np
import copy
from datetime import datetime
from src.models.train_models import load_data, train_models
from src.utils.context_utils import get_current_context

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'=' * 80}")
    print(f"{title.center(80)}")
    print(f"{'=' * 80}")

def print_recommendations(user_id, recommendations, itemid_to_title, itemid_to_genres, context=None):
    """Print recommendations in a formatted way"""
    if context:
        ctx_str = []
        if 'mood' in context and context['mood']:
            ctx_str.append(f"Mood: {context['mood']}")
        if 'age' in context and context['age']:
            ctx_str.append(f"Age: {context['age']}")
        if 'time_of_day' in context and context['time_of_day']:
            ctx_str.append(f"Time: {context['time_of_day']}")
        if 'day_of_week' in context and context['day_of_week']:
            ctx_str.append(f"Day: {context['day_of_week']}")
        if 'weather' in context and context['weather']:
            ctx_str.append(f"Weather: {context['weather']}")
        if 'temperature' in context and context['temperature']:
            ctx_str.append(f"Temp: {context['temperature']}°C")
        
        print(f"CONTEXT: {', '.join(ctx_str)}")
    
    for i, (item_id, score) in enumerate(recommendations):
        title = itemid_to_title.get(item_id, 'Unknown')
        genres = itemid_to_genres.get(item_id, '')
        print(f"  {i+1}. {title} (ID: {item_id}) - Score: {score:.4f}")
        print(f"     Genres: {genres}")
    print("\n")

def test_recommendation_scenarios():
    """Test the recommendation system with different scenarios"""
    print_header("LOADING DATA AND TRAINING MODELS")
    movies_df, users_df, interactions_df = load_data()
    engine = train_models(movies_df, users_df, interactions_df)

    # Build a mapping from item_id to title and genres
    itemid_to_title = dict(zip(movies_df['item_id'], movies_df['title']))
    itemid_to_genres = {}
    if 'genres' in movies_df.columns:
        itemid_to_genres = dict(zip(movies_df['item_id'], movies_df['genres']))

    # Get real context data as base
    base_context = get_current_context()
    print(f"Base context: {base_context}")

    # Define test scenarios
    scenarios = [
        # Age-based scenarios
        {"name": "Child", "context": {"mood": "happy", "age": 8, "time_of_day": "afternoon", "weather": "sunny"}},
        {"name": "Teen", "context": {"mood": "excited", "age": 16, "time_of_day": "evening", "weather": "clear"}},
        {"name": "Young Adult", "context": {"mood": "relaxed", "age": 25, "time_of_day": "night", "weather": "clear"}},
        {"name": "Senior", "context": {"mood": "neutral", "age": 70, "time_of_day": "morning", "weather": "cloudy"}},
        
        # Mood-based scenarios
        {"name": "Happy Mood", "context": {"mood": "happy", "age": 30, "time_of_day": "afternoon", "weather": "sunny"}},
        {"name": "Sad Mood", "context": {"mood": "sad", "age": 30, "time_of_day": "afternoon", "weather": "rainy"}},
        {"name": "Excited Mood", "context": {"mood": "excited", "age": 30, "time_of_day": "evening", "weather": "clear"}},
        {"name": "Relaxed Mood", "context": {"mood": "relaxed", "age": 30, "time_of_day": "evening", "weather": "clear"}},
        
        # Time-based scenarios
        {"name": "Morning Time", "context": {"mood": "neutral", "age": 30, "time_of_day": "morning", "weather": "clear"}},
        {"name": "Evening Time", "context": {"mood": "neutral", "age": 30, "time_of_day": "evening", "weather": "clear"}},
        {"name": "Night Time", "context": {"mood": "neutral", "age": 30, "time_of_day": "night", "weather": "clear"}},
        
        # Weather-based scenarios
        {"name": "Sunny Weather", "context": {"mood": "neutral", "age": 30, "time_of_day": "afternoon", "weather": "sunny"}},
        {"name": "Rainy Weather", "context": {"mood": "neutral", "age": 30, "time_of_day": "afternoon", "weather": "rainy"}},
        {"name": "Snowy Weather", "context": {"mood": "neutral", "age": 30, "time_of_day": "afternoon", "weather": "snowy"}},
        
        # Special combinations
        {"name": "Friday Night", "context": {"mood": "excited", "age": 25, "time_of_day": "night", "day_of_week": "Friday", "weather": "clear"}},
        {"name": "Rainy Sunday", "context": {"mood": "sad", "age": 30, "time_of_day": "morning", "day_of_week": "Sunday", "weather": "rainy"}},
        {"name": "Holiday Special", "context": {"mood": "happy", "age": 35, "time_of_day": "evening", "day_of_week": "Saturday", "weather": "snowy", "temperature": 0.5}},
    ]

    # Test users
    test_users = users_df['user_id'].tolist()[:2]  # Use two test users

    for scenario in scenarios:
        print_header(f"SCENARIO: {scenario['name']}")
        
        # Create context by merging base context with scenario context
        context = copy.deepcopy(base_context)
        for key, value in scenario['context'].items():
            context[key] = value
        
        # Test for each user
        for user_id in test_users:
            print(f"\nUSER {user_id} RECOMMENDATIONS:")
            
            # Get recommendations without context (baseline)
            baseline_recs = engine.get_recommendations(user_id, n=5)
            
            print("BASELINE RECOMMENDATIONS (NO CONTEXT):")
            print_recommendations(user_id, baseline_recs, itemid_to_title, itemid_to_genres)
            
            # Get recommendations with this scenario's context
            context_recs = engine.get_recommendations(user_id, n=5, context_data=context)
            
            print(f"RECOMMENDATIONS WITH {scenario['name'].upper()} CONTEXT:")
            print_recommendations(user_id, context_recs, itemid_to_title, itemid_to_genres, context)
            
            # Analyze differences
            baseline_ids = [item_id for item_id, _ in baseline_recs]
            context_ids = [item_id for item_id, _ in context_recs]
            
            different_items = sum(1 for item in context_ids if item not in baseline_ids)
            print(f"Impact Analysis: {different_items} of 5 recommendations are different due to {scenario['name']} context\n")
    
    # Test interaction scenarios
    print_header("INTERACTION SCENARIOS")
    
    # Use the first test user
    user_id = test_users[0]
    
    # Get baseline recommendations
    print(f"\nUSER {user_id} INTERACTION TEST:")
    baseline_recs = engine.get_recommendations(user_id, n=5)
    print("INITIAL RECOMMENDATIONS:")
    print_recommendations(user_id, baseline_recs, itemid_to_title, itemid_to_genres)
    
    # Simulate watching the top movie
    if baseline_recs:
        watched_item_id = baseline_recs[0][0]
        watched_title = itemid_to_title.get(watched_item_id, 'Unknown')
        print(f"USER WATCHES: {watched_title}")
        
        # Record with different moods to see impact
        moods = ["happy", "sad", "excited", "relaxed", "neutral"]
        
        for mood in moods:
            context = copy.deepcopy(base_context)
            context["mood"] = mood
            
            # Create a copy of the engine for this test
            # (To avoid previous interactions affecting subsequent tests)
            test_engine = copy.deepcopy(engine)
            
            # Record interaction with this mood
            print(f"\nRECORDING INTERACTION WITH MOOD: {mood}")
            test_engine.record_interaction(user_id, watched_item_id, sentiment_score=1.0, context_data=context)
            
            # Get new recommendations
            new_recs = test_engine.get_recommendations(user_id, n=5, context_data=context)
            print(f"RECOMMENDATIONS AFTER WATCHING WITH {mood.upper()} MOOD:")
            print_recommendations(user_id, new_recs, itemid_to_title, itemid_to_genres, context)
            
            # Check if watched item was removed
            if watched_item_id in [item_id for item_id, _ in new_recs]:
                print(f"WARNING: Watched movie still in recommendations with {mood} mood\n")
            else:
                print(f"SUCCESS: Watched movie removed from recommendations with {mood} mood\n")
                
            # Calculate recommendation changes
            baseline_ids = [item_id for item_id, _ in baseline_recs]
            new_ids = [item_id for item_id, _ in new_recs]
            
            new_items = [item_id for item_id in new_ids if item_id not in baseline_ids]
            if new_items:
                print(f"New recommendations introduced with {mood} mood:")
                for item_id in new_items:
                    title = itemid_to_title.get(item_id, 'Unknown')
                    print(f"  - {title}")
                print()

if __name__ == "__main__":
    test_recommendation_scenarios() 