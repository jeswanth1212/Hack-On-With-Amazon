import pandas as pd
import numpy as np
from src.models.train_models import load_data, train_models
from src.utils.context_utils import get_current_context

def test_recommendation_system():
    print("Loading data and training models...")
    movies_df, users_df, interactions_df = load_data()
    engine = train_models(movies_df, users_df, interactions_df)

    # Build a mapping from item_id to title and genres
    itemid_to_title = dict(zip(movies_df['item_id'], movies_df['title']))
    itemid_to_genres = {}
    if 'genres' in movies_df.columns:
        itemid_to_genres = dict(zip(movies_df['item_id'], movies_df['genres']))

    # Get real context data (current time, day, weather)
    real_context = get_current_context()
    
    # Print detailed context information
    print(f"\n{'=' * 50}")
    print("CURRENT CONTEXT DATA:")
    print(f"{'=' * 50}")
    print(f"Time of day: {real_context['time_of_day']}")
    print(f"Day of week: {real_context['day_of_week']}")
    print(f"Weather: {real_context['weather']}")
    if 'temperature' in real_context:
        print(f"Temperature: {real_context['temperature']}°C")
    
    # Add a mood (this would typically come from user input)
    real_context['mood'] = 'sad'
    real_context['age'] = 20
    print(f"Mood: {real_context['mood']} (manually set)")
    print(f"Age: {real_context['age']} (manually set)")
    print(f"{'=' * 50}\n")

    test_users = users_df['user_id'].tolist()[:3]
    for user_id in test_users:
        print(f"\n{'=' * 50}")
        print(f"USER {user_id} RECOMMENDATIONS")
        print(f"{'=' * 50}")
        
        # Get recommendations without context
        print(f"\nTOP 5 RECOMMENDATIONS WITHOUT CONTEXT:")
        recommendations = engine.get_recommendations(user_id, n=5)
        for i, (item_id, score) in enumerate(recommendations):
            title = itemid_to_title.get(item_id, 'Unknown')
            genres = itemid_to_genres.get(item_id, '')
            print(f"  {i+1}. {title} (ID: {item_id}) - Score: {score:.4f}")
            print(f"     Genres: {genres}")

        # Get recommendations with context
        print(f"\nTOP 5 RECOMMENDATIONS WITH CONTEXT:")
        print(f"  [Mood: {real_context['mood']}, Time: {real_context['time_of_day']}, Weather: {real_context['weather']}, Age: {real_context['age']}]")
        recommendations_with_context = engine.get_recommendations(user_id, n=5, context_data=real_context)
        
        # Check if context changed the recommendations
        context_changed = set([item_id for item_id, _ in recommendations]) != set([item_id for item_id, _ in recommendations_with_context])
        if context_changed:
            print("  * Context had a significant impact on recommendations!")
        
        for i, (item_id, score) in enumerate(recommendations_with_context):
            title = itemid_to_title.get(item_id, 'Unknown')
            genres = itemid_to_genres.get(item_id, '')
            print(f"  {i+1}. {title} (ID: {item_id}) - Score: {score:.4f}")
            print(f"     Genres: {genres}")

        # Simulate the user watching the top recommended movie
        if recommendations_with_context:
            watched_item_id = recommendations_with_context[0][0]
            watched_title = itemid_to_title.get(watched_item_id, 'Unknown')
            watched_genres = itemid_to_genres.get(watched_item_id, '')
            
            print(f"\nUSER {user_id} WATCHES: {watched_title}")
            print(f"Genres: {watched_genres}")
            
            engine.record_interaction(user_id, watched_item_id, sentiment_score=1.0, context_data=real_context)

            # Get new recommendations after the interaction
            print(f"\nTOP 5 RECOMMENDATIONS AFTER WATCHING {watched_title}:")
            new_recommendations = engine.get_recommendations(user_id, n=5, context_data=real_context)
            
            # Compare with previous recommendations
            removed_items = set([item_id for item_id, _ in recommendations_with_context]) - set([item_id for item_id, _ in new_recommendations])
            new_items = set([item_id for item_id, _ in new_recommendations]) - set([item_id for item_id, _ in recommendations_with_context])
            
            if watched_item_id in [item_id for item_id, _ in new_recommendations]:
                print(f"  WARNING: {watched_title} is still in recommendations after being watched")
            else:
                print(f"  SUCCESS: {watched_title} was removed from recommendations")
                
            print(f"  Items removed: {len(removed_items)}, Items added: {len(new_items)}")
            
            for i, (item_id, score) in enumerate(new_recommendations):
                title = itemid_to_title.get(item_id, 'Unknown')
                genres = itemid_to_genres.get(item_id, '')
                
                # Check if this is a new recommendation
                is_new = item_id in new_items
                print(f"  {i+1}. {title} (ID: {item_id}) - Score: {score:.4f} {'[NEW]' if is_new else ''}")
                print(f"     Genres: {genres}")

if __name__ == "__main__":
    test_recommendation_system() 