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

def test_mood_and_age():
    """Test how mood and age affect recommendations"""
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
    
    # Test different moods and ages
    moods = ["happy", "sad", "excited", "relaxed", "neutral"]
    ages = [8, 16, 25, 30, 45, 70]
    
    # Test all combinations
    for mood in moods:
        print_header(f"MOOD: {mood.upper()}")
        for age in ages:
            context = copy.deepcopy(base_context)
            context["mood"] = mood
            context["age"] = age
            
            print(f"\nTesting: Mood={mood}, Age={age}")
            recs = engine.get_recommendations(users_df['user_id'].iloc[0], n=5, context_data=context)
            
            # Print recommendations
            print(f"CONTEXT: mood={mood}, age={age}")
            for i, (item_id, score) in enumerate(recs):
                title = itemid_to_title.get(item_id, "Unknown")
                genres = itemid_to_genres.get(item_id, "")
                print(f"  {i+1}. {title} (ID: {item_id}) - Score: {score:.4f}")
                print(f"     Genres: {genres}")
            print()
            
            # Record an interaction and test again
            if i == 0:  # Just for the first age in each mood
                print("Recording interaction with top recommended item...")
                watched_item_id = recs[0][0]
                watched_title = itemid_to_title.get(watched_item_id, "Unknown")
                print(f"Watching: {watched_title}")
                
                # Record the interaction
                engine.record_interaction(
                    users_df['user_id'].iloc[0], 
                    watched_item_id, 
                    sentiment_score=1.0, 
                    context_data=context
                )
                
                # Get new recommendations
                new_recs = engine.get_recommendations(users_df['user_id'].iloc[0], n=5, context_data=context)
                print("\nRECOMMENDATIONS AFTER WATCHING:")
                for i, (item_id, score) in enumerate(new_recs):
                    title = itemid_to_title.get(item_id, "Unknown")
                    genres = itemid_to_genres.get(item_id, "")
                    print(f"  {i+1}. {title} (ID: {item_id}) - Score: {score:.4f}")
                    print(f"     Genres: {genres}")
                
                # Check if watched item was removed
                if watched_item_id in [item_id for item_id, _ in new_recs]:
                    print(f"WARNING: Watched movie still in recommendations")
                else:
                    print(f"SUCCESS: Watched movie removed from recommendations")

if __name__ == "__main__":
    test_mood_and_age()
