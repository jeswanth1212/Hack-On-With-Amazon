"""
Simple API server that returns mock recommendations
"""
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

# Create the FastAPI app
app = FastAPI(
    title="Simple Recommendation API",
    description="A simple API to test recommendation functionality"
)

# Define the recommendation response model
class Recommendation(BaseModel):
    item_id: str
    title: str
    score: float
    genres: Optional[str] = None
    release_year: Optional[int] = None
    overview: Optional[str] = None

# Sample data
SAMPLE_MOVIES = [
    {
        "item_id": "ml_1",
        "title": "Toy Story",
        "score": 0.95,
        "genres": "Animation|Children|Comedy",
        "release_year": 1995,
        "overview": "A story of toys that come to life when humans aren't looking."
    },
    {
        "item_id": "ml_2",
        "title": "Jumanji",
        "score": 0.88,
        "genres": "Adventure|Children|Fantasy",
        "release_year": 1995,
        "overview": "When two kids find and play a magical board game, they release a man who's been trapped for decades."
    },
    {
        "item_id": "ml_3",
        "title": "Grumpier Old Men",
        "score": 0.82,
        "genres": "Comedy|Romance",
        "release_year": 1995,
        "overview": "The neighborhood curmudgeons compete for the affections of an attractive new neighbor."
    },
    {
        "item_id": "ml_4",
        "title": "Waiting to Exhale",
        "score": 0.78,
        "genres": "Drama|Romance",
        "release_year": 1995,
        "overview": "Four African-American women deal with issues of life, love, and men."
    },
    {
        "item_id": "ml_5",
        "title": "Father of the Bride Part II",
        "score": 0.76,
        "genres": "Comedy",
        "release_year": 1995,
        "overview": "George Banks must deal with both his daughter and his wife being pregnant at the same time."
    },
]

@app.get("/")
async def read_root():
    """Root endpoint."""
    return {"message": "Welcome to the Simple Recommendation API"}

@app.get("/recommend", response_model=List[Recommendation])
async def recommend(user_id: str, n: int = 5):
    """
    Get recommendations for a user.
    
    Args:
        user_id (str): User ID
        n (int): Number of recommendations
        
    Returns:
        List[Recommendation]: List of recommendations
    """
    # Return a list of sample recommendations
    return SAMPLE_MOVIES[:min(n, len(SAMPLE_MOVIES))]

def start():
    """Start the API server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start() 