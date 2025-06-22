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
import json
import random
import socketio
import asyncio

# Add the project root to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# Import from other modules
from src.models.model import RecommendationEngine
from src.database.database import (
    init_db, setup_database, add_user, add_interaction, get_user_interactions, 
    get_db_connection, get_item_details, get_all_users, get_all_items, get_all_interactions,
    search_users, send_friend_request, respond_to_friend_request, 
    get_pending_friend_requests, get_friends, get_friend_activities,
    create_watch_party, get_watch_party_invites, accept_watch_party, get_watch_party_details,
    end_watch_party
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

# Define CORS allowed origins
allowed_origins = ["http://localhost:3000", "http://localhost", "http://127.0.0.1:3000", "*"]  # Explicitly allow the frontend origin

# Add CORS middleware to FastAPI - make sure it's before mounting the socket_app
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO server with proper CORS settings
sio = socketio.AsyncServer(
    async_mode='asgi', 
    cors_allowed_origins=allowed_origins,
    logger=True,
    engineio_logger=True,
    ping_timeout=60,  # Increase ping timeout
    ping_interval=25,  # Reduce ping interval
    max_http_buffer_size=1e8  # Increase buffer size for larger packets
)

# Create a Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, socketio_path='socket.io')

# Mount the Socket.IO app at a specific path instead of root
app.mount("/socket.io", socket_app)

# Create a queue for processing interactions
interaction_queue = Queue()

# Initialize recommendation engine with strengthened contextual factor weights
engine = RecommendationEngine(cf_weight=0.6, cb_weight=0.4, context_alpha=0.5)

# Dictionary to track active watch parties and their participants
active_watch_parties = {}

# Socket.IO events
@sio.event
async def connect(sid, environ, auth):
    logger.info(f"Client connected: {sid}")
    logger.info(f"Connection environ: {environ.get('HTTP_ORIGIN', 'unknown')} - Headers: {environ.get('HTTP_SEC_WEBSOCKET_KEY', 'unknown')}")
    return True

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
    # Remove user from any watch parties they were in
    for party_id in list(active_watch_parties.keys()):
        found_participant = None
        for participant in active_watch_parties[party_id]['participants']:
            if isinstance(participant, dict) and participant.get('sid') == sid:
                found_participant = participant
                break
                
        if found_participant:
            # Remove participant from the party
            active_watch_parties[party_id]['participants'].remove(found_participant)
            logger.info(f"Removed participant {found_participant.get('user_id')} with sid {sid} from party {party_id}")
            
            # Notify other participants that this user has left
            await sio.emit('participant_left', {'sid': sid, 'user_id': found_participant.get('user_id')}, 
                          room=f"party_{party_id}")
            
            # If party is now empty, clean it up
            if not active_watch_parties[party_id]['participants']:
                logger.info(f"Party {party_id} is now empty, removing it")
                del active_watch_parties[party_id]

@sio.event
async def join_watch_party(sid, data):
    logger.info(f"Join watch party request from {sid}: {data}")
    party_id = data.get('party_id')
    user_id = data.get('user_id')
    username = data.get('username', user_id)
    
    if not party_id:
        logger.error(f"Join request missing party_id: {data}")
        return {'success': False, 'error': 'Party ID is required'}
    
    # Create party room if it doesn't exist yet
    room_name = f"party_{party_id}"
    if party_id not in active_watch_parties:
        active_watch_parties[party_id] = {
            'participants': [],
            'video_state': {
                'playing': False,
                'currentTime': 0,
                'tmdbId': data.get('tmdbId')
            }
        }
        logger.info(f"Created new watch party: {party_id}")
    
    # Check if user is already in the party
    for participant in active_watch_parties[party_id]['participants']:
        if isinstance(participant, dict) and participant.get('user_id') == user_id:
            # Update the SID if user reconnected
            logger.info(f"User {user_id} reconnected with new SID {sid}")
            participant['sid'] = sid
            await sio.enter_room(sid, room_name)
            return {
                'success': True,
                'participants': active_watch_parties[party_id]['participants'],
                'video_state': active_watch_parties[party_id]['video_state']
            }
    
    # Add user to party room
    logger.info(f"User {username} ({user_id}) joined party {party_id} with SID {sid}")
    await sio.enter_room(sid, room_name)
    
    # Create participant record
    participant = {
        'sid': sid,
        'user_id': user_id,
        'username': username
    }
    
    active_watch_parties[party_id]['participants'].append(participant)
    
    # Notify others in room that user has joined
    logger.info(f"Broadcasting new participant to room {room_name}")
    await sio.emit('participant_joined', participant, room=room_name, skip_sid=sid)
    
    # Send current participants to the joining user
    return {
        'success': True,
        'participants': active_watch_parties[party_id]['participants'],
        'video_state': active_watch_parties[party_id]['video_state']
    }

@sio.event
async def leave_watch_party(sid, data):
    logger.info(f"Leave watch party request: {data}")
    party_id = data.get('party_id')
    user_id = data.get('user_id')
    
    if not party_id or party_id not in active_watch_parties:
        logger.error(f"Invalid party ID in leave request: {party_id}")
        return {'success': False, 'error': 'Invalid party ID'}
        
    room_name = f"party_{party_id}"
    
    # Find and remove user from participants list
    participants = active_watch_parties[party_id]['participants']
    for i, participant in enumerate(participants):
        if participant['sid'] == sid:
            removed_participant = participants.pop(i)
            break
    
    # Notify others that user has left
    await sio.emit('participant_left', {
        'user_id': user_id
    }, room=room_name)
    
    # Leave the room
    await sio.leave_room(sid, room_name)
    
    # If party is now empty, clean it up
    if not active_watch_parties[party_id]['participants']:
        del active_watch_parties[party_id]
        
    return {'success': True}

@sio.event
async def video_state_change(sid, data):
    logger.info(f"Video state change from {sid}: {data}")
    party_id = data.get('party_id')
    state = data.get('state', {})
    
    if not party_id or party_id not in active_watch_parties:
        logger.error(f"Invalid party ID in video state change: {party_id}")
        return {'success': False, 'error': 'Invalid party ID'}
        
    # Update stored state
    active_watch_parties[party_id]['video_state'].update(state)
    
    # Broadcast to other participants
    room_name = f"party_{party_id}"
    await sio.emit('video_state_updated', {
        'state': state
    }, room=room_name, skip_sid=sid)
    
    return {'success': True}

@sio.event
async def send_signal(sid, data):
    party_id = data.get('party_id')
    target_sid = data.get('target_sid')
    signal_data = data.get('signal')
    
    logger.info(f"Signal from {sid} to {target_sid} in party {party_id}")
    
    if not party_id or party_id not in active_watch_parties:
        logger.error(f"Invalid party ID in signal: {party_id}")
        return {'success': False, 'error': 'Invalid party ID'}
    
    # Ensure target user is in the party
    participant_exists = False
    for participant in active_watch_parties[party_id]['participants']:
        if isinstance(participant, dict) and participant.get('sid') == target_sid:
            participant_exists = True
            break
    
    if not participant_exists:
        logger.warning(f"Target user {target_sid} not in party {party_id}")
        return {'success': False, 'error': 'Target user not in this party'}
    
    # Forward WebRTC signal to the target peer
    logger.info(f"Forwarding signal from {sid} to {target_sid} in party {party_id}")
    
    await sio.emit('signal_received', {
        'signal': signal_data,
        'from_sid': sid
    }, to=target_sid)
    
    return {'success': True}

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

# Friend system models
class FriendRequest(BaseModel):
    sender_id: str
    receiver_id: str

class FriendRequestResponse(BaseModel):
    request_id: int
    sender_id: str
    receiver_id: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    # Additional sender info
    age: Optional[int] = None
    location: Optional[str] = None
    language_preference: Optional[str] = None

class FriendResponse(BaseModel):
    user_id: str
    age: Optional[int] = None
    age_group: Optional[str] = None
    location: Optional[str] = None
    language_preference: Optional[str] = None
    preferred_genres: Optional[List[str]] = None
    friendship_date: str

class FriendActivityResponse(BaseModel):
    friend_id: str
    item_id: str
    title: str
    timestamp: str
    genres: Optional[str] = None
    release_year: Optional[int] = None
    sentiment_score: Optional[float] = None

class NotificationCountResponse(BaseModel):
    friend_requests: int
    friend_activities: int
    watch_parties: int = 0
    total: int

class SearchUserRequest(BaseModel):
    query: str

class FriendRequestAction(BaseModel):
    status: str

# ------------------- Watch Party models -------------------

class WatchPartyCreate(BaseModel):
    host_id: str
    tmdb_id: int
    friend_ids: List[str]

class WatchPartyInviteResponse(BaseModel):
    party_id: int
    host_id: str
    tmdb_id: int
    created_at: str

class WatchPartyDetailsResponse(BaseModel):
    party_id: int
    host_id: str
    tmdb_id: int
    status: str
    created_at: str
    participants: List[Dict[str, Any]]

# ------------------- Watch Party endpoints -------------------

@app.post('/watchparty/create', response_model=Dict[str, Any], tags=['WatchParty'])
async def api_create_watch_party(party: WatchPartyCreate):
    try:
        party_id = create_watch_party(party.host_id, party.tmdb_id, party.friend_ids)
        return {"party_id": party_id}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Failed to create party")

@app.get('/watchparty/notifications/{user_id}', response_model=List[WatchPartyInviteResponse], tags=['WatchParty'])
async def api_get_watch_party_invites(user_id: str):
    try:
        return get_watch_party_invites(user_id)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Failed to fetch invites")

@app.post('/watchparty/accept', response_model=Dict[str, str], tags=['WatchParty'])
async def api_accept_watch_party(party_id: int = Query(...), user_id: str = Query(...)):
    try:
        accept_watch_party(party_id, user_id)
        return {"status": "accepted"}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Failed to accept invite")

@app.get('/watchparty/details/{party_id}', response_model=WatchPartyDetailsResponse, tags=['WatchParty'])
async def api_get_watch_party_details(party_id: int):
    """
    Get details of a watch party including participants.
    
    Args:
        party_id (int): ID of the watch party
        
    Returns:
        WatchPartyDetailsResponse: Watch party details
    """
    logger.info(f"Fetching details for watch party ID: {party_id}")
    try:
        details = get_watch_party_details(party_id)
        if not details:
            logger.warning(f"Watch party ID {party_id} not found")
            raise HTTPException(status_code=404, detail=f"Party with ID {party_id} not found")
        logger.info(f"Successfully retrieved watch party details for ID {party_id}")
        return details
    except Exception as e:
        logger.error(f"Error retrieving watch party details for ID {party_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving watch party: {str(e)}")

@app.post('/watchparty/end', response_model=Dict[str, str], tags=['WatchParty'])
async def api_end_watch_party(party_id: int = Query(...)):
    try:
        end_watch_party(party_id)
        return {"status": "ended"}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Failed to end party")

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
    include_local_language: bool = Query(True, description="Whether to include local language recommendations"),
    language_weight: float = Query(0.95, ge=0.0, le=1.0, description="Weight for language preference"),
    ensure_language_diversity: bool = Query(True, description="Whether to ensure language diversity"),
    preferred_languages: str = Query(None, description="Comma-separated list of preferred languages"),
    _uuid: str = Query(None, description="Unique request identifier for cache busting"),
    _t: int = Query(None, description="Timestamp for cache busting")
):
    """
    Get personalized recommendations for a user.
    
    Args:
        user_id: User ID
        n: Number of recommendations
        context: Contextual data
        include_local_language: Whether to include local language recommendations
        language_weight: Weight for language preference (0-1)
        ensure_language_diversity: Whether to ensure language diversity
        preferred_languages: Comma-separated list of preferred languages
        _uuid: Cache-busting unique ID (ignored in processing)
        _t: Cache-busting timestamp (ignored in processing)
        
    Returns:
        List[RecommendationResponse]: List of recommendations
    """
    try:
        # Completely disable caching - always generate fresh recommendations
        
        # Get user profile
        user_profile = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM UserProfiles WHERE user_id = ?", (user_id,))
            user_row = cursor.fetchone()
            if user_row:
                user_profile = dict(user_row)
        except Exception as e:
            logger.warning(f"Error fetching user profile: {e}")
        
        # Parse preferred languages if provided
        language_prefs = []
        if preferred_languages:
            language_prefs = preferred_languages.split(',')
        elif user_profile and user_profile.get('language_preference'):
            language_prefs = [user_profile.get('language_preference')]
            
        # Improve the contextual data with weather location correlations
        if context.get('location') and not context.get('weather'):
            # Randomize weather to add variety to recommendations
            context['weather'] = simulate_weather(context['location'])
            
        # If mood is not provided, randomize it for diversity
        if not context.get('mood'):
            context['mood'] = simulate_mood()
            
        # Build full context dictionary with user profile data
        context_dict = {
            "mood": context.get('mood'),
            "time_of_day": context.get('time_of_day'),
            "day_of_week": context.get('day_of_week'),
            "weather": context.get('weather'),
            "age": context.get('age') or (user_profile.get('age') if user_profile else None),
            "location": context.get('location') or (user_profile.get('location') if user_profile else None),
            "language": context.get('language') or (user_profile.get('language_preference') if user_profile else None)
        }
        
        # Add user's preferred genres from profile if available
        if user_profile and user_profile.get('preferred_genres'):
            preferred_genres = user_profile.get('preferred_genres')
            if isinstance(preferred_genres, str) and '|' in preferred_genres:
                context_dict["preferred_genres"] = preferred_genres.split('|')
            else:
                context_dict["preferred_genres"] = [preferred_genres]
        
        logger.info(f"Getting fresh recommendations for user {user_id} with context: {context_dict}")
        
        # Get recommendations from recommendation engine
        recommendations = engine.get_recommendations(
            user_id=user_id,
            n=n * 2,  # Get more recommendations than needed to ensure diversity
            context_data=context_dict,
            exclude_items=None
        )
        
        # Apply language filtering if requested
        filtered_recs = recommendations
        if include_local_language and (context.get('language') or language_prefs):
            # Sort recommendations by language preference
            item_language_map = {}
            language_matches = []
            language_mismatches = []
            
            # Get language information for items
            try:
                # Get all item_ids
                item_ids = [item_id for item_id, _ in recommendations]
                if item_ids:
                    # Fetch item details for all items in recommendations
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Get details in batches
                    batch_size = 50
                    for i in range(0, len(item_ids), batch_size):
                        batch = item_ids[i:i+batch_size]
                        placeholders = ','.join(['?' for _ in batch])
                        cursor.execute(f"SELECT item_id, language FROM Items WHERE item_id IN ({placeholders})", batch)
                        for row in cursor.fetchall():
                            item_language_map[row['item_id']] = row['language']
                    conn.close()
            except Exception as e:
                logger.error(f"Error fetching language information: {e}")
            
            # Determine user's preferred languages
            user_languages = set(language_prefs) if language_prefs else set()
            if context.get('language'):
                user_languages.add(context.get('language'))
            
            # Sort recommendations into matches and mismatches
            for item_id, score in recommendations:
                if item_id in item_language_map:
                    item_lang = item_language_map[item_id]
                    if item_lang and item_lang in user_languages:
                        # Boost score for language match
                        boosted_score = min(1.0, score * language_weight)
                        language_matches.append((item_id, boosted_score))
                    else:
                        language_mismatches.append((item_id, score))
                else:
                    language_mismatches.append((item_id, score))
            
            # Ensure language diversity if requested
            if ensure_language_diversity:
                # Take more matches first, then add mismatches if needed
                filtered_recs = language_matches + language_mismatches
            else:
                # Prioritize language matches completely
                filtered_recs = language_matches
                
                # Only add mismatches if we don't have enough matches
                if len(language_matches) < n:
                    filtered_recs.extend(language_mismatches)
            
        # Get item details for recommendations and add some randomness
        recommendation_objects = []
        seen_genres = set()
        
        # Add some randomization to the recommendation order to ensure variety
        random.shuffle(filtered_recs)
        
        # Process recommendations
        for item_id, score in filtered_recs:
            try:
                item_details = get_item_details(item_id)
                if item_details:
                    # Add small random factor to scores for variety
                    adjusted_score = min(1.0, max(0.0, score * (0.9 + random.random() * 0.2)))
                    
                    # Try to diversify by genre while respecting user preferences
                    genres = item_details.get("genres", "")
                    if genres:
                        # Extract all genres for this item
                        all_genres = genres.split("|") if "|" in genres else [genres]
                        main_genre = all_genres[0] if all_genres else ""
                        
                        # Check if this is a preferred genre for the user
                        is_preferred = False
                        if user_profile and user_profile.get('preferred_genres'):
                            user_prefs = user_profile.get('preferred_genres')
                            if isinstance(user_prefs, str):
                                user_prefs = user_prefs.split('|')
                            
                            # Check if any of the item's genres match user preferences
                            is_preferred = any(genre in user_prefs for genre in all_genres)
                        
                        # Skip only if we've seen this genre before AND it's not preferred AND random check passes
                        if main_genre in seen_genres and not is_preferred and random.random() < 0.4:
                            continue
                        
                        # Always add preferred genres to recommendations, but still track them for diversity
                        seen_genres.add(main_genre)
                    
                    recommendation_objects.append({
                        "item_id": item_id,
                        "title": item_details.get("title", "Unknown Title"),
                        "score": float(adjusted_score),
                        "genres": item_details.get("genres"),
                        "release_year": item_details.get("release_year"),
                        "overview": item_details.get("overview")
                    })
                    
                    # Stop once we have enough recommendations
                    if len(recommendation_objects) >= n:
                        break
            except Exception as e:
                logger.error(f"Error getting item details: {e}")
        
        # Sort by score for final order
        recommendation_objects.sort(key=lambda x: x["score"], reverse=True)
        
        # Return only the requested number
        return recommendation_objects[:n]
    except Exception as e:
        logger.error(f"Error in recommendations: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

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
    
    # Stop any remaining tasks gracefully
    logger.info("Cleaning up resources...")
    try:
        # Give tasks time to complete
        await asyncio.sleep(1)
    except asyncio.CancelledError:
        # This is expected during shutdown, ignore it
        pass
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}")
    
    logger.info("API server shutdown complete")

def cache_recommendations(cache_key, recommendations, ttl_seconds=1800):
    """
    Cache recommendations in the database.
    
    Args:
        cache_key: Unique key for the cache entry
        recommendations: List of recommendation objects
        ttl_seconds: Time-to-live in seconds (default: 30 minutes)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Store recommendations as JSON string
        recommendations_json = json.dumps(recommendations)
        created_at = datetime.datetime.now().isoformat()
        
        # Insert or replace cache entry
        cursor.execute(
            "INSERT OR REPLACE INTO recommendation_cache (cache_key, recommendations, created_at) VALUES (?, ?, ?)",
            (cache_key, recommendations_json, created_at)
        )
        
        conn.commit()
        conn.close()
        logger.info(f"Cached recommendations for key: {cache_key}")
    except Exception as e:
        logger.error(f"Failed to cache recommendations: {e}")

def start():
    """Start the API server."""
    # This function is kept for backward compatibility
    # The actual server configuration is now in run.py
    import uvicorn
    uvicorn.run(
        "src.api.main:app", 
        host="0.0.0.0", 
        port=8080, 
        reload=True,
        ws_max_size=16777216,  # 16MB max WebSocket message size
        ws_ping_interval=20.0,  # Send pings to client every 20 seconds
        ws_ping_timeout=30.0,   # Wait up to 30 seconds for pings
        log_level="info"
    )

# Friend system endpoints
@app.post("/friends/search", response_model=List[UserProfileResponse], tags=["Friends"])
async def search_for_users(search_request: SearchUserRequest, user_id: str = Query(..., description="The current user's ID")):
    """
    Search for users by partial username match.
    
    Args:
        search_request: Search query
        user_id: The current user's ID
        
    Returns:
        List of matching user profiles
    """
    results = search_users(search_request.query, user_id)
    
    # Process preferred_genres if present
    for result in results:
        if result.get("preferred_genres"):
            result["preferred_genres"] = result["preferred_genres"].split("|") if result["preferred_genres"] else []
            
    return results

@app.post("/friends/request", status_code=201, tags=["Friends"])
async def create_friend_request(request: FriendRequest):
    """
    Send a friend request from one user to another.
    
    Args:
        request: Friend request details
        
    Returns:
        Success status
    """
    success = send_friend_request(request.sender_id, request.receiver_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to send friend request")
        
    return {"status": "success", "message": "Friend request sent"}

@app.get("/friends/requests/{user_id}", response_model=List[FriendRequestResponse], tags=["Friends"])
async def get_friend_requests(user_id: str):
    """
    Get all pending friend requests for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        List of pending friend requests
    """
    requests = get_pending_friend_requests(user_id)
    return requests

@app.put("/friends/requests/{request_id}", tags=["Friends"])
async def update_friend_request(request_id: int, action: FriendRequestAction):
    """
    Accept or reject a friend request.
    
    Args:
        request_id: Friend request ID
        action: Action to take ('accepted' or 'rejected')
        
    Returns:
        Success status
    """
    success = respond_to_friend_request(request_id, action.status)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to {action.status} friend request")
        
    return {"status": "success", "message": f"Friend request {action.status}"}

@app.get("/friends/{user_id}", response_model=List[FriendResponse], tags=["Friends"])
async def get_user_friends(user_id: str):
    """
    Get all friends of a user.
    
    Args:
        user_id: User ID
        
    Returns:
        List of friend profiles
    """
    friends = get_friends(user_id)
    
    # Process preferred_genres if present
    for friend in friends:
        if friend.get("preferred_genres"):
            friend["preferred_genres"] = friend["preferred_genres"].split("|") if friend["preferred_genres"] else []
            
    return friends

@app.get("/friends/{user_id}/activities", response_model=List[FriendActivityResponse], tags=["Friends"])
async def get_friend_activity(user_id: str, limit: int = Query(20, ge=1, le=100)):
    """
    Get recent activities (interactions) of a user's friends.
    
    Args:
        user_id: User ID
        limit: Maximum number of activities to return
        
    Returns:
        List of friend activities
    """
    activities = get_friend_activities(user_id, limit)
    return activities

@app.get("/friends/{user_id}/notifications", response_model=NotificationCountResponse, tags=["Friends"])
async def get_notification_count(
    user_id: str, 
    since_timestamp: Optional[str] = Query(None, description="Only count activities after this timestamp")
):
    """Get notification counts for friend requests and activities."""
    try:
        # Get pending friend requests
        requests = get_pending_friend_requests(user_id)
        request_count = len(requests)
        
        # Get friend activities
        activities = get_friend_activities(user_id, 50)  # Get recent activities
        
        # Filter activities by timestamp if provided
        if since_timestamp:
            try:
                # Parse the provided timestamp
                from datetime import datetime
                since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
                
                # Filter activities that are newer than the provided timestamp
                activities = [
                    a for a in activities 
                    if datetime.fromisoformat(a["timestamp"].replace('Z', '+00:00')) > since_dt
                ]
            except (ValueError, AttributeError) as e:
                logger.error(f"Error parsing timestamp: {e}")
                # If timestamp format is invalid, return all activities
                pass
                
        activity_count = len(activities)
        
        # watch party invites
        watch_party_invites = len(get_watch_party_invites(user_id))
        total = request_count + activity_count + watch_party_invites
        
        return {
            "friend_requests": request_count,
            "friend_activities": activity_count,
            "watch_parties": watch_party_invites,
            "total": total,
        }
    except Exception as e:
        logger.error(f"Error getting notification counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/friends/recommendations/{user_id}", response_model=List[RecommendationResponse], tags=["Friends"])
async def get_friend_recommendations(
    user_id: str, 
    n: int = Query(5, ge=1, le=20, description="Number of recommendations")
):
    """
    Get recommendations based on what friends are watching.
    
    This endpoint returns items that friends have interacted with positively,
    but the user hasn't watched yet.
    
    Args:
        user_id: User ID
        n: Number of recommendations to return
        
    Returns:
        List of recommendations from friends
    """
    try:
        # Get friend activities
        friend_activities = get_friend_activities(user_id, limit=100)
        
        # Create a set of items the user has already watched
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT item_id FROM Interactions WHERE user_id = ?', (user_id,))
        user_items = {row['item_id'] for row in cursor.fetchall()}
        conn.close()
        
        # Filter for positive interactions (score > 0.6) from friends
        # that the user hasn't watched yet
        friend_recommendations = {}
        
        for activity in friend_activities:
            item_id = activity['item_id']
            
            # Skip if user already watched this
            if item_id in user_items:
                continue
                
            # Only consider positive interactions
            if activity.get('sentiment_score', 0) > 0.6:
                # If multiple friends watched the same item, increase its score
                if item_id in friend_recommendations:
                    friend_recommendations[item_id]['score'] += 0.1
                    friend_recommendations[item_id]['friends'].append(activity['friend_id'])
                else:
                    item_details = get_item_details(item_id)
                    if item_details:
                        friend_recommendations[item_id] = {
                            "item_id": item_id,
                            "title": item_details.get("title", "Unknown"),
                            "score": 0.7,  # Base score
                            "genres": item_details.get("genres"),
                            "release_year": item_details.get("release_year"),
                            "overview": item_details.get("overview"),
                            "friends": [activity['friend_id']]
                        }
        
        # Convert to list and sort by score
        recommendations = list(friend_recommendations.values())
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N recommendations
        result = recommendations[:n]
        
        # If we don't have enough recommendations, pad with regular recommendations
        if len(result) < n and engine is not None:
            additional_needed = n - len(result)
            regular_recs = engine.get_recommendations(user_id, n=additional_needed)
            
            # Convert to the required format and add to results
            for item_id, score in regular_recs:
                if item_id not in friend_recommendations:
                    item_details = get_item_details(item_id)
                    if item_details:
                        result.append({
                            "item_id": item_id,
                            "title": item_details.get("title", "Unknown"),
                            "score": score,
                            "genres": item_details.get("genres"),
                            "release_year": item_details.get("release_year"),
                            "overview": item_details.get("overview")
                        })
        
        # Return the recommendations
        return result
        
    except Exception as e:
        logger.error(f"Error getting friend recommendations: {e}")
        raise HTTPException(status_code=500, detail="Error getting friend recommendations")

if __name__ == "__main__":
    start() 