# Local Recommendation System

A fully local recommendation system for movies, TV shows, and other media, built from scratch to provide high-quality, diverse, and personalized recommendations. The system leverages datasets from MovieLens and TMDb, automatically downloading and processing them to create a seamless experience.

## Features

- Hybrid recommendation system combining collaborative filtering, content-based filtering, and contextual adjustments
- Fully local operation with no external API dependencies
- Real-time updates via online learning
- Personalization based on user interactions and contextual factors
- Diversity in recommendations to avoid repetition
- Automated dataset downloading and processing
- Exclusive use of real data for all operations (no simulated data)

## Architecture

1. **Data Layer**
   - SQLite database for persistent storage
   - In-memory cache for reduced latency
   - Automated dataset download and processing

2. **Processing Layer**
   - Collaborative Filtering using Matrix Factorization (SVD)
   - Content-Based Filtering using TF-IDF and cosine similarity
   - Contextual adjustment using SGDRegressor
   - Feature engineering and online learning

3. **Application Layer**
   - FastAPI server for recommendation requests
   - Background processing for new interactions
   - Model persistence using joblib

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Sufficient disk space for datasets (approximately 2-3 GB)
- Kaggle API credentials (optional, for TMDB dataset)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/local-recommendation-system.git
   cd local-recommendation-system
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. (Optional) Set up Kaggle API credentials:
   - Download your Kaggle API credentials (kaggle.json) from your Kaggle account
   - Place the kaggle.json file in the following location:
     - Windows: `C:\Users\<Windows-username>\.kaggle\kaggle.json`
     - Linux/macOS: `~/.kaggle/kaggle.json`
   - Ensure the file has restricted permissions:
     - Linux/macOS: `chmod 600 ~/.kaggle/kaggle.json`

4. Run the system (includes automatic dataset download and processing):
   ```
   python run.py
   ```
   
   This will:
   - Download the MovieLens dataset automatically
   - Download the TMDB dataset if Kaggle credentials are available
   - Process the datasets
   - Train the recommendation models
   - Start the API server

### Usage

1. Start the local API server if not already running:
   ```
   python run.py --step api
   ```

2. Make recommendation requests:
   ```
   GET http://localhost:8000/recommend?user_id=123&mood=happy&n=10
   ```

3. Record user interactions:
   ```
   POST http://localhost:8000/interaction
   {
     "user_id": "123",
     "item_id": "ml_1234",
     "sentiment_score": 0.9,
     "mood": "happy",
     "time_of_day": "evening",
     "weather": "clear"
   }
   ```

## Advanced Usage

1. Download and process datasets only:
   ```
   python run.py --step preprocess
   ```

2. Train models only:
   ```
   python run.py --step train
   ```

3. Process only a sample of the data (for testing):
   ```
   python run.py --sample 1000
   ```

## Data Sources

This project automatically downloads and uses the following datasets:
- MovieLens Dataset (small): Contains movie ratings and metadata
- TMDb Datasets (optional): Contains detailed movie information

## License

This project is licensed under the MIT License - see the LICENSE file for details.

**Note**: All datasets are used in compliance with their respective licenses and terms of use.

# Recommendation System Backend

This directory contains the backend code for the recommendation system.

## Running the Backend

### Quick Start (With WebSocket Support)

To run the API server with WebSocket support for watch parties:

```bash
python run.py --step api
```

This will start the server at:
- API endpoint: http://localhost:8080
- WebSocket endpoint: ws://localhost:8080/socket.io/

### Full System

To run the full system with data preprocessing and model training:

```bash
python run.py
```

This will:
1. Download necessary datasets
2. Preprocess the data
3. Train recommendation models
4. Start the API server with WebSocket support

To run only specific steps:

```bash
python run.py --step preprocess  # Only preprocess data
python run.py --step train       # Only train models
python run.py --step api         # Only start API server
```

## Troubleshooting

### Port Conflicts

If you see errors related to port 8080 already being in use:

1. Run the port kill script to free the port:
   ```bash
   python kill_port.py
   ```

2. If that doesn't work, manually find and stop the process:
   - For Windows: `netstat -ano | findstr :8080` to find the PID, then `taskkill /F /PID <PID>` to kill it
   - For Linux/Mac: `lsof -i :8080` to find the PID, then `kill -9 <PID>` to kill it

3. Make sure you don't have multiple instances of the server running

### Startup Crashes

If the server crashes immediately after startup:

1. Check logs in `logs/api.log` for specific error messages
2. Make sure no other process is using port 8080
3. Try running with logging level set to debug by setting environment variable: `set DEBUG=1` (Windows) or `export DEBUG=1` (Linux/Mac)

### WebSocket Connection Issues

If you're experiencing WebSocket connection issues:

1. Check that the server is running at http://localhost:8080
2. Verify the WebSocket endpoint is accessible at ws://localhost:8080/socket.io/
3. Check browser console for connection errors
4. Look at server logs in logs/api.log for connection details

## API Endpoints

The API provides the following endpoints:

- `/recommend?user_id=<user_id>` - Get recommendations for a user
- `/interaction` - Record user interactions with content
- `/user/<user_id>/history` - Get user interaction history

See FastAPI documentation at http://localhost:8080/docs for more details. 