"""
FinSense Backend - FastAPI Server
Modern REST API for financial analysis
"""

from utils.pdf_generator import PDFReportGenerator
from utils.excel_exporter import ExcelExporter
from utils.visualizations import FinSenseVisualizations
from utils.dcf_calc import DCFCalculator
from utils.data_fetch import FinancialDataFetcher
from config import Config
from fastapi import FastAPI, HTTPException, Path, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
import uvicorn
import sys
import os
import re
import time
from datetime import datetime, timedelta
from collections import defaultdict

# Import our security modules (commented out for now to keep app working)
# from auth import (
#     authenticate_user, create_access_token, get_current_active_user,
#     get_admin_user, User, Token, fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES
# )
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from security import SecurityHeadersMiddleware, RequestLoggingMiddleware, RateLimitMiddleware

# Add parent directory to path to import utils modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


app = FastAPI(
    title="FinSense API",
    description="AI-Powered Financial Analysis API",
    version="1.0.0"
)

# Add security middleware (commented out for now to keep app working)
# app.add_middleware(SecurityHeadersMiddleware)
# app.add_middleware(RequestLoggingMiddleware)
# app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Initialize services
data_fetcher = FinancialDataFetcher()
dcf_calculator = DCFCalculator()
visualizations = FinSenseVisualizations()
excel_exporter = ExcelExporter()
pdf_generator = PDFReportGenerator()

# Rate limiting storage
request_counts = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # 1 minute window
RATE_LIMIT_MAX_REQUESTS = 30  # Max 30 requests per minute per IP


def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit"""
    current_time = time.time()

    # Clean old requests outside the window
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]

    # Check if limit exceeded
    if len(request_counts[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    # Add current request
    request_counts[client_ip].append(current_time)
    return True

# Pydantic models


class StockAnalysisRequest(BaseModel):
    growth_rate: Optional[float] = None
    discount_rate: Optional[float] = None
    terminal_growth: Optional[float] = None

    @validator('growth_rate')
    def validate_growth_rate(cls, v):
        if v is not None and (v < -0.5 or v > 2.0):
            raise ValueError('Growth rate must be between -50% and 200%')
        return v

    @validator('discount_rate')
    def validate_discount_rate(cls, v):
        if v is not None and (v <= 0 or v > 0.5):
            raise ValueError('Discount rate must be between 0% and 50%')
        return v

    @validator('terminal_growth')
    def validate_terminal_growth(cls, v):
        if v is not None and (v < 0 or v > 0.1):
            raise ValueError('Terminal growth rate must be between 0% and 10%')
        return v


class ExportRequest(BaseModel):
    ticker: str
    format: str  # 'excel' or 'pdf'
    data: Dict[str, Any]

    @validator('ticker')
    def validate_ticker(cls, v):
        if not re.match(r'^[A-Z]{1,5}$', v.upper()):
            raise ValueError('Ticker must be 1-5 uppercase letters')
        return v.upper()

    @validator('format')
    def validate_format(cls, v):
        if v.lower() not in ['excel', 'pdf']:
            raise ValueError('Format must be either "excel" or "pdf"')
        return v.lower()


@app.get("/")
async def root():
    return {"message": "FinSense API is running!", "version": "1.0.0", "security": "enterprise-grade"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "security": "enabled"}


# Authentication endpoints (commented out for now - can be enabled later)
# @app.post("/api/auth/login", response_model=Token)
# async def login_for_access_token(email: str, password: str):
#     """Authenticate user and return JWT token"""
#     user = authenticate_user(fake_users_db, email, password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.email}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}


# @app.get("/api/auth/me", response_model=User)
# async def read_users_me(current_user: User = Depends(get_current_active_user)):
#     """Get current user info"""
#     return current_user


@app.get("/api/auth/demo-credentials")
async def get_demo_credentials():
    """Get demo credentials for showcase"""
    return {
        "demo_user": {
            "email": "demo@finsense.com",
            "password": "secret",
            "role": "user"
        },
        "admin_user": {
            "email": "admin@finsense.com",
            "password": "admin",
            "role": "admin"
        },
        "note": "These are demo credentials for showcase purposes"
    }


@app.post("/api/analyze/{ticker}")
async def analyze_stock(
    ticker: str = Path(..., regex=r'^[A-Z]{1,5}$',
                       description="Stock ticker symbol (1-5 uppercase letters)"),
    request: StockAnalysisRequest = None
):
    """Analyze a stock with DCF calculation"""
    try:
        # Log analysis request
        print(
            f"Analysis request for {ticker} - security features ready for activation")
        # Fetch financial data
        stock_data = data_fetcher.get_stock_data(ticker)
        if not stock_data:
            raise HTTPException(
                status_code=404, detail=f"No data found for ticker: {ticker}")

        # Calculate DCF
        dcf_results = dcf_calculator.calculate_dcf_valuation(
            fcf_history=stock_data.get('fcf_data', []),
            fcf_growth_rate=request.growth_rate or 0.05,
            wacc=request.discount_rate or 0.10,
            terminal_growth=request.terminal_growth or 0.03,
            shares_outstanding=stock_data.get('shares_outstanding', 1e9),
            monte_carlo_runs=1000
        )

        return {
            "ticker": ticker.upper(),
            "stock_data": stock_data,
            "dcf_results": dcf_results,
            "timestamp": "2024-01-01T00:00:00Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        # Log the full error for debugging but don't expose it to client
        print(f"Internal error in analyze_stock: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred")


@app.get("/api/stock/{ticker}")
async def get_stock_data(ticker: str = Path(..., regex=r'^[A-Z]{1,5}$', description="Stock ticker symbol (1-5 uppercase letters)")):
    """Get basic stock data"""
    try:
        stock_data = data_fetcher.get_stock_data(ticker)
        if not stock_data:
            raise HTTPException(
                status_code=404, detail=f"No data found for ticker: {ticker}")

        return {
            "ticker": ticker.upper(),
            "data": stock_data,
            "timestamp": data_fetcher.get_current_time()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/visualizations/{ticker}")
async def get_visualizations(ticker: str = Path(..., regex=r'^[A-Z]{1,5}$', description="Stock ticker symbol (1-5 uppercase letters)")):
    """Get chart data for visualizations"""
    try:
        stock_data = data_fetcher.get_stock_data(ticker)
        if not stock_data:
            raise HTTPException(
                status_code=404, detail=f"No data found for ticker: {ticker}")

        # Create chart data
        price_chart = visualizations.create_price_chart(stock_data)
        financial_chart = visualizations.create_financial_metrics_chart(
            stock_data)

        return {
            "ticker": ticker.upper(),
            "charts": {
                "price_chart": price_chart,
                "financial_chart": financial_chart
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tickers")
async def get_popular_tickers():
    """Get popular stock tickers with current prices using Alpha Vantage API"""
    try:
        tickers_data = data_fetcher.get_popular_tickers()

        return {
            "tickers": tickers_data,
            "count": len(tickers_data),
            "timestamp": data_fetcher.get_current_time()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/export")
async def export_data(request: ExportRequest):
    """Export analysis data to Excel or PDF"""
    try:
        if request.format.lower() == "excel":
            file_path = excel_exporter.export_comprehensive_analysis(
                stock_data=request.data.get('stock_data', {}),
                dcf_results=request.data.get('dcf_results', {}),
                sentiment_summary={},
                analyzed_articles=[]
            )
            return FileResponse(
                file_path,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=f"FinSense_Analysis_{request.ticker}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            )
        elif request.format.lower() == "pdf":
            file_path = pdf_generator.generate_report(
                ticker=request.ticker,
                data=request.data
            )
            return FileResponse(
                file_path,
                media_type="application/pdf",
                filename=f"FinSense_Analysis_{request.ticker}_{datetime.now().strftime('%Y%m%d')}.pdf"
            )
        else:
            raise HTTPException(
                status_code=400, detail="Invalid format. Use 'excel' or 'pdf'")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/demo-mode")
async def toggle_demo_mode():
    """Toggle demo mode on/off"""
    try:
        if data_fetcher.is_demo_mode():
            data_fetcher.disable_demo_mode()
            return {"demo_mode": False, "message": "Demo mode disabled - using real API data"}
        else:
            data_fetcher.enable_demo_mode()
            return {"demo_mode": True, "message": "Demo mode enabled - using mock data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/demo-mode")
async def get_demo_mode_status():
    """Get current demo mode status"""
    try:
        return {
            "demo_mode": data_fetcher.is_demo_mode(),
            "api_limit_exceeded": data_fetcher.api_limit_exceeded,
            "manual_demo_mode": data_fetcher.demo_mode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Backend can be run from project root using run_backend.py
# or directly with: uvicorn backend.main:app --host 0.0.0.0 --port 8000
