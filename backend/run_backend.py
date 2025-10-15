#!/usr/bin/env python3
"""
Run the FinSense backend
"""

import uvicorn
import sys
import os

# Add parent directory to path to find utils and backend
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import after path setup
from config import Config
from main import app


# Import and run the backend

if __name__ == "__main__":
    print(
        f"🚀 Starting FinSense API server on {Config.API_HOST}:{Config.API_PORT}")
    print(
        f"🔑 Using Alpha Vantage API with key: {Config.ALPHA_VANTAGE_API_KEY[:8]}...")
    uvicorn.run("main:app", host=Config.API_HOST,
                port=Config.API_PORT, reload=True)
