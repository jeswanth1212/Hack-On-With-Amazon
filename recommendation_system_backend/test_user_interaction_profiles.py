import pandas as pd
import numpy as np
import copy
from tabulate import tabulate
from collections import Counter, defaultdict

from src.models.train_models import load_data, train_models
from src.utils.context_utils import get_current_context
from src.models.model import RecommendationEngine

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

def create_genre_profile(movies_df, genres, n=5):
    """Create a list of movies that match the given genres."""
    matching_movies = []
    
    for _, movie in movies_df.iterrows():
        movie_genres = str(movie.get('genres', '')).split('|')
        if any(genre in movie_genres for genre in genres):
            matching_movies.append(movie)
    
    # If we found enough movies
    if len(matching_movies) >= n:
        return matching_movies[:n]
    
    # If not enough movies match the genres, add random movies
    remaining = n - len(matching_movies)
    random_movies = movies_df.sample(remaining)
    return matching_movies + random_movies.to_dict('records')

def test_user_interaction_profiles():
    """Test how different user interaction histories affect recommendations."""
    print_header("LOADING DATA AND TRAINING MODELS")
    movies_df, users_df, interactions_df = load_data()
    
    # Build a mapping from item_id to title and genres
    itemid_to_title = dict(zip(movies_df['item_id'], movies_df['title']))
    itemid_to_genres = {}
    if 'genres' in movies_df.columns:
        itemid_to_genres = dict(zip(movies_df['item_id'], movies_df['genres']))
    
    # Get current context as base
    base_context = get_current_context()
    print(f"Base context: {base_context}")
    
    # Define different user interaction profiles
    user_profiles = [
        {
            "name": "Action Fan",
            "genres": ["Action", "Adventure", "Thriller"],
            "description": "User who mostly watches action and adventure movies"
        },
        {
            "name": "Comedy Lover",
            "genres": ["Comedy", "Romance"],
            "description": "User who mostly watches comedies and romantic comedies"
        },
        {
            "name": "Drama Enthusiast",
            "genres": ["Drama", "Crime"],
            "description": "User who mostly watches dramas and crime movies"
        },
        {
            "name": "Sci-Fi Geek",
            "genres": ["Sci-Fi", "Fantasy"],
            "description": "User who mostly watches science fiction and fantasy"
        },
        {
            "name": "Family Viewer",
            "genres": ["Family", "Animation", "Children"],
            "description": "User who mostly watches family-friendly and animated films"
        }
    ]
    
    # We'll simulate each profile by creating a new recommendation engine
    # and training it with interactions based on the profile
    profile_recommendations = {}
    
    for profile in user_profiles:
        print_header(f"SIMULATING USER PROFILE: {profile['name']}")
        print(f"Description: {profile['description']}")
        print(f"Preferred Genres: {', '.join(profile['genres'])}")
        
        # Create a new engine for this profile
        engine = RecommendationEngine()
        
        # Create a fake user ID for this profile
        user_id = f"test_{profile['name'].lower().replace(' ', '_')}"
        
        # Create interactions for this profile by finding movies of the preferred genres
        profile_movies = create_genre_profile(movies_df, profile['genres'], n=10)
        
        print(f"\nCreating interaction history with {len(profile_movies)} movies:")
        history_table = []
        
        # Record interactions for this profile
        for i, movie in enumerate(profile_movies):
            item_id = movie['item_id']
            title = movie['title']
            genres = movie.get('genres', '')
            
            # Higher sentiment score for movies that match preferred genres
            movie_genres = str(genres).split('|')
            matching_genres = sum(1 for g in profile['genres'] if g in movie_genres)
            sentiment_score = min(1.0, 0.6 + (matching_genres * 0.1))
            
            # Record the interaction
            context_data = copy.deepcopy(base_context)
            context_data['mood'] = np.random.choice(['happy', 'excited', 'relaxed'])
            
            engine.record_interaction(
                user_id=user_id,
                item_id=item_id,
                sentiment_score=sentiment_score,
                context_data=context_data
            )
            
            history_table.append([i+1, title, item_id, f"{sentiment_score:.2f}", genres])
        
        # Print the interaction history
        print(tabulate(history_table, 
                      headers=["#", "Title", "ID", "Score", "Genres"], 
                      tablefmt="grid"))
        
        # Get recommendations for this profile
        recommendations = engine.get_recommendations(user_id, n=10)
        profile_recommendations[profile['name']] = recommendations
        
        print(f"\nRecommendations for {profile['name']}:")
        print_recommendations(recommendations, itemid_to_title, itemid_to_genres)
        
        # Analyze genre distribution in recommendations
        genre_counts = defaultdict(int)
        for item_id, _ in recommendations:
            genres = itemid_to_genres.get(item_id, '').split('|')
            for genre in genres:
                if genre and genre not in ['', 'NULL', None]:
                    genre_counts[genre] += 1
        
        # Sort genres by count
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate the percentage of recommended movies with preferred genres
        preferred_count = sum(count for genre, count in sorted_genres 
                             if genre in profile['genres'])
        total_genres = sum(count for _, count in sorted_genres)
        
        preferred_percentage = (preferred_count / total_genres) * 100 if total_genres else 0
        
        print(f"Top genres in recommendations:")
        genre_table = []
        for genre, count in sorted_genres[:10]:  # Top 10 genres
            is_preferred = "Yes" if genre in profile['genres'] else "No"
            percentage = (count / total_genres) * 100
            genre_table.append([genre, count, f"{percentage:.1f}%", is_preferred])
        
        print(tabulate(genre_table, 
                      headers=["Genre", "Count", "Percentage", "Preferred?"], 
                      tablefmt="simple"))
        
        print(f"\nPercentage of recommendations matching preferred genres: {preferred_percentage:.1f}%")
    
    # Compare recommendations across different profiles
    print_header("COMPARING RECOMMENDATIONS ACROSS PROFILES")
    
    # Create a matrix of overlapping recommendations
    profile_names = [p['name'] for p in user_profiles]
    overlap_matrix = np.zeros((len(profile_names), len(profile_names)))
    
    for i, profile1 in enumerate(profile_names):
        for j, profile2 in enumerate(profile_names):
            recs1 = set(item_id for item_id, _ in profile_recommendations[profile1])
            recs2 = set(item_id for item_id, _ in profile_recommendations[profile2])
            
            # Calculate Jaccard similarity (intersection over union)
            intersection = len(recs1.intersection(recs2))
            union = len(recs1.union(recs2))
            
            similarity = intersection / union if union > 0 else 0
            overlap_matrix[i, j] = similarity
    
    # Print similarity matrix
    print("\nRecommendation Similarity Matrix (Jaccard Index):")
    headers = profile_names
    table_data = []
    
    for i, profile in enumerate(profile_names):
        row = [profile]
        for j in range(len(profile_names)):
            row.append(f"{overlap_matrix[i, j]:.2f}")
        table_data.append(row)
    
    print(tabulate(table_data, headers=["Profile"] + headers, tablefmt="grid"))
    
    # Find the most unique and most generic profiles
    row_means = np.mean(overlap_matrix, axis=1)
    most_unique_idx = np.argmin(row_means)
    most_generic_idx = np.argmax(row_means)
    
    print(f"\nMost unique profile: {profile_names[most_unique_idx]} (avg. similarity: {row_means[most_unique_idx]:.2f})")
    print(f"Most generic profile: {profile_names[most_generic_idx]} (avg. similarity: {row_means[most_generic_idx]:.2f})")

if __name__ == "__main__":
    test_user_interaction_profiles() 