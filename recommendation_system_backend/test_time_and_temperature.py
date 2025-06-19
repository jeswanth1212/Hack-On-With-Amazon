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

def print_recommendations(recommendations, itemid_to_title, itemid_to_genres, context=None):
    """Print recommendations in a formatted way"""
    if context:
        ctx_str = []
        for key, value in context.items():
            if value is not None:
                ctx_str.append(f"{key}: {value}")
        
        print(f"CONTEXT: {', '.join(ctx_str)}")
    
    for i, (item_id, score) in enumerate(recommendations):
        title = itemid_to_title.get(item_id, 'Unknown')
        genres = itemid_to_genres.get(item_id, '')
        print(f"  {i+1}. {title} (ID: {item_id}) - Score: {score:.4f}")
        print(f"     Genres: {genres}")
    print("\n")

def analyze_genres(recommendations, itemid_to_genres):
    """Analyze genre distributions in recommendations"""
    genre_counts = {}
    for item_id, _ in recommendations:
        genres = itemid_to_genres.get(item_id, '').split('|')
        for genre in genres:
            if genre:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    # Sort by count
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    print("Genre distribution:")
    for genre, count in sorted_genres:
        print(f"  {genre}: {count}")
    print()
    
    return genre_counts

def test_time_and_temperature():
    """Test how time of day and temperature affect recommendations"""
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
    
    # Select a test user
    test_user = users_df['user_id'].tolist()[0]
    
    # Get baseline recommendations (without context)
    baseline_recs = engine.get_recommendations(test_user, n=10)
    print("\nBASELINE RECOMMENDATIONS (NO CONTEXT):")
    print_recommendations(baseline_recs, itemid_to_title, itemid_to_genres)
    baseline_genres = analyze_genres(baseline_recs, itemid_to_genres)
    
    # Test different times of day
    print_header("TIME OF DAY TEST")
    times = [
        "early_morning",  # 5-7 AM
        "morning",        # 7-11 AM
        "noon",           # 11-1 PM
        "afternoon",      # 1-5 PM
        "evening",        # 5-8 PM
        "night",          # 8-11 PM
        "late_night"      # 11 PM-5 AM
    ]
    
    time_genre_data = {}
    
    for time_of_day in times:
        print(f"\nTIME OF DAY: {time_of_day.upper()}")
        
        # Create context with this time
        context = copy.deepcopy(base_context)
        context["time_of_day"] = time_of_day
        context["mood"] = "neutral"  # Keep other factors neutral
        context["age"] = 30
        
        # Get recommendations
        recs = engine.get_recommendations(test_user, n=10, context_data=context)
        print_recommendations(recs, itemid_to_title, itemid_to_genres, context)
        
        # Analyze genre distribution
        genre_counts = analyze_genres(recs, itemid_to_genres)
        time_genre_data[time_of_day] = genre_counts
        
        # Compare to baseline
        baseline_ids = [item_id for item_id, _ in baseline_recs]
        time_ids = [item_id for item_id, _ in recs]
        
        different_items = sum(1 for item in time_ids if item not in baseline_ids)
        print(f"Impact Analysis: {different_items} of 10 recommendations are different due to time being {time_of_day}")
        
        # Print top genres that changed
        print("Genres that increased in prominence:")
        for genre, count in genre_counts.items():
            baseline_count = baseline_genres.get(genre, 0)
            if count > baseline_count:
                print(f"  {genre}: +{count - baseline_count}")
    
    # Test different temperatures
    print_header("TEMPERATURE TEST")
    temperatures = [-10, 0, 5, 10, 15, 20, 25, 30, 35, 40]
    
    temp_genre_data = {}
    
    for temp in temperatures:
        print(f"\nTEMPERATURE: {temp}°C")
        
        # Create context with this temperature
        context = copy.deepcopy(base_context)
        context["temperature"] = temp
        context["mood"] = "neutral"  # Keep other factors neutral
        context["age"] = 30
        
        # Determine weather based on temperature (for consistency)
        if temp < 0:
            context["weather"] = "snowy"
        elif temp < 10:
            context["weather"] = "cold"
        elif temp < 20:
            context["weather"] = "cool"
        elif temp < 30:
            context["weather"] = "warm"
        else:
            context["weather"] = "hot"
        
        # Get recommendations
        recs = engine.get_recommendations(test_user, n=10, context_data=context)
        print_recommendations(recs, itemid_to_title, itemid_to_genres, context)
        
        # Analyze genre distribution
        genre_counts = analyze_genres(recs, itemid_to_genres)
        temp_genre_data[temp] = genre_counts
        
        # Compare to baseline
        baseline_ids = [item_id for item_id, _ in baseline_recs]
        temp_ids = [item_id for item_id, _ in recs]
        
        different_items = sum(1 for item in temp_ids if item not in baseline_ids)
        print(f"Impact Analysis: {different_items} of 10 recommendations are different due to temperature being {temp}°C")
        
        # Print top genres that changed
        print("Genres that increased in prominence:")
        for genre, count in genre_counts.items():
            baseline_count = baseline_genres.get(genre, 0)
            if count > baseline_count:
                print(f"  {genre}: +{count - baseline_count}")
    
    # Test combined time and temperature
    print_header("COMBINED TIME AND TEMPERATURE TEST")
    
    # Define interesting combinations
    combinations = [
        {"name": "Hot Summer Afternoon", "time": "afternoon", "temp": 35, "weather": "hot"},
        {"name": "Cold Winter Morning", "time": "morning", "temp": -5, "weather": "snowy"},
        {"name": "Cool Spring Evening", "time": "evening", "temp": 15, "weather": "cool"},
        {"name": "Warm Fall Night", "time": "night", "temp": 22, "weather": "warm"},
        {"name": "Rainy Late Night", "time": "late_night", "temp": 10, "weather": "rainy"}
    ]
    
    for combo in combinations:
        print(f"\nSCENARIO: {combo['name'].upper()}")
        
        # Create context with this combination
        context = copy.deepcopy(base_context)
        context["time_of_day"] = combo["time"]
        context["temperature"] = combo["temp"]
        context["weather"] = combo["weather"]
        context["mood"] = "neutral"  # Keep other factors neutral
        context["age"] = 30
        
        # Get recommendations
        recs = engine.get_recommendations(test_user, n=10, context_data=context)
        print_recommendations(recs, itemid_to_title, itemid_to_genres, context)
        
        # Analyze genre distribution
        genre_counts = analyze_genres(recs, itemid_to_genres)
        
        # Compare to baseline
        baseline_ids = [item_id for item_id, _ in baseline_recs]
        combo_ids = [item_id for item_id, _ in recs]
        
        different_items = sum(1 for item in combo_ids if item not in baseline_ids)
        print(f"Impact Analysis: {different_items} of 10 recommendations are different due to this scenario")
        
        # Print top genres that changed
        print("Genres that increased in prominence:")
        for genre, count in genre_counts.items():
            baseline_count = baseline_genres.get(genre, 0)
            if count > baseline_count:
                print(f"  {genre}: +{count - baseline_count}")

if __name__ == "__main__":
    test_time_and_temperature() 