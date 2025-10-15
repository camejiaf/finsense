"""
PDF report generator for FinSense DCF and sentiment analysis
Creates professional 1-page investment memos
"""

from fpdf import FPDF
from datetime import datetime
import io
from typing import Dict, List
import os


class PDFReportGenerator:
    """Generate PDF investment memos with DCF and sentiment analysis"""

    def __init__(self):
        self.pdf = None
        self.page_width = 210  # A4 width in mm
        self.margin = 20
        self.content_width = self.page_width - (2 * self.margin)

    def generate_investment_memo(self,
                                 stock_data: Dict,
                                 dcf_results: Dict,
                                 sentiment_summary: Dict,
                                 output_path: str = None) -> str:
        """
        Generate a comprehensive investment memo PDF

        Args:
            stock_data: Stock information and financial data
            dcf_results: DCF calculation results
            sentiment_summary: Sentiment analysis summary
            output_path: Optional custom output path

        Returns:
            Path to generated PDF file
        """

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ticker = stock_data.get('ticker', 'UNKNOWN')
            output_path = f"FinSense_Report_{ticker}_{timestamp}.pdf"

        # Initialize PDF
        self.pdf = FPDF()
        self.pdf.add_page()
        self.pdf.set_font('Arial', 'B', 16)

        # Header
        self._add_header(stock_data)

        # Executive Summary
        self._add_executive_summary(stock_data, dcf_results, sentiment_summary)

        # DCF Analysis Section
        self._add_dcf_analysis(dcf_results)

        # Sentiment Analysis Section
        self._add_sentiment_analysis(sentiment_summary)

        # Key Metrics Section
        self._add_key_metrics(stock_data, dcf_results)

        # Footer
        self._add_footer()

        # Save PDF
        self.pdf.output(output_path)

        return output_path

    def _add_header(self, stock_data: Dict):
        """Add report header with company information"""

        ticker = stock_data.get('ticker', 'N/A')
        company_name = stock_data.get('company_name', ticker)
        current_price = stock_data.get('current_price', 0)

        # Title
        self.pdf.set_font('Arial', 'B', 20)
        self.pdf.cell(0, 10, f"FinSense Investment Analysis", 0, 1, 'C')
        self.pdf.ln(5)

        # Company Info
        self.pdf.set_font('Arial', 'B', 16)
        self.pdf.cell(0, 8, f"{company_name} ({ticker})", 0, 1, 'C')

        self.pdf.set_font('Arial', '', 12)
        current_price_str = f"${current_price:.2f}" if current_price > 0 else "N/A"
        self.pdf.cell(0, 6, f"Current Price: {current_price_str}", 0, 1, 'C')

        # Report Date
        report_date = datetime.now().strftime("%B %d, %Y")
        self.pdf.cell(0, 6, f"Report Date: {report_date}", 0, 1, 'C')

        self.pdf.ln(10)

        # Horizontal line
        self.pdf.line(self.margin, self.pdf.get_y(),
                      self.page_width - self.margin, self.pdf.get_y())
        self.pdf.ln(8)

    def _add_executive_summary(self, stock_data: Dict, dcf_results: Dict, sentiment_summary: Dict):
        """Add executive summary section"""

        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 8, "Executive Summary", 0, 1)
        self.pdf.ln(2)

        self.pdf.set_font('Arial', '', 10)

        # DCF Summary
        if dcf_results and 'base_case_valuation' in dcf_results:
            dcf_price = dcf_results['base_case_valuation'].get(
                'equity_value_per_share', 0)
            current_price = stock_data.get('current_price', 0)

            if current_price > 0 and dcf_price > 0:
                upside = ((dcf_price - current_price) / current_price) * 100
                recommendation = "BUY" if upside > 10 else "HOLD" if upside > -10 else "SELL"

                summary_text = f"""
DCF Analysis indicates an intrinsic value of ${dcf_price:.2f} per share, representing 
a {'{:.1f}%'.format(upside)} {'upside' if upside > 0 else 'downside'} from current levels. 
Recommendation: {recommendation}.
                """
            else:
                summary_text = "DCF analysis completed with available data. See detailed analysis below."
        else:
            summary_text = "DCF analysis in progress. Please review detailed calculations below."

        # Sentiment Summary
        if sentiment_summary and sentiment_summary.get('total_articles', 0) > 0:
            overall_sentiment = sentiment_summary.get(
                'overall_sentiment', 'neutral')
            positive_pct = sentiment_summary.get('positive_percentage', 0)

            sentiment_text = f"""
News sentiment analysis of {sentiment_summary['total_articles']} articles shows 
{overall_sentiment} sentiment with {positive_pct:.1f}% positive coverage.
            """
        else:
            sentiment_text = "News sentiment analysis completed. See detailed results below."

        # Combine summaries
        full_summary = summary_text.strip() + "\n\n" + sentiment_text.strip()

        # Write summary with proper line breaks
        lines = full_summary.split('\n')
        for line in lines:
            if line.strip():
                self.pdf.cell(0, 5, line.strip(), 0, 1)

        self.pdf.ln(8)

    def _add_dcf_analysis(self, dcf_results: Dict):
        """Add DCF analysis section"""

        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 8, "DCF Valuation Analysis", 0, 1)
        self.pdf.ln(2)

        if not dcf_results or 'base_case_valuation' not in dcf_results:
            self.pdf.set_font('Arial', '', 10)
            self.pdf.cell(0, 5, "DCF analysis data not available.", 0, 1)
            self.pdf.ln(5)
            return

        base_case = dcf_results['base_case_valuation']
        monte_carlo = dcf_results.get('monte_carlo_results', {})
        assumptions = dcf_results.get('assumptions', {})

        self.pdf.set_font('Arial', '', 10)

        # Key DCF Metrics
        intrinsic_value = base_case.get('equity_value_per_share', 0)
        enterprise_value = base_case.get('enterprise_value', 0)

        self.pdf.cell(
            0, 5, f"Intrinsic Value per Share: ${intrinsic_value:.2f}", 0, 1)
        self.pdf.cell(
            0, 5, f"Enterprise Value: ${enterprise_value/1e9:.2f}B", 0, 1)

        # Monte Carlo Results
        if monte_carlo:
            mean_val = monte_carlo.get('mean_valuation', 0)
            std_val = monte_carlo.get('std_valuation', 0)
            p5_val = monte_carlo.get('percentile_5', 0)
            p95_val = monte_carlo.get('percentile_95', 0)

            self.pdf.cell(
                0, 5, f"Monte Carlo Mean: ${mean_val:.2f} (±${std_val:.2f})", 0, 1)
            self.pdf.cell(
                0, 5, f"5th-95th Percentile Range: ${p5_val:.2f} - ${p95_val:.2f}", 0, 1)

        # Key Assumptions
        if assumptions:
            growth_rate = assumptions.get('fcf_growth_rate', 0) * 100
            wacc = assumptions.get('wacc', 0) * 100
            terminal_growth = assumptions.get('terminal_growth', 0) * 100

            self.pdf.cell(0, 5, f"Key Assumptions:", 0, 1)
            self.pdf.cell(10, 5, "", 0, 0)  # Indent
            self.pdf.cell(0, 5, f"FCF Growth Rate: {growth_rate:.1f}%", 0, 1)
            self.pdf.cell(10, 5, "", 0, 0)  # Indent
            self.pdf.cell(0, 5, f"WACC: {wacc:.1f}%", 0, 1)
            self.pdf.cell(10, 5, "", 0, 0)  # Indent
            self.pdf.cell(
                0, 5, f"Terminal Growth: {terminal_growth:.1f}%", 0, 1)

        self.pdf.ln(8)

    def _add_sentiment_analysis(self, sentiment_summary: Dict):
        """Add sentiment analysis section"""

        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 8, "News Sentiment Analysis", 0, 1)
        self.pdf.ln(2)

        if not sentiment_summary or sentiment_summary.get('total_articles', 0) == 0:
            self.pdf.set_font('Arial', '', 10)
            self.pdf.cell(0, 5, "No news sentiment data available.", 0, 1)
            self.pdf.ln(5)
            return

        self.pdf.set_font('Arial', '', 10)

        # Sentiment Breakdown
        total = sentiment_summary.get('total_articles', 0)
        positive = sentiment_summary.get('positive_count', 0)
        negative = sentiment_summary.get('negative_count', 0)
        neutral = sentiment_summary.get('neutral_count', 0)

        self.pdf.cell(0, 5, f"Total Articles Analyzed: {total}", 0, 1)
        self.pdf.cell(
            0, 5, f"Positive: {positive} ({sentiment_summary.get('positive_percentage', 0):.1f}%)", 0, 1)
        self.pdf.cell(
            0, 5, f"Negative: {negative} ({sentiment_summary.get('negative_percentage', 0):.1f}%)", 0, 1)
        self.pdf.cell(
            0, 5, f"Neutral: {neutral} ({sentiment_summary.get('neutral_percentage', 0):.1f}%)", 0, 1)

        # Overall Sentiment
        overall_sentiment = sentiment_summary.get(
            'overall_sentiment', 'neutral')
        avg_confidence = sentiment_summary.get('average_confidence', 0)

        self.pdf.cell(
            0, 5, f"Overall Sentiment: {overall_sentiment.title()}", 0, 1)
        self.pdf.cell(0, 5, f"Average Confidence: {avg_confidence:.1%}", 0, 1)

        self.pdf.ln(8)

    def _add_key_metrics(self, stock_data: Dict, dcf_results: Dict):
        """Add key financial metrics section"""

        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 8, "Key Financial Metrics", 0, 1)
        self.pdf.ln(2)

        self.pdf.set_font('Arial', '', 10)

        # Basic Metrics
        current_price = stock_data.get('current_price', 0)
        market_cap = stock_data.get('market_cap', 0)

        if current_price > 0:
            self.pdf.cell(
                0, 5, f"Current Stock Price: ${current_price:.2f}", 0, 1)

        if market_cap > 0:
            self.pdf.cell(0, 5, f"Market Cap: ${market_cap/1e9:.2f}B", 0, 1)

        # DCF Metrics
        if dcf_results and 'base_case_valuation' in dcf_results:
            dcf_price = dcf_results['base_case_valuation'].get(
                'equity_value_per_share', 0)

            if current_price > 0 and dcf_price > 0:
                upside = ((dcf_price - current_price) / current_price) * 100
                self.pdf.cell(
                    0, 5, f"DCF vs Current Price: {'{:.1f}%'.format(upside)} {'upside' if upside > 0 else 'downside'}", 0, 1)

        # FCF Information
        fcf_data = stock_data.get('fcf_data', [])
        if fcf_data:
            current_fcf = fcf_data[0] if fcf_data[0] > 0 else max(fcf_data)
            self.pdf.cell(
                0, 5, f"Latest Free Cash Flow: ${current_fcf/1e9:.2f}B", 0, 1)

        fcf_growth = stock_data.get('fcf_growth_rate', 0)
        if fcf_growth != 0:
            self.pdf.cell(
                0, 5, f"Historical FCF Growth: {fcf_growth*100:.1f}%", 0, 1)

        self.pdf.ln(8)

    def _add_footer(self):
        """Add report footer"""

        # Horizontal line
        current_y = self.pdf.get_y()
        self.pdf.line(self.margin, current_y,
                      self.page_width - self.margin, current_y)
        self.pdf.ln(5)

        # Footer text
        self.pdf.set_font('Arial', '', 8)
        self.pdf.cell(
            0, 4, "Generated by FinSense - AI-Powered DCF & Sentiment Dashboard", 0, 1, 'C')
        self.pdf.cell(
            0, 4, "This report is for informational purposes only and not financial advice.", 0, 1, 'C')

        # Page number
        self.pdf.cell(0, 4, f"Page 1 of 1", 0, 1, 'C')

    def generate_simple_report(self,
                               ticker: str,
                               current_price: float,
                               dcf_price: float,
                               sentiment_summary: Dict,
                               output_path: str = None) -> str:
        """
        Generate a simplified 1-page report for quick analysis

        Args:
            ticker: Stock ticker symbol
            current_price: Current stock price
            dcf_price: DCF calculated price
            sentiment_summary: Sentiment analysis summary
            output_path: Optional output path

        Returns:
            Path to generated PDF
        """

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"FinSense_QuickReport_{ticker}_{timestamp}.pdf"

        # Initialize PDF
        self.pdf = FPDF()
        self.pdf.add_page()

        # Header
        self.pdf.set_font('Arial', 'B', 18)
        self.pdf.cell(0, 10, f"FinSense Quick Analysis: {ticker}", 0, 1, 'C')
        self.pdf.ln(10)

        # Price Comparison
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 8, "Price Analysis", 0, 1)

        self.pdf.set_font('Arial', '', 12)
        self.pdf.cell(0, 6, f"Current Price: ${current_price:.2f}", 0, 1)
        self.pdf.cell(0, 6, f"DCF Value: ${dcf_price:.2f}", 0, 1)

        if current_price > 0 and dcf_price > 0:
            upside = ((dcf_price - current_price) / current_price) * 100
            recommendation = "BUY" if upside > 10 else "HOLD" if upside > -10 else "SELL"

            self.pdf.set_font('Arial', 'B', 12)
            self.pdf.cell(0, 6, f"Recommendation: {recommendation}", 0, 1)
            self.pdf.set_font('Arial', '', 12)
            self.pdf.cell(
                0, 6, f"Upside/Downside: {'{:.1f}%'.format(upside)}", 0, 1)

        self.pdf.ln(10)

        # Sentiment Summary
        if sentiment_summary and sentiment_summary.get('total_articles', 0) > 0:
            self.pdf.set_font('Arial', 'B', 14)
            self.pdf.cell(0, 8, "News Sentiment", 0, 1)

            self.pdf.set_font('Arial', '', 12)
            overall_sentiment = sentiment_summary.get(
                'overall_sentiment', 'neutral')
            positive_pct = sentiment_summary.get('positive_percentage', 0)

            self.pdf.cell(
                0, 6, f"Overall Sentiment: {overall_sentiment.title()}", 0, 1)
            self.pdf.cell(
                0, 6, f"Positive Coverage: {positive_pct:.1f}%", 0, 1)
            self.pdf.cell(
                0, 6, f"Articles Analyzed: {sentiment_summary.get('total_articles', 0)}", 0, 1)

        # Footer
        self.pdf.ln(20)
        self.pdf.set_font('Arial', '', 8)
        self.pdf.cell(
            0, 4, "Generated by FinSense - AI-Powered Investment Analysis", 0, 1, 'C')
        self.pdf.cell(
            0, 4, "For informational purposes only. Not financial advice.", 0, 1, 'C')

        # Save PDF
        self.pdf.output(output_path)

        return output_path
