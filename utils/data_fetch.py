"""
Financial data fetching utilities for FinSense
Handles Alpha Vantage integration and news retrieval via RSS feeds
"""

import pandas as pd
import feedparser
import requests
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple
import random
import sys
import os
from utils.demo_data import demo_data_generator

# Add the backend directory to the path to import config
backend_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from alpha_vantage.timeseries import TimeSeries
    from alpha_vantage.fundamentaldata import FundamentalData
    from alpha_vantage.techindicators import TechIndicators
    import config  # type: ignore
    Config = config.Config  # type: ignore
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Alpha Vantage not available: {e}")
    ALPHA_VANTAGE_AVAILABLE = False


class FinancialDataFetcher:
    """Main class for fetching financial data and news using Alpha Vantage"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache = {}  # Simple cache to avoid repeated requests

        # API limit tracking
        self.api_limit_exceeded = False
        self.demo_mode = True  # Force demo mode for showcase

        # For showcase purposes, always use demo mode
        print("🎭 FinSense running in DEMO MODE for showcase")
        print("   Using realistic mock data - perfect for demonstrations!")

        # Initialize demo data generator
        self.demo_generator = demo_data_generator

        # Try to initialize Alpha Vantage if available, but don't fail if not
        if ALPHA_VANTAGE_AVAILABLE and Config.ALPHA_VANTAGE_API_KEY:
            try:
                self.ts = TimeSeries(
                    key=Config.ALPHA_VANTAGE_API_KEY, output_format='pandas')
                self.fd = FundamentalData(
                    key=Config.ALPHA_VANTAGE_API_KEY, output_format='pandas')
                self.ti = TechIndicators(
                    key=Config.ALPHA_VANTAGE_API_KEY, output_format='pandas')
                self.av_min_request_interval = Config.MIN_REQUEST_INTERVAL
                self.last_av_request_time = 0
                print("✅ Alpha Vantage also available for real data")
            except Exception as e:
                print(f"⚠️  Alpha Vantage setup failed: {e}")
                print("   Continuing with demo mode...")
        else:
            print("⚠️  No Alpha Vantage API key - using demo data only")

    def _alpha_vantage_rate_limit(self):
        """Ensure minimum time between Alpha Vantage requests (12 seconds for free tier)"""
        current_time = time.time()
        time_since_last = current_time - self.last_av_request_time

        if time_since_last < self.av_min_request_interval:
            sleep_time = self.av_min_request_interval - time_since_last
            print(
                f"Alpha Vantage rate limiting: waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)

        self.last_av_request_time = time.time()

    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()

    def enable_demo_mode(self):
        """Enable demo mode to use mock data instead of API calls"""
        self.demo_mode = True
        print("Demo mode enabled - using mock data")

    def disable_demo_mode(self):
        """Disable demo mode to resume API calls"""
        self.demo_mode = False
        print("Demo mode disabled - resuming API calls")

    def is_demo_mode(self) -> bool:
        """Check if demo mode is active"""
        return self.demo_mode or self.api_limit_exceeded

    def get_stock_data(self, ticker: str) -> Dict:
        """
        Fetch basic stock data using Alpha Vantage free tier
        Returns dict with basic stock information
        """
        ticker_upper = ticker.upper()

        # Check if we should use demo data
        if self.demo_mode or self.api_limit_exceeded:
            print(f"Using demo data for {ticker_upper}")
            return demo_data_generator.get_demo_stock_data(ticker_upper)

        # Check cache first (cache for 5 minutes)
        cache_key = f"av_{ticker_upper}_{int(time.time() // 300)}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            result = {
                'ticker': ticker_upper,
                'company_name': ticker_upper,
                'current_price': 0,
                'market_cap': 0,
                'shares_outstanding': 0,
                'fcf_data': [0, 0, 0, 0],
                'fcf_growth_rate': 0,
                'financials': None,
                'balance_sheet': None,
                'cashflow': None,
                'price_history': None,
                'info': {},
                'data_source': 'Alpha Vantage Free Tier'
            }

            # Get current stock price using free tier GLOBAL_QUOTE endpoint
            try:
                self._alpha_vantage_rate_limit()
                quote_data, meta_data = self.ts.get_quote_endpoint(
                    symbol=ticker_upper)

                if not quote_data.empty:
                    # Get the current price
                    current_price = float(quote_data.iloc[0]['05. price'])
                    result['current_price'] = current_price
                    result['price_history'] = quote_data

                    # Store basic info
                    result['info'] = {
                        'currentPrice': current_price,
                        'longName': ticker_upper,
                        'data_source': 'Alpha Vantage Free Tier'
                    }
                else:
                    result['info'] = {
                        'currentPrice': 0,
                        'longName': ticker_upper,
                        'data_source': 'Alpha Vantage Free Tier'
                    }
            except Exception as e:
                print(
                    f"Warning: Could not fetch price data for {ticker_upper}: {str(e)}")
                result['info'] = {
                    'currentPrice': 0,
                    'longName': ticker_upper,
                    'data_source': 'Alpha Vantage Free Tier'
                }

            # Skip premium endpoints for free tier
            print(
                f"Using free tier - skipping premium data for {ticker_upper}")

            # Cache the result
            self.cache[cache_key] = result
            return result

        except Exception as e:
            if "API call frequency" in str(e) or "5 calls per minute" in str(e):
                raise Exception(
                    f"Alpha Vantage rate limit exceeded for {ticker}. Please wait before trying again.")
            else:
                raise Exception(
                    f"Error fetching Alpha Vantage data for {ticker}: {str(e)}")

    def _extract_av_fcf_data(self, cashflow: pd.DataFrame) -> List[float]:
        """Extract Free Cash Flow data from Alpha Vantage cashflow statement"""
        fcf_data = []

        try:
            # Look for Free Cash Flow in the cashflow data
            if 'freeCashFlow' in cashflow.index:
                fcf_series = cashflow.loc['freeCashFlow'].dropna()
                if len(fcf_series) >= 3:
                    # Convert to float and get last 4 years
                    fcf_values = []
                    for val in fcf_series.head(4):
                        try:
                            fcf_values.append(float(val))
                        except (ValueError, TypeError):
                            fcf_values.append(0.0)
                    fcf_data = fcf_values
        except Exception as e:
            print(f"Error extracting FCF from Alpha Vantage data: {e}")

        # Fallback to zeros if no data found
        if not fcf_data:
            fcf_data = [0.0, 0.0, 0.0, 0.0]

        return fcf_data

    def _calculate_growth_rate(self, fcf_data: List[float]) -> float:
        """Calculate average FCF growth rate over available years"""
        if len(fcf_data) < 2:
            return 0.0

        # Remove any zeros or negative values for growth calculation
        valid_data = [x for x in fcf_data if x > 0]

        if len(valid_data) < 2:
            return 0.0

        # Calculate year-over-year growth rates
        growth_rates = []
        for i in range(1, len(valid_data)):
            if valid_data[i-1] != 0:
                growth_rate = (
                    valid_data[i] - valid_data[i-1]) / abs(valid_data[i-1])
                growth_rates.append(growth_rate)

        # Return average growth rate, capped at reasonable limits
        if growth_rates:
            avg_growth = sum(growth_rates) / len(growth_rates)
            return max(-0.5, min(0.5, avg_growth))  # Cap between -50% and +50%

        return 0.0

    def get_news_headlines(self, ticker: str, max_articles: int = 20) -> List[Dict]:
        """
        Fetch news headlines using RSS feeds (free alternative to paid APIs)
        Uses multiple financial news sources for comprehensive coverage
        """
        news_sources = [
            f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
            f"https://feeds.marketwatch.com/marketwatch/topstories/",
            "https://feeds.reuters.com/reuters/businessNews",
            "https://rss.cnn.com/rss/money_latest.rss"
        ]

        all_articles = []

        for source in news_sources:
            try:
                feed = feedparser.parse(source)

                for entry in feed.entries[:max_articles//len(news_sources)]:
                    # Filter for ticker-relevant articles
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')

                    # Simple relevance check - look for ticker in title or summary
                    if ticker.upper() in title.upper() or ticker.upper() in summary.upper():
                        article = {
                            'title': title,
                            'summary': summary,
                            'published': entry.get('published', ''),
                            'link': entry.get('link', ''),
                            'source': source
                        }
                        all_articles.append(article)

                time.sleep(0.5)  # Be respectful to RSS feeds

            except Exception as e:
                print(f"Error fetching from {source}: {str(e)}")
                continue

        # Remove duplicates and limit results
        seen_titles = set()
        unique_articles = []

        for article in all_articles:
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                unique_articles.append(article)

                if len(unique_articles) >= max_articles:
                    break

        return unique_articles

    def get_market_data(self, ticker: str) -> Dict:
        """Get additional market data for context using Alpha Vantage"""
        ticker_upper = ticker.upper()

        try:
            # Get 1-year price data for volatility calculation
            self._alpha_vantage_rate_limit()
            data, _ = self.ts.get_daily_adjusted(
                ticker_upper, outputsize='full')

            if data.empty:
                return {}

            # Calculate volatility (annualized)
            returns = data['5. adjusted close'].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)  # Annualized

            # Calculate beta (simplified - would need market index for proper calculation)
            beta = 1.0  # Default assumption

            return {
                'volatility': volatility,
                'beta': beta,
                '52_week_high': data['2. high'].max(),
                '52_week_low': data['4. low'].min(),
                'avg_volume': data['6. volume'].mean()
            }

        except Exception as e:
            print(f"Error getting market data: {str(e)}")
            return {}

    def get_technical_indicators(self, ticker: str) -> Dict:
        """
        Get technical indicators using Alpha Vantage
        Returns RSI, MACD, SMA, EMA, and other indicators
        """
        ticker_upper = ticker.upper()

        # Check cache first
        cache_key = f"ti_{ticker_upper}_{int(time.time() // 300)}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            indicators = {}

            # RSI (Relative Strength Index)
            try:
                self._alpha_vantage_rate_limit()
                rsi_data, rsi_meta = self.ti.get_rsi(
                    ticker_upper, time_period=14)
                if not rsi_data.empty:
                    indicators['rsi'] = rsi_data.iloc[0]['RSI']
            except Exception as e:
                print(f"Could not fetch RSI for {ticker_upper}: {e}")

            # MACD (Moving Average Convergence Divergence)
            try:
                self._alpha_vantage_rate_limit()
                macd_data, macd_meta = self.ti.get_macd(ticker_upper)
                if not macd_data.empty:
                    latest_macd = macd_data.iloc[0]
                    indicators['macd'] = {
                        'MACD': latest_macd['MACD'],
                        'MACD_Signal': latest_macd['MACD_Signal'],
                        'MACD_Hist': latest_macd['MACD_Hist']
                    }
            except Exception as e:
                print(f"Could not fetch MACD for {ticker_upper}: {e}")

            # Simple Moving Average (SMA)
            try:
                self._alpha_vantage_rate_limit()
                sma_data, sma_meta = self.ti.get_sma(
                    ticker_upper, time_period=20)
                if not sma_data.empty:
                    indicators['sma_20'] = sma_data.iloc[0]['SMA']
            except Exception as e:
                print(f"Could not fetch SMA for {ticker_upper}: {e}")

            # Exponential Moving Average (EMA)
            try:
                self._alpha_vantage_rate_limit()
                ema_data, ema_meta = self.ti.get_ema(
                    ticker_upper, time_period=20)
                if not ema_data.empty:
                    indicators['ema_20'] = ema_data.iloc[0]['EMA']
            except Exception as e:
                print(f"Could not fetch EMA for {ticker_upper}: {e}")

            # Bollinger Bands
            try:
                self._alpha_vantage_rate_limit()
                bb_data, bb_meta = self.ti.get_bbands(
                    ticker_upper, time_period=20)
                if not bb_data.empty:
                    latest_bb = bb_data.iloc[0]
                    indicators['bollinger_bands'] = {
                        'Upper': latest_bb['Real Upper Band'],
                        'Middle': latest_bb['Real Middle Band'],
                        'Lower': latest_bb['Real Lower Band']
                    }
            except Exception as e:
                print(
                    f"Could not fetch Bollinger Bands for {ticker_upper}: {e}")

            # Cache the result
            self.cache[cache_key] = indicators
            return indicators

        except Exception as e:
            if "API call frequency" in str(e) or "5 calls per minute" in str(e):
                raise Exception(
                    f"Alpha Vantage rate limit exceeded for technical indicators. Please wait before trying again.")
            else:
                raise Exception(
                    f"Error fetching technical indicators for {ticker}: {str(e)}")

    def get_popular_tickers(self) -> List[Dict]:
        """
        Get a list of popular stock tickers with basic information
        Returns a predefined list of popular stocks since Alpha Vantage doesn't have a ticker list endpoint
        """
        # Check if we should use demo data
        if self.demo_mode or self.api_limit_exceeded:
            print("Using demo data for popular tickers")
            return demo_data_generator.get_demo_tickers(3)

        # Popular tickers - only 3 stocks to get real prices within free tier limits
        popular_tickers = [
            {"symbol": "AAPL", "name": "Apple Inc.",
                "price": 0, "change": 0, "market_cap": 0},
            {"symbol": "MSFT", "name": "Microsoft Corporation",
                "price": 0, "change": 0, "market_cap": 0},
            {"symbol": "GOOGL", "name": "Alphabet Inc. Class A",
                "price": 0, "change": 0, "market_cap": 0}
        ]

        # Get current prices for all 3 tickers using free tier GLOBAL_QUOTE endpoint
        for i, ticker_data in enumerate(popular_tickers):
            try:
                # Use the free tier GLOBAL_QUOTE endpoint
                self._alpha_vantage_rate_limit()
                quote_data, meta_data = self.ts.get_quote_endpoint(
                    symbol=ticker_data["symbol"])

                if not quote_data.empty:
                    # Get the current price and change
                    current_price = float(quote_data.iloc[0]['05. price'])
                    change_percent = float(
                        quote_data.iloc[0]['10. change percent'].replace('%', ''))

                    ticker_data["price"] = current_price
                    ticker_data["change"] = change_percent

                    print(
                        f"Got price for {ticker_data['symbol']}: ${current_price:.2f} ({change_percent:+.2f}%)")
                else:
                    print(f"No data available for {ticker_data['symbol']}")

            except Exception as e:
                error_msg = str(e)
                print(
                    f"Could not fetch data for {ticker_data['symbol']}: {error_msg}")

                # Check if this is an API limit error
                if "premium" in error_msg.lower() or "limit" in error_msg.lower() or "exceeded" in error_msg.lower():
                    print("API limit detected, switching to demo mode")
                    self.api_limit_exceeded = True
                    self.demo_mode = True
                    return demo_data_generator.get_demo_tickers(3)

                # Keep default values (0) if fetch fails

            # Add delay to respect rate limits (25 calls per day = 57.6 seconds between calls)
            if i < 2:  # Don't delay after the last request
                # Wait 8 seconds between calls to be more aggressive
                time.sleep(8)

        return popular_tickers

    def get_current_time(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()

    def get_alpha_vantage_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """
        Get news sentiment data using Alpha Vantage News & Sentiment API
        Note: This requires a premium Alpha Vantage subscription
        """
        ticker_upper = ticker.upper()

        try:
            # This would require the News & Sentiment API which is premium
            # For now, we'll return a placeholder
            print(f"News sentiment API requires premium Alpha Vantage subscription")
            return []

        except Exception as e:
            print(f"Error fetching Alpha Vantage news: {e}")
            return []
