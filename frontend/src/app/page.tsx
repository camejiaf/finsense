'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, TrendingUp, Calculator, FileText, Download, ChevronDown, RefreshCw } from 'lucide-react';
import Link from 'next/link';

interface TrendingStock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  timestamp?: string;
}

export default function Home() {
  const [error, setError] = useState('');
  const [trendingStocks, setTrendingStocks] = useState<TrendingStock[]>([]);
  const [loadingTrending, setLoadingTrending] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch trending stocks
  const fetchTrendingStocks = async () => {
    setLoadingTrending(true);
    setError('');

    try {
      console.log('Fetching trending stocks from frontend...');

      // Simple fetch with timeout using Promise.race
      const fetchPromise = fetch('http://localhost:8000/api/tickers', {
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), 60000) // 60 second timeout
      );

      const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;
      console.log('Response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Received data:', data);
        setTrendingStocks(data.tickers || []);
        setLastUpdated(data.timestamp);

        // Check if any ticker has demo flag
        const hasDemoData = data.tickers?.some((ticker: any) => ticker.is_demo);
        setIsDemoMode(hasDemoData);
      } else {
        console.error('API response not ok:', response.status);
        setError('Failed to load stock data');
      }
    } catch (error) {
      console.error('Error fetching trending stocks:', error);
      if (error instanceof Error && error.message === 'Request timeout') {
        setError('Request timeout - please try again');
      } else {
        setError('Failed to connect to server');
      }
      // Set some default stocks if API fails
      setTrendingStocks([
        { "symbol": "AAPL", "name": "Apple Inc.", "price": 0, "change": 0, "timestamp": "" },
        { "symbol": "MSFT", "name": "Microsoft Corporation", "price": 0, "change": 0, "timestamp": "" },
        { "symbol": "GOOGL", "name": "Alphabet Inc. Class A", "price": 0, "change": 0, "timestamp": "" }
      ]);
    } finally {
      setLoadingTrending(false);
    }
  };

  // Load trending stocks on component mount
  useEffect(() => {
    fetchTrendingStocks();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);


  const handleStockSelect = (selectedStock: TrendingStock) => {
    console.log('Stock selected:', selectedStock);
    setShowDropdown(false);
    setError('');
    window.location.href = `/analysis/${selectedStock.symbol}`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-gray-900" />
              <h1 className="ml-2 text-2xl font-bold text-gray-900">FinSense</h1>
              {isDemoMode && (
                <div className="ml-3 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
                  DEMO MODE
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Professional Financial Analysis
          </h2>

          {/* Stock Selection */}
          <div className="max-w-2xl mx-auto mb-12">
            <div className="text-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Select a Stock to Analyze</h3>
              <p className="text-sm text-gray-600">Choose from trending stocks below</p>
              {isDemoMode && (
                <div className="mt-2 text-xs text-yellow-600 bg-yellow-50 px-3 py-1 rounded-full inline-block">
                  📊 Using demo data - prices rotate hourly to simulate market conditions
                </div>
              )}
            </div>

            {/* Trending Stocks Dropdown */}
            <div ref={dropdownRef} className="relative mb-4">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="w-full flex items-center justify-between px-4 py-3 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
              >
                <div className="flex items-center">
                  <TrendingUp className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-gray-700">
                    Select a trending stock
                  </span>
                </div>
                <div className="flex items-center">
                  <RefreshCw
                    className={`h-4 w-4 text-gray-400 mr-2 ${loadingTrending ? 'animate-spin' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      fetchTrendingStocks();
                    }}
                  />
                  <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
                </div>
              </button>

              {/* Dropdown Menu */}
              {showDropdown && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto overflow-x-hidden">
                  {trendingStocks.length > 0 ? (
                    trendingStocks.map((stock) => (
                      <button
                        key={stock.symbol}
                        onClick={() => handleStockSelect(stock)}
                        className="w-full px-4 py-3 text-left hover:bg-blue-50 focus:bg-blue-50 focus:outline-none border-b border-gray-100 last:border-b-0 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-gray-900">{stock.symbol}</div>
                            <div className="text-sm text-gray-600 truncate">{stock.name}</div>
                          </div>
                          <div className="text-right ml-4 flex-shrink-0">
                            <div className="font-medium text-gray-900">${stock.price.toFixed(2)}</div>
                            <div className={`text-sm ${stock.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}%
                            </div>
                          </div>
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="px-4 py-6 text-center text-gray-500">
                      {loadingTrending ? (
                        <>
                          <TrendingUp className="h-8 w-8 mx-auto mb-2 text-gray-300 animate-pulse" />
                          <p className="text-sm">Loading stock data...</p>
                          <p className="text-xs mt-1">This may take up to 60 seconds</p>
                        </>
                      ) : (
                        <>
                          <TrendingUp className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                          <p className="text-sm">No stocks available</p>
                          {error && <p className="text-xs mt-1 text-red-500">{error}</p>}
                        </>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>


            {/* Error Message */}
            {error && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Last Updated Info */}
            {lastUpdated && (
              <div className="mt-2 text-xs text-gray-500 text-center">
                Trending stocks updated: {new Date(lastUpdated).toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>



      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500">
            <p>FinSense - Professional Financial Analysis Platform</p>
            <p className="mt-2 text-sm">For investment professionals and financial analysts</p>
          </div>
        </div>
      </footer>
    </div>
  );
}