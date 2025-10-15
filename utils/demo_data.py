"""
Demo Data Generator for FinSense
Provides realistic mock data when API limits are exceeded
"""

import random
import time
from typing import Dict, List
from datetime import datetime, timedelta
import json


class DemoDataGenerator:
    """Generates realistic mock financial data for demonstration purposes"""

    def __init__(self):
        self.base_prices = {
            "AAPL": 247.66,
            "MSFT": 514.05,
            "GOOGL": 244.15,
            "AMZN": 185.50,
            "TSLA": 248.42,
            "META": 520.80,
            "NVDA": 183.00,
            "NFLX": 485.35,
            "AMD": 142.67,
            "INTC": 43.82
        }

        self.company_names = {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc. Class A",
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc.",
            "META": "Meta Platforms Inc.",
            "NVDA": "NVIDIA Corporation",
            "NFLX": "Netflix Inc.",
            "AMD": "Advanced Micro Devices Inc.",
            "INTC": "Intel Corporation"
        }

        # Seed random with current hour to rotate data throughout the day
        self.rotation_seed = int(time.time() // 3600)  # Changes every hour
        random.seed(self.rotation_seed)

    def get_demo_tickers(self, count: int = 3) -> List[Dict]:
        """
        Get demo ticker data with realistic price variations
        Rotates data every hour to simulate different market conditions
        """
        # Select random subset of tickers for variety
        available_tickers = list(self.base_prices.keys())
        selected_tickers = random.sample(
            available_tickers, min(count, len(available_tickers)))

        demo_tickers = []
        for ticker in selected_tickers:
            base_price = self.base_prices[ticker]

            # Generate realistic price variation (-5% to +5%)
            price_variation = random.uniform(-0.05, 0.05)
            current_price = base_price * (1 + price_variation)

            # Generate realistic change percentage (-3% to +3%)
            change_percent = random.uniform(-3.0, 3.0)

            # Generate realistic market cap (rough estimates)
            market_cap = self._estimate_market_cap(ticker, current_price)

            demo_tickers.append({
                "symbol": ticker,
                "name": self.company_names[ticker],
                "price": round(current_price, 2),
                "change": round(change_percent, 2),
                "market_cap": market_cap,
                "timestamp": datetime.now().isoformat(),
                "is_demo": True  # Flag to indicate this is demo data
            })

        return demo_tickers

    def get_demo_stock_data(self, ticker: str) -> Dict:
        """Get comprehensive demo stock data for a specific ticker"""
        ticker_upper = ticker.upper()

        if ticker_upper not in self.base_prices:
            # Generate random data for unknown tickers
            base_price = random.uniform(10, 1000)
            company_name = f"{ticker_upper} Corporation"
        else:
            base_price = self.base_prices[ticker_upper]
            company_name = self.company_names[ticker_upper]

        # Generate realistic variations
        price_variation = random.uniform(-0.05, 0.05)
        current_price = base_price * (1 + price_variation)

        # Generate mock financial data
        fcf_data = self._generate_fcf_data(ticker_upper, current_price)

        return {
            'ticker': ticker_upper,
            'company_name': company_name,
            'current_price': round(current_price, 2),
            'market_cap': self._estimate_market_cap(ticker_upper, current_price),
            'shares_outstanding': self._estimate_shares_outstanding(ticker_upper),
            'fcf_data': fcf_data,
            'fcf_growth_rate': random.uniform(0.02, 0.15),  # 2-15% growth
            'financials': self._generate_mock_financials(ticker_upper),
            'balance_sheet': self._generate_mock_balance_sheet(ticker_upper),
            'cashflow': self._generate_mock_cashflow(ticker_upper),
            'price_history': self._generate_price_history(ticker_upper, current_price),
            'info': {
                'sector': self._get_sector(ticker_upper),
                'industry': self._get_industry(ticker_upper),
                'employee_count': random.randint(1000, 500000)
            },
            'data_source': 'Demo Data (API Limit Exceeded)',
            'is_demo': True
        }

    def _estimate_market_cap(self, ticker: str, price: float) -> int:
        """Estimate market cap based on ticker and price"""
        # Rough estimates for major companies
        market_caps = {
            "AAPL": 3.8e12, "MSFT": 3.2e12, "GOOGL": 1.8e12,
            "AMZN": 1.9e12, "TSLA": 7.9e11, "META": 1.3e12,
            "NVDA": 4.5e12, "NFLX": 2.1e11, "AMD": 2.3e11, "INTC": 1.8e11
        }

        if ticker in market_caps:
            # Add some variation
            variation = random.uniform(0.8, 1.2)
            return int(market_caps[ticker] * variation)

        # Estimate based on price for unknown tickers
        estimated_shares = random.randint(100e6, 10e9)  # 100M to 10B shares
        return int(price * estimated_shares)

    def _estimate_shares_outstanding(self, ticker: str) -> int:
        """Estimate shares outstanding based on ticker"""
        # Rough estimates for major companies
        shares_estimates = {
            "AAPL": 15.4e9, "MSFT": 7.4e9, "GOOGL": 12.6e9,
            "AMZN": 10.6e9, "TSLA": 3.2e9, "META": 2.5e9,
            "NVDA": 2.4e9, "NFLX": 430e6, "AMD": 1.6e9, "INTC": 4.1e9
        }

        if ticker in shares_estimates:
            return int(shares_estimates[ticker])

        return random.randint(100e6, 10e9)  # Default range

    def _generate_fcf_data(self, ticker: str, current_price: float) -> List[float]:
        """Generate realistic free cash flow data"""
        # Base FCF estimate (roughly 5-15% of market cap)
        estimated_market_cap = self._estimate_market_cap(ticker, current_price)
        base_fcf = estimated_market_cap * \
            random.uniform(0.05, 0.15) / 4  # Quarterly

        # Generate 4 quarters of data with some growth/variation
        fcf_data = []
        for i in range(4):
            variation = random.uniform(0.8, 1.3)
            quarterly_fcf = base_fcf * variation * \
                (1.05 ** i)  # Slight growth trend
            fcf_data.append(quarterly_fcf)

        return [round(fcf, 2) for fcf in fcf_data]

    def _generate_mock_financials(self, ticker: str) -> Dict:
        """Generate mock income statement data"""
        return {
            'revenue': random.randint(10e9, 500e9),
            'net_income': random.randint(1e9, 50e9),
            'gross_profit': random.randint(5e9, 250e9),
            'operating_income': random.randint(2e9, 100e9),
            'total_expenses': random.randint(5e9, 200e9)
        }

    def _generate_mock_balance_sheet(self, ticker: str) -> Dict:
        """Generate mock balance sheet data"""
        return {
            'total_assets': random.randint(50e9, 1000e9),
            'total_liabilities': random.randint(10e9, 500e9),
            'shareholders_equity': random.randint(20e9, 600e9),
            'cash_and_equivalents': random.randint(1e9, 100e9),
            'total_debt': random.randint(1e9, 200e9)
        }

    def _generate_mock_cashflow(self, ticker: str) -> Dict:
        """Generate mock cash flow data"""
        return {
            'operating_cash_flow': random.randint(5e9, 100e9),
            'investing_cash_flow': random.randint(-50e9, -1e9),
            'financing_cash_flow': random.randint(-20e9, 20e9),
            'free_cash_flow': random.randint(1e9, 80e9)
        }

    def _generate_price_history(self, ticker: str, current_price: float) -> List[Dict]:
        """Generate mock price history for charts"""
        history = []
        for days_ago in range(30, 0, -1):  # Last 30 days
            date = datetime.now() - timedelta(days=days_ago)
            # Add some random walk to price
            price_change = random.uniform(-0.02, 0.02)  # ±2% daily change
            current_price *= (1 + price_change)

            history.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': round(current_price, 2),
                'volume': random.randint(1000000, 100000000)
            })

        return history

    def _get_sector(self, ticker: str) -> str:
        """Get sector for ticker"""
        sectors = {
            "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
            "AMZN": "Consumer Discretionary", "TSLA": "Consumer Discretionary",
            "META": "Technology", "NVDA": "Technology", "NFLX": "Communication Services",
            "AMD": "Technology", "INTC": "Technology"
        }
        return sectors.get(ticker, "Technology")

    def _get_industry(self, ticker: str) -> str:
        """Get industry for ticker"""
        industries = {
            "AAPL": "Consumer Electronics", "MSFT": "Software", "GOOGL": "Internet Content & Information",
            "AMZN": "Internet Retail", "TSLA": "Auto Manufacturers",
            "META": "Social Media", "NVDA": "Semiconductors", "NFLX": "Entertainment",
            "AMD": "Semiconductors", "INTC": "Semiconductors"
        }
        return industries.get(ticker, "Technology")


# Global instance
demo_data_generator = DemoDataGenerator()
