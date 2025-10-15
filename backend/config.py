"""
Configuration settings for FinSense backend
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for FinSense backend"""

    # Alpha Vantage API Configuration
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'

    # Rate limiting
    ALPHA_VANTAGE_REQUESTS_PER_MINUTE = 5  # Free tier limit
    MIN_REQUEST_INTERVAL = 12  # 12 seconds between requests

    # Cache settings
    CACHE_DURATION_MINUTES = 5

    # API Settings
    API_HOST = '0.0.0.0'
    API_PORT = 8000

    # CORS settings
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        # For demo/showcase purposes, we'll use mock data if no API key is provided
        if not cls.ALPHA_VANTAGE_API_KEY:
            print("⚠️  No Alpha Vantage API key found - using demo/mock data")
            print("   This is perfect for showcasing the app!")
        return True


# Validate configuration on import
Config.validate_config()
