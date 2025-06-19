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

# Add the project root to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.models.model import RecommendationEngine
from src.data.database import (
    add_interaction, get_user_interactions, get_item_details,
    add_user, get_db_connection, init_db, setup_database
)
from src.utils.context_utils import (
    get_current_time_of_day, get_current_day_of_week,
    simulate_weather, simulate_mood, get_age_group
)

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
    allow_origins=["*"],
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
    location: Optional[str] = None
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
        "location": location
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
    context: ContextData = Depends(get_context_data)
):
    """
    Get recommendations for a user.
    
    Args:
        user_id (str): User ID
        n (int): Number of recommendations
        context (ContextData): Contextual data
        
    Returns:
        List[RecommendationResponse]: List of recommendations
    """
    # Check if engine is loaded
    if engine is None:
        raise HTTPException(status_code=503, detail="Recommendation engine not loaded")
    
    # Get recommendations
    recommendations = engine.get_recommendations(
        user_id=user_id,
        n=n,
        context_data=context,
        exclude_items=None
    )
    
    # Prepare response
    response = []
    for item_id, score in recommendations:
        # Get item details
        item_details = get_item_details(item_id)
        
        if item_details:
            response.append(
                RecommendationResponse(
                    item_id=item_id,
                    title=item_details["title"],
                    score=float(score),
                    genres=item_details.get("genres"),
                    release_year=item_details.get("release_year"),
                    overview=item_details.get("overview")
                )
            )
    
    return response

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
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start() 