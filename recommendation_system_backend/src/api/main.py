import sys
import os
import logging
import pandas as pd
import uvicorn
import datetime
from queue import Queue
from threading import Thread
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
import traceback

# Add the project root to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# Import from other modules
from src.models.model import RecommendationEngine
from src.database.database import (
    init_db, setup_database, add_user, add_interaction, get_user_interactions, 
    get_db_connection, get_item_details, get_all_users, get_all_items, get_all_interactions
)
from src.utils.context_utils import (
    get_current_time_of_day, get_current_day_of_week,
    simulate_weather, simulate_mood, get_age_group
)

# Configuration
USE_ONLY_TMDB_DATA = True

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Local Recommendation System",
    description="A locally-run recommendation system for movies and TV shows",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a queue for processing interactions
interaction_queue = Queue()

# Initialize recommendation engine
engine = RecommendationEngine()

# Pydantic models for API
class InteractionCreate(BaseModel):
    user_id: str
    item_id: str
    sentiment_score: float = Field(0.5, ge=0.0, le=1.0)
    mood: Optional[str] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    weather: Optional[str] = None
    location: Optional[str] = None
    event_type: str = "watch"

class InteractionResponse(BaseModel):
    interaction_id: int
    user_id: str
    item_id: str
    timestamp: str
    sentiment_score: float
    mood: Optional[str] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    weather: Optional[str] = None
    location: Optional[str] = None
    event_type: str

class RecommendationResponse(BaseModel):
    item_id: str
    title: str
    score: float
    genres: Optional[str] = None
    release_year: Optional[int] = None
    overview: Optional[str] = None

class ContextData(BaseModel):
    mood: Optional[str] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    weather: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    language: Optional[str] = None

class UserProfileCreate(BaseModel):
    user_id: str
    age: Optional[int] = None
    location: Optional[str] = None
    language_preference: Optional[str] = None
    preferred_genres: Optional[List[str]] = None

class UserProfileResponse(BaseModel):
    user_id: str
    age: Optional[int] = None
    age_group: Optional[str] = None
    location: Optional[str] = None
    language_preference: Optional[str] = None
    preferred_genres: Optional[List[str]] = None

# Background thread for processing interactions
def process_interactions():
    """Process interactions from the queue."""
    logger.info("Starting interaction processing thread")
    
    while True:
        try:
            # Get an interaction from the queue
            interaction = interaction_queue.get()
            
            # Add the interaction to the database
            add_interaction(
                user_id=interaction["user_id"],
                item_id=interaction["item_id"],
                sentiment_score=interaction["sentiment_score"],
                mood=interaction["mood"],
                age=interaction.get("age"),
                time_of_day=interaction["time_of_day"],
                day_of_week=interaction["day_of_week"],
                weather=interaction["weather"],
                location=interaction.get("location"),
                event_type=interaction["event_type"]
            )
            
            # Update the recommendation engine
            if engine is not None:
                context_data = {
                    "mood": interaction["mood"],
                    "time_of_day": interaction["time_of_day"],
                    "day_of_week": interaction["day_of_week"],
                    "weather": interaction["weather"],
                    "age": interaction.get("age")
                }
                
                engine.record_interaction(
                    user_id=interaction["user_id"],
                    item_id=interaction["item_id"],
                    sentiment_score=interaction["sentiment_score"],
                    context_data=context_data
                )
            
            # Mark the task as done
            interaction_queue.task_done()
        
        except Exception as e:
            logger.error(f"Error processing interaction: {e}")
            interaction_queue.task_done()

# Start the background thread
interaction_thread = Thread(target=process_interactions, daemon=True)
interaction_thread.start()

# Dependency for getting contextual data
def get_context_data(
    mood: Optional[str] = None,
    time_of_day: Optional[str] = None,
    day_of_week: Optional[str] = None,
    weather: Optional[str] = None,
    age: Optional[int] = None,
    location: Optional[str] = None,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get contextual data with default values where not provided.
    
    Args:
        mood (str, optional): User mood
        time_of_day (str, optional): Time of day
        day_of_week (str, optional): Day of week
        weather (str, optional): Weather
        age (int, optional): User age
        location (str, optional): User location
        language (str, optional): Preferred language
        
    Returns:
        dict: Contextual data
    """
    # Use provided values or defaults
    context_data = {
        "mood": mood if mood else simulate_mood(),
        "time_of_day": time_of_day if time_of_day else get_current_time_of_day(),
        "day_of_week": day_of_week if day_of_week else get_current_day_of_week(),
        "weather": weather if weather else simulate_weather(location),
        "age": age,
        "location": location,
        "language": language
    }
    
    # Add age_group if age is provided
    if age:
        context_data["age_group"] = get_age_group(age)
    
    return context_data

# API routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the Local Recommendation System API"}

@app.post("/interaction", response_model=Dict[str, str])
async def create_interaction(interaction: InteractionCreate):
    """
    Record a user interaction.
    
    Args:
        interaction (InteractionCreate): Interaction data
        
    Returns:
        dict: Status message
    """
    # Fill in missing contextual data
    context_data = get_context_data(
        mood=interaction.mood,
        time_of_day=interaction.time_of_day,
        day_of_week=interaction.day_of_week,
        weather=interaction.weather,
        location=interaction.location
    )
    
    # Add the interaction to the queue
    interaction_data = interaction.dict()
    interaction_data.update({
        "mood": context_data["mood"],
        "time_of_day": context_data["time_of_day"],
        "day_of_week": context_data["day_of_week"],
        "weather": context_data["weather"]
    })
    
    interaction_queue.put(interaction_data)
    
    return {"status": "success", "message": "Interaction recorded"}

@app.get("/recommend", response_model=List[RecommendationResponse])
async def get_recommendations(
    user_id: str = Query(..., description="User ID"),
    n: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    context: ContextData = Depends(get_context_data),
    include_local_language: bool = Query(True, description="Whether to include local language recommendations")
):
    """
    Get recommendations for a user.
    
    Args:
        user_id (str): User ID
        n (int): Number of recommendations
        context (ContextData): Contextual data
        include_local_language (bool): Whether to include local language recommendations
        
    Returns:
        List[RecommendationResponse]: List of recommendations
    """
    # Check if engine is loaded
    if engine is None:
        raise HTTPException(status_code=503, detail="Recommendation engine not loaded")
    
    # Get user profile data including preferred genres
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM UserProfiles WHERE user_id = ?', (user_id,))
    user_profile = cursor.fetchone()
    conn.close()
    
    # Initialise variable to avoid UnboundLocalError later
    preferred_genres = None
    
    # If user profile exists, add data to context
    if user_profile:
        # Handle context as either dict or object
        if isinstance(context, dict):
            if user_profile['age'] and not context.get('age'):
                context['age'] = user_profile['age']
                
            if user_profile['language_preference'] and not context.get('language'):
                context['language'] = user_profile['language_preference']
                
            if user_profile['location'] and not context.get('location'):
                context['location'] = user_profile['location']
        else:
            if user_profile['age'] and not context.age:
                context.age = user_profile['age']
                
            if user_profile['language_preference'] and not context.language:
                context.language = user_profile['language_preference']
                
            if user_profile['location'] and not context.location:
                context.location = user_profile['location']
            
            # Get preferred genres if available
            if user_profile['preferred_genres']:
                # Convert from pipe-separated string to list
                preferred_genres = user_profile['preferred_genres'].split('|')
                logger.info(f"Using user's preferred genres: {preferred_genres}")
    
    # Get base recommendations
    recommendations = engine.get_recommendations(
        user_id=user_id,
        n=n,
        context_data=context,
        exclude_items=None
    )
    
    # Prepare response
    response = []
    
    # Map to store item IDs that have been included in response
    included_item_ids = set()
    
    # Process standard recommendations
    for item_id, score in recommendations:
        # Get item details
        item_details = get_item_details(item_id)
        
        if item_details:
            # Boost score for items matching user's preferred genres
            boost_factor = 1.0
            if preferred_genres and item_details.get("genres"):
                item_genres = item_details["genres"].lower().split("|")
                matches = [g for g in preferred_genres if g.lower() in item_genres or 
                          any(g.lower() in genre.lower() for genre in item_genres)]
                if matches:
                    # Add a boost based on number of matching genres
                    boost_factor = 1.0 + (0.1 * len(matches))
                    logger.info(f"Boosting item {item_id} by factor {boost_factor} due to genre match")
            
            response.append(
                RecommendationResponse(
                    item_id=item_id,
                    title=item_details["title"],
                    score=float(score * boost_factor),
                    genres=item_details.get("genres"),
                    release_year=item_details.get("release_year"),
                    overview=item_details.get("overview")
                )
            )
            included_item_ids.add(item_id)
    
    # If we should include local language recommendations and location is provided
    # Check if context is a dict or a Pydantic model
    context_location = context.get('location') if isinstance(context, dict) else context.location
    
    if include_local_language and context_location:
        # Determine language based on location (simplified mapping)
        local_language = None
        
        # Map some Indian cities to languages
        location = context_location.lower() if context_location else ""
        
        if any(city in location for city in ["mumbai", "pune"]):
            local_language = "hi"  # Hindi (could also be Marathi)
        elif any(city in location for city in ["delhi", "lucknow", "jaipur"]):
            local_language = "hi"  # Hindi
        elif any(city in location for city in ["chennai", "coimbatore"]):
            local_language = "ta"  # Tamil
        elif any(city in location for city in ["hyderabad"]):
            local_language = "te"  # Telugu
        elif any(city in location for city in ["bangalore", "bengaluru"]):
            local_language = "kn"  # Kannada
        elif any(city in location for city in ["kochi", "thiruvananthapuram", "kerala"]):
            local_language = "ml"  # Malayalam
        elif any(city in location for city in ["kolkata", "patna"]):
            local_language = "bn"  # Bengali
        elif any(city in location for city in ["ahmedabad", "surat"]):
            local_language = "gu"  # Gujarati
        
        # If language determined or explicitly provided in context, find local language movies
        context_language = context.get('language') if isinstance(context, dict) else context.language
        target_language = context_language or local_language
        
        if target_language:
            # Get local language movies (5 movies)
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get popular movies in target language that user hasn't seen
            cursor.execute('''
            SELECT i.* FROM Items i
            WHERE i.language = ? AND i.item_id NOT IN (
                SELECT item_id FROM Interactions WHERE user_id = ?
            )
            ORDER BY i.popularity DESC, i.vote_average DESC
            LIMIT 5
            ''', (target_language, user_id))
            
            local_movies = cursor.fetchall()
            conn.close()
            
            # Add these movies to the recommendations with a boosted score
            for movie in local_movies:
                item_id = movie['item_id']
                
                # Skip if already included
                if item_id in included_item_ids:
                    continue
                
                # Add to response with a somewhat high score
                response.append(
                    RecommendationResponse(
                        item_id=item_id,
                        title=movie["title"],
                        score=0.85,  # Give local language movies a high score
                        genres=movie.get("genres"),
                        release_year=movie.get("release_year"),
                        overview=movie.get("overview")
                    )
                )
                included_item_ids.add(item_id)
    
    # Sort by score (highest first)
    response.sort(key=lambda x: x.score, reverse=True)
    
    # Limit to requested number
    return response[:n]

@app.get("/user/{user_id}/history", response_model=List[Dict[str, Any]])
async def get_user_history(
    user_id: str,
    limit: int = Query(10, ge=1, le=100, description="Number of interactions to return")
):
    """
    Get interaction history for a user.
    
    Args:
        user_id (str): User ID
        limit (int): Number of interactions to return
        
    Returns:
        List[Dict[str, Any]]: List of interactions
    """
    # Get user interactions
    interactions = get_user_interactions(user_id, limit)
    
    return interactions

@app.post("/user", response_model=UserProfileResponse)
async def create_user_profile(user_profile: UserProfileCreate):
    """
    Create or update a user profile.
    
    Args:
        user_profile (UserProfileCreate): User profile data
        
    Returns:
        UserProfileResponse: Created user profile
    """
    # Calculate age_group if age is provided
    age_group = None
    if user_profile.age:
        age_group = get_age_group(user_profile.age)
    
    # Add user to database
    add_user(
        user_id=user_profile.user_id,
        age=user_profile.age,
        age_group=age_group,
        location=user_profile.location,
        language_preference=user_profile.language_preference,
        preferred_genres=user_profile.preferred_genres
    )
    
    # Initialize user in the recommendation engine
    if engine is not None:
        # Add user to recommendation engine with a default context
        # This helps the engine recognize this as a valid user
        context_data = {
            "age": user_profile.age,
            "location": user_profile.location,
            "language": user_profile.language_preference
        }
        
        if user_profile.age:
            context_data["age_group"] = age_group
        
        # For new users with no interactions, we add them to the engine
        # so they can start receiving recommendations
        
        # Add the preferred genres to the context data for initial recommendations
        if user_profile.preferred_genres:
            context_data["preferred_genres"] = user_profile.preferred_genres
            
        engine.record_interaction(
            user_id=user_profile.user_id,
            item_id="initialization",  # Special marker for user initialization
            sentiment_score=0.0,  # Neutral score
            context_data=context_data
        )
    
    # Return response
    return UserProfileResponse(
        user_id=user_profile.user_id,
        age=user_profile.age,
        age_group=age_group,
        location=user_profile.location,
        language_preference=user_profile.language_preference,
        preferred_genres=user_profile.preferred_genres
    )

@app.get("/options", response_model=Dict[str, List[Dict[str, str]]])
async def get_selection_options():
    """
    Get available options for user registration (genres and languages).
    
    Returns:
        Dict[str, List[Dict[str, str]]]: Available genres and languages
    """
    # Define common genres
    genres = [
        {"id": "action", "name": "Action"},
        {"id": "adventure", "name": "Adventure"},
        {"id": "animation", "name": "Animation"},
        {"id": "comedy", "name": "Comedy"},
        {"id": "crime", "name": "Crime"},
        {"id": "documentary", "name": "Documentary"},
        {"id": "drama", "name": "Drama"},
        {"id": "family", "name": "Family"},
        {"id": "fantasy", "name": "Fantasy"},
        {"id": "history", "name": "History"},
        {"id": "horror", "name": "Horror"},
        {"id": "music", "name": "Music"},
        {"id": "mystery", "name": "Mystery"},
        {"id": "romance", "name": "Romance"},
        {"id": "science_fiction", "name": "Science Fiction"},
        {"id": "thriller", "name": "Thriller"},
        {"id": "war", "name": "War"},
        {"id": "western", "name": "Western"}
    ]
    
    # Define languages (focusing on Indian languages)
    languages = [
        {"id": "hi", "name": "Hindi"},
        {"id": "ta", "name": "Tamil"},
        {"id": "te", "name": "Telugu"},
        {"id": "ml", "name": "Malayalam"},
        {"id": "kn", "name": "Kannada"},
        {"id": "bn", "name": "Bengali"},
        {"id": "mr", "name": "Marathi"},
        {"id": "pa", "name": "Punjabi"},
        {"id": "gu", "name": "Gujarati"},
        {"id": "or", "name": "Odia"},
        {"id": "as", "name": "Assamese"},
        {"id": "en", "name": "English"},
        {"id": "ja", "name": "Japanese"},
        {"id": "ko", "name": "Korean"},
        {"id": "zh", "name": "Chinese"},
        {"id": "fr", "name": "French"},
        {"id": "es", "name": "Spanish"},
        {"id": "de", "name": "German"}
    ]
    
    return {
        "genres": genres,
        "languages": languages
    }

@app.get("/user/{user_id}", response_model=UserProfileResponse, tags=["User"])
async def get_user_profile(user_id: str):
    """Fetch a single user profile from the database.

    Args:
        user_id (str): The user ID to look up.

    Returns:
        UserProfileResponse: The user profile data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM UserProfiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert pipe-separated genres back to list
    preferred_genres = None
    if row["preferred_genres"]:
        preferred_genres = row["preferred_genres"].split("|")

    return UserProfileResponse(
        user_id=row["user_id"],
        age=row["age"],
        age_group=row["age_group"],
        location=row["location"],
        language_preference=row["language_preference"],
        preferred_genres=preferred_genres,
    )

@app.on_event("startup")
async def startup_event():
    """Run when the API server starts up."""
    global engine
    
    logger.info("Starting API server...")
    
    # Initialize database and load data
    try:
        setup_database()
        logger.info("Database initialized and data loaded successfully")
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        # Continue anyway, might fail with database errors

    # Load recommendation engine
    try:
        engine_loaded = engine.load_models()
        
        if not engine_loaded:
            logger.warning("Failed to load recommendation engine models")
            # Continue anyway, but with default models
    except Exception as e:
        logger.error(f"Error loading recommendation engine: {e}")
        # Continue with default models

@app.on_event("shutdown")
async def shutdown_event():
    """Run when the API server shuts down."""
    logger.info("Shutting down API server...")
    
    # Save recommendation engine
    if engine is not None:
        try:
            engine.save_models()
            logger.info("Recommendation engine models saved")
        except Exception as e:
            logger.error(f"Error saving recommendation engine models: {e}")

def start():
    """Start the API server."""
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8080, reload=True)

if __name__ == "__main__":
    start() 