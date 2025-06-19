import datetime
import random
import logging
import os
import requests
import numpy as np
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path("logs/context_utils.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants for context
MOODS = ["happy", "sad", "neutral", "excited", "relaxed", "bored", "stressed", "curious"]
WEATHERS = ["sunny", "cloudy", "rainy", "snowy", "foggy", "windy", "stormy", "clear"]
TIME_OF_DAY_RANGES = {
    "early_morning": (5, 8),
    "morning": (8, 12),
    "afternoon": (12, 17),
    "evening": (17, 21),
    "night": (21, 24),
    "late_night": (0, 5)
}
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
AGE_GROUPS = ["child", "teen", "young_adult", "adult", "senior"]
AGE_GROUP_RANGES = {
    "child": (5, 12),
    "teen": (13, 19),
    "young_adult": (20, 35),
    "adult": (36, 65),
    "senior": (66, 100)
}

# Weather API configuration
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '')  # OpenWeatherMap API key
DEFAULT_LOCATION = 'New York'  # Default location if none specified

# Mood mappings
MOOD_ENCODINGS = {
    'happy': [1, 0, 0, 0, 0],
    'sad': [0, 1, 0, 0, 0],
    'excited': [0, 0, 1, 0, 0],
    'relaxed': [0, 0, 0, 1, 0],
    'neutral': [0, 0, 0, 0, 1],
    None: [0, 0, 0, 0, 1]  # Default to neutral
}

# Weather mappings
WEATHER_ENCODINGS = {
    'sunny': [1, 0, 0, 0, 0],
    'rainy': [0, 1, 0, 0, 0],
    'cloudy': [0, 0, 1, 0, 0],
    'snowy': [0, 0, 0, 1, 0],
    'clear': [0, 0, 0, 0, 1],
    None: [0, 0, 0, 0, 1]  # Default to clear
}

# Time of day mappings
TIME_OF_DAY_ENCODINGS = {
    'morning': [1, 0, 0, 0],
    'afternoon': [0, 1, 0, 0],
    'evening': [0, 0, 1, 0],
    'night': [0, 0, 0, 1],
    None: [0, 0, 0, 0]  # Default to no time specified
}

# Day of week mappings
DAY_OF_WEEK_ENCODINGS = {
    'Monday': [1, 0, 0, 0, 0, 0, 0],
    'Tuesday': [0, 1, 0, 0, 0, 0, 0],
    'Wednesday': [0, 0, 1, 0, 0, 0, 0],
    'Thursday': [0, 0, 0, 1, 0, 0, 0],
    'Friday': [0, 0, 0, 0, 1, 0, 0],
    'Saturday': [0, 0, 0, 0, 0, 1, 0],
    'Sunday': [0, 0, 0, 0, 0, 0, 1],
    None: [0, 0, 0, 0, 0, 0, 0]  # Default to no day specified
}

def get_current_time_of_day():
    """Get the current time of day based on current hour."""
    current_hour = datetime.datetime.now().hour
    
    for time_of_day, (start_hour, end_hour) in TIME_OF_DAY_RANGES.items():
        if start_hour <= current_hour < end_hour:
            return time_of_day
    
    return "night"  # Default fallback

def get_current_day_of_week():
    """Get the current day of the week."""
    return DAYS_OF_WEEK[datetime.datetime.now().weekday()]

def simulate_weather(location=None):
    """
    Simulate weather based on location or return random weather.
    In a real system, this would connect to a weather API.
    """
    # In a real system, we would use a weather API based on location
    return random.choice(WEATHERS)

def simulate_mood():
    """Simulate user mood (random for now)."""
    # In a real system, this might be inferred from user behavior or explicitly set
    return random.choice(MOODS)

def get_age_group(age):
    """Get age group based on age."""
    if age is None:
        return None
    
    for group, (min_age, max_age) in AGE_GROUP_RANGES.items():
        if min_age <= age <= max_age:
            return group
    
    return "adult"  # Default fallback

def generate_random_contextual_data():
    """Generate random contextual data for testing."""
    age = random.randint(5, 100)
    return {
        "mood": simulate_mood(),
        "weather": random.choice(WEATHERS),
        "time_of_day": get_current_time_of_day(),
        "day_of_week": get_current_day_of_week(),
        "age": age,
        "age_group": get_age_group(age),
        "location": f"City_{random.randint(1, 50)}"
    }

def encode_mood(mood):
    """One-hot encode mood for model input."""
    if not mood or mood not in MOODS:
        # Default to neutral if mood is invalid
        mood = "neutral"
    
    encoding = [0] * len(MOODS)
    encoding[MOODS.index(mood)] = 1
    return encoding

def encode_weather(weather):
    """One-hot encode weather for model input."""
    if not weather or weather not in WEATHERS:
        # Default to clear if weather is invalid
        weather = "clear"
    
    encoding = [0] * len(WEATHERS)
    encoding[WEATHERS.index(weather)] = 1
    return encoding

def encode_time_of_day(time_of_day):
    """One-hot encode time of day for model input."""
    if not time_of_day or time_of_day not in TIME_OF_DAY_RANGES:
        # Default to current time if time_of_day is invalid
        time_of_day = get_current_time_of_day()
    
    encoding = [0] * len(TIME_OF_DAY_RANGES)
    encoding[list(TIME_OF_DAY_RANGES.keys()).index(time_of_day)] = 1
    return encoding

def encode_day_of_week(day_of_week):
    """One-hot encode day of week for model input."""
    if not day_of_week or day_of_week not in DAYS_OF_WEEK:
        # Default to current day if day_of_week is invalid
        day_of_week = get_current_day_of_week()
    
    encoding = [0] * len(DAYS_OF_WEEK)
    encoding[DAYS_OF_WEEK.index(day_of_week)] = 1
    return encoding

def normalize_age(age):
    """Normalize age to 0-1 range."""
    if not age:
        return 0.5  # Default to middle age if age is not provided
    
    min_age = 5
    max_age = 100
    return (age - min_age) / (max_age - min_age)

def get_contextual_features(context_data):
    """
    Convert contextual data into feature vector for model input.
    
    Args:
        context_data (dict): Dictionary containing mood, weather, time_of_day, day_of_week, age
        
    Returns:
        list: Feature vector for model input
    """
    features = []
    
    # Add mood encoding
    features.extend(encode_mood(context_data.get("mood")))
    
    # Add weather encoding
    features.extend(encode_weather(context_data.get("weather")))
    
    # Add time of day encoding
    features.extend(encode_time_of_day(context_data.get("time_of_day")))
    
    # Add day of week encoding
    features.extend(encode_day_of_week(context_data.get("day_of_week")))
    
    # Add normalized age
    features.append(normalize_age(context_data.get("age")))
    
    return features

def get_current_context():
    """Get the current context based on time, day, and simulated data."""
    return {
        "mood": simulate_mood(),
        "weather": simulate_weather(),
        "time_of_day": get_current_time_of_day(),
        "day_of_week": get_current_day_of_week(),
        "location": None  # Would be set by user in real system
    }

def get_real_weather(location=None):
    """
    Get real weather data from OpenWeatherMap API.
    
    Args:
        location (str, optional): Location to get weather for. Defaults to 'New York'.
        
    Returns:
        tuple: (weather_condition, temperature_celsius)
    """
    if not WEATHER_API_KEY:
        logger.warning("No Weather API key found, using simulated weather")
        return simulate_weather(), 22.0  # Default temperature
    
    location = location or DEFAULT_LOCATION
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code != 200:
            logger.error(f"Error getting weather: {data.get('message', 'Unknown error')}")
            return simulate_weather(), 22.0
        
        # Get temperature
        temperature = data['main']['temp']
        
        # Map OpenWeatherMap weather codes to our weather categories
        weather_id = data['weather'][0]['id']
        
        # Thunderstorm: 200-299, Drizzle: 300-399, Rain: 500-599
        if 200 <= weather_id < 600:
            return 'rainy', temperature
        # Snow: 600-699
        elif 600 <= weather_id < 700:
            return 'snowy', temperature
        # Atmosphere (mist, fog, etc): 700-799
        elif 700 <= weather_id < 800:
            return 'cloudy', temperature
        # Clear: 800
        elif weather_id == 800:
            return 'clear', temperature
        # Clouds: 801-899
        elif 801 <= weather_id < 900:
            return 'cloudy', temperature
        else:
            return 'clear', temperature
    
    except Exception as e:
        logger.error(f"Error getting real weather data: {e}")
        return simulate_weather(), 22.0

def get_current_context(location=None):
    """
    Get the current context based on real time, day, and weather.
    
    Args:
        location (str, optional): Location to get weather for. Defaults to None.
    
    Returns:
        dict: Dictionary with current context data
    """
    # Get real weather and temperature
    weather, temperature = get_real_weather(location)
    
    return {
        "mood": None,  # Mood always needs user input
        "weather": weather,
        "temperature": temperature,
        "time_of_day": get_current_time_of_day(),
        "day_of_week": get_current_day_of_week(),
        "location": location
    }

if __name__ == "__main__":
    # Test the context utilities
    current_context = get_current_context()
    logger.info(f"Current context: {current_context}")
    
    # Test feature encoding
    test_context = {
        "mood": "happy",
        "weather": "sunny",
        "time_of_day": "evening",
        "day_of_week": "Friday",
        "age": 30
    }
    features = get_contextual_features(test_context)
    logger.info(f"Encoded features for {test_context}: {features}") 