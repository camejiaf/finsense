'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, TrendingUp, TrendingDown, Minus, Download, FileText, XCircle, DollarSign, Percent, BarChart3, ArrowUpRight, ArrowDownRight, Assessment, Scale } from 'lucide-react';
import Link from 'next/link';

interface StockData {
    ticker: string;
    company_name: string;
    current_price: number;
    market_cap: number;
    shares_outstanding: number;
    fcf_data: number[];
    fcf_growth_rate: number;
}

interface DCFResults {
    base_case: {
        equity_value_per_share: number;
        enterprise_value: number;
    };
    monte_carlo: {
        mean: number;
        p5: number;
        p95: number;
    };
    assumptions: {
        base_fcf: number;
        growth_rate: number;
        wacc: number;
        terminal_growth: number;
    };
}

export default function AnalysisPage() {
    const params = useParams();
    const router = useRouter();
    const ticker = params.ticker as string;

    const [loading, setLoading] = useState(false);
    const [stockData, setStockData] = useState<StockData | null>(null);
    const [dcfResults, setDcfResults] = useState<DCFResults | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [wacc, setWacc] = useState(10.0);
    const [terminalGrowth, setTerminalGrowth] = useState(2.5);
    const [monteCarloRuns, setMonteCarloRuns] = useState(1000);
    const [analysisHistory, setAnalysisHistory] = useState<any[]>([]);

    // Load analysis history from localStorage on component mount
    useEffect(() => {
        const savedHistory = localStorage.getItem('finsense_analysis_history');
        if (savedHistory) {
            try {
                setAnalysisHistory(JSON.parse(savedHistory));
            } catch (e) {
                console.error('Error parsing analysis history:', e);
            }
        }
    }, []);

    // Save analysis to localStorage
    const saveAnalysisToHistory = (analysisData: any) => {
        const newAnalysis = {
            ticker: ticker.toUpperCase(),
            timestamp: new Date().toISOString(),
            ...analysisData
        };

        const updatedHistory = [newAnalysis, ...analysisHistory.slice(0, 9)]; // Keep last 10 analyses
        setAnalysisHistory(updatedHistory);
        localStorage.setItem('finsense_analysis_history', JSON.stringify(updatedHistory));
    };

    // Validate ticker format
    const isValidTicker = (ticker: string) => {
        if (!ticker || typeof ticker !== 'string') return false;
        const cleanTicker = ticker.trim().toUpperCase();

        // Check length (1-5 characters typically)
        if (cleanTicker.length < 1 || cleanTicker.length > 5) return false;

        // Check if it contains only letters and numbers
        if (!/^[A-Z0-9]+$/.test(cleanTicker)) return false;

        // Check for common invalid patterns
        const invalidPatterns = [
            /^\d+$/, // Only numbers
            /^(AND|OR|NOT|FOR|THE|NEW|OLD)$/i, // Common English words
            /^(TEST|DEMO|SAMPLE)$/i, // Test words
        ];

        return !invalidPatterns.some(pattern => pattern.test(cleanTicker));
    };

    const runAnalysis = async () => {
        // Clear previous errors
        setError(null);

        // Validate ticker first
        if (!isValidTicker(ticker)) {
            setError(`Invalid ticker symbol: "${ticker}". Please enter a valid stock ticker (1-5 letters/numbers, e.g., AAPL, MSFT, GOOGL).`);
            return;
        }

        // Validate parameters
        if (wacc < 1 || wacc > 50) {
            setError('WACC must be between 1% and 50%.');
            return;
        }

        if (terminalGrowth < 0 || terminalGrowth > 10) {
            setError('Terminal Growth must be between 0% and 10%.');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/api/analyze/${ticker}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    growth_rate: 5.0 / 100, // Default growth rate
                    discount_rate: wacc / 100,
                    terminal_growth: terminalGrowth / 100,
                }),
            });

            if (response.ok) {
                const data = await response.json();

                // Validate response data
                if (!data.stock_data || !data.dcf_results) {
                    setError('Invalid response from server. Please try again.');
                    return;
                }

                // Check if stock data is valid
                if (!data.stock_data.company_name || data.stock_data.current_price === undefined) {
                    setError(`No data found for ticker "${ticker}". This ticker may not exist or may not be publicly traded.`);
                    return;
                }

                setStockData(data.stock_data);
                setDcfResults(data.dcf_results);

                // Save analysis to history
                saveAnalysisToHistory({
                    stock_data: data.stock_data,
                    dcf_results: data.dcf_results,
                    parameters: {
                        wacc: wacc / 100,
                        terminal_growth: terminalGrowth / 100,
                        growth_rate: 5.0 / 100
                    }
                });
            } else {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.detail || errorData.error || 'Analysis failed';

                if (response.status === 404) {
                    setError(`Ticker "${ticker}" not found. Please check the ticker symbol and try again.`);
                } else if (response.status === 429) {
                    setError('Too many requests. Please wait a moment and try again.');
                } else if (response.status >= 500) {
                    setError('Server error. Please try again later.');
                } else {
                    setError(`Analysis failed: ${errorMessage}`);
                }
            }
        } catch (error) {
            console.error('Error running analysis:', error);
            setError('Network error. Please check your connection and try again.');
        } finally {
            setLoading(false);
        }
    };

    const getRecommendation = (upside: number) => {
        if (upside > 10) return { action: 'BUY', color: 'text-green-600 bg-green-50', icon: TrendingUp };
        if (upside > -10) return { action: 'HOLD', color: 'text-yellow-600 bg-yellow-50', icon: Minus };
        return { action: 'SELL', color: 'text-red-600 bg-red-50', icon: TrendingDown };
    };

    const upside = stockData && dcfResults
        ? ((dcfResults.base_case.equity_value_per_share - stockData.current_price) / stockData.current_price) * 100
        : 0;

    const recommendation = getRecommendation(upside);

    // Export functions
    const exportToExcel = async () => {
        if (!stockData || !dcfResults) {
            alert('Please run an analysis first');
            return;
        }

        try {
            const response = await fetch('http://localhost:8000/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ticker: ticker.toUpperCase(),
                    format: 'excel',
                    data: {
                        stock_data: stockData,
                        dcf_results: dcfResults,
                        parameters: {
                            wacc: wacc / 100,
                            terminal_growth: terminalGrowth / 100,
                            growth_rate: 5.0 / 100
                        }
                    }
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `FinSense_Analysis_${ticker}_${new Date().toISOString().split('T')[0]}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                alert('Export failed. Please try again.');
            }
        } catch (error) {
            console.error('Export error:', error);
            alert('Export failed. Please try again.');
        }
    };

    const exportToPDF = async () => {
        if (!stockData || !dcfResults) {
            alert('Please run an analysis first');
            return;
        }

        try {
            const response = await fetch('http://localhost:8000/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ticker: ticker.toUpperCase(),
                    format: 'pdf',
                    data: {
                        stock_data: stockData,
                        dcf_results: dcfResults,
                        parameters: {
                            wacc: wacc / 100,
                            terminal_growth: terminalGrowth / 100,
                            growth_rate: 5.0 / 100
                        }
                    }
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `FinSense_Analysis_${ticker}_${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                alert('Export failed. Please try again.');
            }
        } catch (error) {
            console.error('Export error:', error);
            alert('Export failed. Please try again.');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center py-6">
                        <Link href="/" className="mr-4">
                            <ArrowLeft className="h-6 w-6 text-gray-600 hover:text-gray-900" />
                        </Link>
                        <div className="flex items-center">
                            <TrendingUp className="h-8 w-8 text-gray-900" />
                            <h1 className="ml-2 text-2xl font-bold text-gray-900">FinSense</h1>
                        </div>
                        <div className="ml-8">
                            <h2 className="text-xl font-semibold text-gray-700">{ticker}</h2>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Error Display */}
                {error && (
                    <div className="mb-8 bg-red-50 border border-red-200 rounded-lg p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <XCircle className="h-5 w-5 text-red-400" />
                            </div>
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-red-800">
                                    Analysis Error
                                </h3>
                                <div className="mt-2 text-sm text-red-700">
                                    <p>{error}</p>
                                </div>
                                <div className="mt-4">
                                    <button
                                        onClick={() => setError(null)}
                                        className="bg-red-100 text-red-800 px-3 py-2 rounded-md text-sm font-medium hover:bg-red-200"
                                    >
                                        Dismiss
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                    {/* Sidebar */}
                    <div className="lg:col-span-1">
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Parameters</h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        WACC (%)
                                    </label>
                                    <input
                                        type="number"
                                        value={wacc}
                                        onChange={(e) => setWacc(Number(e.target.value))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Terminal Growth (%)
                                    </label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={terminalGrowth}
                                        onChange={(e) => setTerminalGrowth(Number(e.target.value))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Monte Carlo Runs
                                    </label>
                                    <select
                                        value={monteCarloRuns}
                                        onChange={(e) => setMonteCarloRuns(Number(e.target.value))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    >
                                        <option value={1000}>1,000</option>
                                        <option value={2000}>2,000</option>
                                        <option value={5000}>5,000</option>
                                    </select>
                                </div>

                                <button
                                    onClick={runAnalysis}
                                    disabled={loading}
                                    className="w-full bg-gray-900 text-white py-2 px-4 rounded-md hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {loading ? 'Running Analysis...' : 'Run Analysis'}
                                </button>
                            </div>

                            {/* Analysis History */}
                            {analysisHistory.length > 0 && (
                                <div className="mt-6 pt-6 border-t border-gray-200">
                                    <h4 className="text-sm font-medium text-gray-700 mb-3">Recent Analyses</h4>
                                    <div className="space-y-2 max-h-40 overflow-y-auto">
                                        {analysisHistory.slice(0, 5).map((analysis, index) => (
                                            <div key={index} className="text-xs text-gray-600 p-2 bg-gray-50 rounded">
                                                <div className="font-medium">{analysis.ticker}</div>
                                                <div>{new Date(analysis.timestamp).toLocaleDateString()}</div>
                                                <div className="text-gray-500">
                                                    WACC: {(analysis.parameters?.wacc * 100).toFixed(1)}%
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Export Options */}
                            <div className="mt-6 pt-6 border-t border-gray-200">
                                <h4 className="text-sm font-medium text-gray-700 mb-3">Export</h4>
                                <div className="space-y-2">
                                    <button
                                        onClick={exportToExcel}
                                        disabled={!stockData || !dcfResults}
                                        className="w-full flex items-center justify-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <Download className="h-4 w-4 mr-2" />
                                        Excel Report
                                    </button>
                                    <button
                                        onClick={exportToPDF}
                                        disabled={!stockData || !dcfResults}
                                        className="w-full flex items-center justify-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <FileText className="h-4 w-4 mr-2" />
                                        PDF Report
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Main Content */}
                    <div className="lg:col-span-3">
                        {stockData && dcfResults ? (
                            <>
                                {/* Key Metrics */}
                                <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Metrics</h3>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <h4 className="text-sm font-medium text-gray-500 mb-3">Market Data</h4>
                                            <div className="space-y-3">
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">Current Price</span>
                                                    <span className="font-semibold">${stockData.current_price.toFixed(2)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">Market Cap</span>
                                                    <span className="font-semibold">${(stockData.market_cap / 1e9).toFixed(1)}B</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">Shares Outstanding</span>
                                                    <span className="font-semibold">{(stockData.shares_outstanding / 1e9).toFixed(1)}B</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div>
                                            <h4 className="text-sm font-medium text-gray-500 mb-3">DCF Valuation</h4>
                                            <div className="space-y-3">
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">DCF Value</span>
                                                    <span className="font-semibold">${dcfResults.base_case.equity_value_per_share.toFixed(2)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">Upside/Downside</span>
                                                    <span className={`font-semibold ${upside > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                        {upside > 0 ? '+' : ''}{upside.toFixed(1)}%
                                                    </span>
                                                </div>
                                                <div className="flex justify-between items-center">
                                                    <span className="text-gray-600">Recommendation</span>
                                                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${recommendation.color}`}>
                                                        <recommendation.icon className="inline h-4 w-4 mr-1" />
                                                        {recommendation.action}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* DCF Details */}
                                <div className="bg-white rounded-lg border border-gray-200 p-6">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">DCF Assumptions & Results</h3>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <h4 className="text-sm font-medium text-gray-500 mb-3">Key Assumptions</h4>
                                            <div className="space-y-3">
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">Base FCF</span>
                                                    <span className="font-semibold">${(dcfResults.assumptions.base_fcf / 1e9).toFixed(2)}B</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">FCF Growth Rate</span>
                                                    <span className="font-semibold">{(dcfResults.assumptions.growth_rate * 100).toFixed(1)}%</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">WACC</span>
                                                    <span className="font-semibold">{(dcfResults.assumptions.wacc * 100).toFixed(1)}%</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">Terminal Growth</span>
                                                    <span className="font-semibold">{(dcfResults.assumptions.terminal_growth * 100).toFixed(1)}%</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div>
                                            <h4 className="text-sm font-medium text-gray-500 mb-3">Valuation Results</h4>
                                            <div className="space-y-3">
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">Intrinsic Value</span>
                                                    <span className="font-semibold">${dcfResults.base_case.equity_value_per_share.toFixed(2)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">Enterprise Value</span>
                                                    <span className="font-semibold">${(dcfResults.base_case.enterprise_value / 1e9).toFixed(2)}B</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">Monte Carlo Mean</span>
                                                    <span className="font-semibold">${dcfResults.monte_carlo.mean.toFixed(2)}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600">5th-95th Percentile</span>
                                                    <span className="font-semibold">
                                                        ${dcfResults.monte_carlo.p5.toFixed(2)} - ${dcfResults.monte_carlo.p95.toFixed(2)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                                <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-gray-900 mb-2">Ready for Analysis</h3>
                                <p className="text-gray-600">Configure your parameters and click "Run Analysis" to begin.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

