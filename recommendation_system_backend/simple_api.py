#!/usr/bin/env python3
"""
Simplified API runner for the recommendation system.
"""

import os
import sys
import logging
import uvicorn

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(script_dir, "logs/api.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def start_server():
    """Start the API server with optimized WebSocket settings."""
    print("Starting API server with WebSocket support...")
    print("Server will be available at http://localhost:8080")
    print("WebSocket will be available at ws://localhost:8080/socket.io/")
    
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

if __name__ == "__main__":
    start_server() 