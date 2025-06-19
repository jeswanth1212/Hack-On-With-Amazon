import os
import pandas as pd
import numpy as np
from tabulate import tabulate
from datetime import datetime
import random
import time

from src.models.train_models import load_data, train_models
from src.utils.context_utils import get_current_context
from src.data.database import (
    init_db, add_user, add_item, add_interaction,
    get_user_interactions, get_item_details, get_all_users
)

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'=' * 100}")
    print(f"{title.center(100)}")
    print(f"{'=' * 100}")

def print_recommendations(recommendations, itemid_to_title, itemid_to_genres):
    """Print recommendations in a formatted way."""
    # Create a table for recommendations
    table_data = []
    for i, (item_id, score) in enumerate(recommendations):
        title = itemid_to_title.get(item_id, 'Unknown')
        genres = itemid_to_genres.get(item_id, '')
        table_data.append([i+1, title, item_id, f"{score:.4f}", genres])
    
    headers = ["#", "Title", "ID", "Score", "Genres"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print()

def print_user_history(user_id):
    """Print a user's watch history from the database."""
    interactions = get_user_interactions(user_id)
    
    if not interactions:
        print(f"No interactions found for user {user_id}")
        return
    
    # Create a table for interactions
    table_data = []
    for i, interaction in enumerate(interactions):
        item_id = interaction['item_id']
        title = interaction.get('title', 'Unknown')
        genres = interaction.get('genres', '')
        sentiment_score = interaction.get('sentiment_score', 0.0)
        mood = interaction.get('mood', 'Unknown')
        time_of_day = interaction.get('time_of_day', 'Unknown')
        
        table_data.append([
            i+1, title, item_id, f"{sentiment_score:.2f}", 
            mood, time_of_day, genres
        ])
    
    headers = ["#", "Title", "ID", "Rating", "Mood", "Time", "Genres"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print()

def create_diverse_users():
    """Create users with different demographics."""
    users = [
        {
            "user_id": "user_young_action", 
            "age": 18, 
            "age_group": "young_adult", 
            "location": "New York"
        },
        {
            "user_id": "user_adult_drama", 
            "age": 35, 
            "age_group": "adult", 
            "location": "Los Angeles"
        },
        {
            "user_id": "user_senior_comedy", 
            "age": 65, 
            "age_group": "senior", 
            "location": "Chicago"
        },
        {
            "user_id": "user_teen_scifi", 
            "age": 16, 
            "age_group": "teen", 
            "location": "Seattle"
        },
        {
            "user_id": "user_parent_family", 
            "age": 42, 
            "age_group": "adult", 
            "location": "Austin"
        }
    ]
    
    for user in users:
        add_user(
            user_id=user["user_id"],
            age=user["age"],
            age_group=user["age_group"],
            location=user["location"]
        )
        print(f"Added user: {user['user_id']} (Age: {user['age']}, Location: {user['location']})")
    
    return users

def get_movies_by_genre(movies_df, genre, n=3):
    """Get n movies of a specific genre."""
    # Filter movies by genre
    genre_movies = movies_df[movies_df['genres'].str.contains(genre, na=False)]
    
    # If not enough movies, use random ones
    if len(genre_movies) < n:
        return movies_df.sample(n).to_dict('records')
    
    # Return n random movies from the filtered list
    return genre_movies.sample(n).to_dict('records')

def build_user_preferences(users, movies_df, engine):
    """Build user watch history based on preferences."""
    user_preferences = {
        "user_young_action": ["Action", "Adventure", "Thriller"],
        "user_adult_drama": ["Drama", "Crime", "Mystery"],
        "user_senior_comedy": ["Comedy", "Romance"],
        "user_teen_scifi": ["Sci-Fi", "Fantasy"],
        "user_parent_family": ["Family", "Animation", "Children"]
    }
    
    # Various context scenarios to make the data more realistic
    mood_options = ["happy", "sad", "excited", "relaxed", "neutral"]
    time_options = ["morning", "afternoon", "evening", "night"]
    day_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weather_options = ["sunny", "rainy", "cloudy", "snowy", "windy"]
    
    for user_id, genres in user_preferences.items():
        print(f"\nBuilding history for {user_id} with preferences: {', '.join(genres)}")
        
        for genre in genres:
            # Get movies of this genre
            genre_movies = get_movies_by_genre(movies_df, genre)
            
            for movie in genre_movies:
                # Create random context data
                context_data = {
                    "mood": random.choice(mood_options),
                    "time_of_day": random.choice(time_options),
                    "day_of_week": random.choice(day_options),
                    "weather": random.choice(weather_options),
                }
                
                # Get user age from our users list
                user_info = next((u for u in users if u["user_id"] == user_id), None)
                if user_info:
                    context_data["age"] = user_info["age"]
                
                # Movies matching user preferences get higher ratings
                sentiment_score = random.uniform(0.7, 1.0)
                
                # Record the interaction in the database
                add_interaction(
                    user_id=user_id,
                    item_id=movie["item_id"],
                    sentiment_score=sentiment_score,
                    mood=context_data["mood"],
                    time_of_day=context_data["time_of_day"],
                    day_of_week=context_data["day_of_week"],
                    weather=context_data["weather"],
                    age=context_data.get("age"),
                    event_type="watch"
                )
                
                # Also record the interaction in the engine for recommendations
                engine.record_interaction(
                    user_id=user_id,
                    item_id=movie["item_id"],
                    sentiment_score=sentiment_score,
                    context_data=context_data
                )
                
                print(f"  Added interaction: {movie['title']} (Genre: {movie['genres']})")
                
                # Small delay to make timestamps different
                time.sleep(0.1)

def simulate_recommendation_scenarios(users, movies_df, engine, itemid_to_title, itemid_to_genres):
    """Simulate different recommendation scenarios with context."""
    # Define context scenarios
    scenarios = [
        {
            "name": "Happy Evening",
            "context": {"mood": "happy", "time_of_day": "evening", "weather": "clear"}
        },
        {
            "name": "Sad Rainy Day",
            "context": {"mood": "sad", "time_of_day": "afternoon", "weather": "rainy"}
        },
        {
            "name": "Excited Weekend",
            "context": {"mood": "excited", "time_of_day": "night", "day_of_week": "Saturday"}
        }
    ]
    
    for user in users:
        user_id = user["user_id"]
        print_header(f"RECOMMENDATIONS FOR {user_id}")
        
        # First get baseline recommendations without context
        print("\nBASELINE RECOMMENDATIONS (No Context):")
        baseline_recs = engine.get_recommendations(user_id, n=5)
        print_recommendations(baseline_recs, itemid_to_title, itemid_to_genres)
        
        # Then get recommendations for each scenario
        for scenario in scenarios:
            # Add user age to context
            context = scenario["context"].copy()
            context["age"] = user["age"]
            
            print(f"\nSCENARIO: {scenario['name']}")
            print(f"Context: {context}")
            
            scenario_recs = engine.get_recommendations(user_id, n=5, context_data=context)
            print_recommendations(scenario_recs, itemid_to_title, itemid_to_genres)
            
            # Compare with baseline
            baseline_items = [item_id for item_id, _ in baseline_recs]
            scenario_items = [item_id for item_id, _ in scenario_recs]
            
            new_items = [item for item in scenario_items if item not in baseline_items]
            removed_items = [item for item in baseline_items if item not in scenario_items]
            
            if new_items:
                print(f"New items due to context: {len(new_items)}")
                for item_id in new_items:
                    print(f"  - {itemid_to_title.get(item_id, 'Unknown')}")
            
            # Simulate watching one of the recommended movies
            if scenario_recs:
                watched_item_id, _ = scenario_recs[0]
                watched_title = itemid_to_title.get(watched_item_id, 'Unknown')
                
                print(f"\nUser watches: {watched_title}")
                
                # Record in database
                add_interaction(
                    user_id=user_id,
                    item_id=watched_item_id,
                    sentiment_score=0.9,  # Assume they liked it
                    mood=context["mood"],
                    time_of_day=context["time_of_day"],
                    day_of_week=context.get("day_of_week"),
                    weather=context.get("weather"),
                    age=context.get("age"),
                    event_type="watch"
                )
                
                # Record in engine
                engine.record_interaction(
                    user_id=user_id,
                    item_id=watched_item_id,
                    sentiment_score=0.9,
                    context_data=context
                )
                
                # Get new recommendations
                print("\nUPDATED RECOMMENDATIONS AFTER WATCHING:")
                updated_recs = engine.get_recommendations(user_id, n=5, context_data=context)
                print_recommendations(updated_recs, itemid_to_title, itemid_to_genres)
                
                # Check if watched item was removed
                if watched_item_id not in [item_id for item_id, _ in updated_recs]:
                    print(f"SUCCESS: {watched_title} was removed from recommendations")
                else:
                    print(f"NOTE: {watched_title} is still in recommendations")

def main():
    """Main function to demonstrate the recommendation system."""
    # Initialize the database
    init_db()
    
    # Load data
    print_header("LOADING DATA AND TRAINING MODELS")
    movies_df, users_df, interactions_df = load_data()
    engine = train_models(movies_df, users_df, interactions_df)
    
    # Build mappings for display
    itemid_to_title = dict(zip(movies_df['item_id'], movies_df['title']))
    itemid_to_genres = {}
    if 'genres' in movies_df.columns:
        itemid_to_genres = dict(zip(movies_df['item_id'], movies_df['genres']))
    
    # Create users
    print_header("CREATING DIVERSE USERS")
    users = create_diverse_users()
    
    # Build user preferences
    print_header("BUILDING USER WATCH HISTORY")
    build_user_preferences(users, movies_df, engine)
    
    # Print user history from database
    print_header("USER WATCH HISTORY FROM DATABASE")
    for user in users:
        print(f"\nWATCH HISTORY FOR {user['user_id']}:")
        print_user_history(user['user_id'])
    
    # Simulate recommendation scenarios
    print_header("SIMULATING RECOMMENDATION SCENARIOS")
    simulate_recommendation_scenarios(users, movies_df, engine, itemid_to_title, itemid_to_genres)
    
    # Final summary
    print_header("SUMMARY")
    print("Successfully demonstrated the complete recommendation flow:")
    print("1. Created diverse users with different demographics")
    print("2. Built personalized watch history for each user")
    print("3. Generated baseline recommendations without context")
    print("4. Applied different contextual scenarios to recommendations")
    print("5. Simulated watching recommended content")
    print("6. Generated updated recommendations after interactions")
    print("7. Confirmed all data was properly stored in the database")

if __name__ == "__main__":
    main() 