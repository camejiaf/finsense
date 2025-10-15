"""
Plotly visualization module for FinSense DCF and sentiment analysis
Creates interactive charts for the Streamlit dashboard
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List
import colorsys


class FinSenseVisualizations:
    """Create interactive visualizations for financial analysis"""

    def __init__(self):
        # Modern color palette - blue-gray theme
        self.colors = {
            'primary': '#2E86AB',      # Blue
            'secondary': '#A23B72',    # Deep pink
            'accent': '#F18F01',       # Orange
            'success': '#C73E1D',      # Red
            'neutral': '#6C757D',      # Gray
            'light': '#F8F9FA',        # Off-white
            'dark': '#212529'          # Dark gray
        }

        # Chart styling
        self.chart_style = {
            'font_family': 'Arial, sans-serif',
            'font_size': 12,
            'title_font_size': 16,
            'margin': dict(l=50, r=50, t=60, b=50),
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white'
        }

    def create_valuation_histogram(self, monte_carlo_results: Dict, current_price: float = 0) -> go.Figure:
        """
        Create Monte Carlo valuation distribution histogram

        Args:
            monte_carlo_results: Monte Carlo simulation results
            current_price: Current stock price for comparison

        Returns:
            Plotly figure object
        """

        if not monte_carlo_results or 'all_valuations' not in monte_carlo_results:
            # Return empty chart if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No Monte Carlo data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=self.colors['neutral'])
            )
            fig.update_layout(**self.chart_style, height=400)
            return fig

        valuations = monte_carlo_results['all_valuations']
        mean_val = monte_carlo_results.get('mean_valuation', 0)
        std_val = monte_carlo_results.get('std_valuation', 0)

        # Create histogram
        fig = go.Figure()

        # Main histogram
        fig.add_trace(go.Histogram(
            x=valuations,
            nbinsx=50,
            name='Valuation Distribution',
            marker_color=self.colors['primary'],
            opacity=0.7,
            hovertemplate='<b>Price Range:</b> %{x}<br>' +
            '<b>Frequency:</b> %{y}<extra></extra>'
        ))

        # Add mean line
        if mean_val > 0:
            fig.add_vline(
                x=mean_val,
                line_dash="dash",
                line_color=self.colors['accent'],
                annotation_text=f"Mean: ${mean_val:.2f}",
                annotation_position="top"
            )

        # Add current price line if provided
        if current_price > 0:
            fig.add_vline(
                x=current_price,
                line_dash="dot",
                line_color=self.colors['success'],
                annotation_text=f"Current: ${current_price:.2f}",
                annotation_position="top"
            )

        # Add percentile lines
        p5 = monte_carlo_results.get('percentile_5', 0)
        p95 = monte_carlo_results.get('percentile_95', 0)

        if p5 > 0:
            fig.add_vline(
                x=p5,
                line_dash="dashdot",
                line_color=self.colors['neutral'],
                line_width=1,
                annotation_text=f"5th %ile: ${p5:.2f}",
                annotation_position="bottom"
            )

        if p95 > 0:
            fig.add_vline(
                x=p95,
                line_dash="dashdot",
                line_color=self.colors['neutral'],
                line_width=1,
                annotation_text=f"95th %ile: ${p95:.2f}",
                annotation_position="bottom"
            )

        # Update layout
        fig.update_layout(
            title=dict(
                text="Monte Carlo Valuation Distribution",
                font=dict(
                    size=self.chart_style['title_font_size'], color=self.colors['dark'])
            ),
            xaxis_title="Intrinsic Value per Share ($)",
            yaxis_title="Frequency",
            showlegend=False,
            **self.chart_style,
            height=500
        )

        # Add statistics box
        stats_text = f"""
        <b>Statistics:</b><br>
        Mean: ${mean_val:.2f}<br>
        Std Dev: ${std_val:.2f}<br>
        5th %ile: ${p5:.2f}<br>
        95th %ile: ${p95:.2f}
        """

        fig.add_annotation(
            text=stats_text,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            showarrow=False,
            align="left",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=self.colors['neutral'],
            borderwidth=1,
            font=dict(size=10)
        )

        return fig

    def create_sentiment_chart(self, sentiment_summary: Dict) -> go.Figure:
        """
        Create sentiment analysis bar chart

        Args:
            sentiment_summary: Sentiment analysis summary

        Returns:
            Plotly figure object
        """

        if not sentiment_summary or sentiment_summary.get('total_articles', 0) == 0:
            # Return empty chart if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No sentiment data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=self.colors['neutral'])
            )
            fig.update_layout(**self.chart_style, height=400)
            return fig

        # Prepare data
        sentiments = ['Positive', 'Neutral', 'Negative']
        counts = [
            sentiment_summary.get('positive_count', 0),
            sentiment_summary.get('neutral_count', 0),
            sentiment_summary.get('negative_count', 0)
        ]
        percentages = [
            sentiment_summary.get('positive_percentage', 0),
            sentiment_summary.get('neutral_percentage', 0),
            sentiment_summary.get('negative_percentage', 0)
        ]

        # Color mapping
        colors = [self.colors['success'],
                  self.colors['neutral'], self.colors['secondary']]

        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=sentiments,
                y=counts,
                text=[f"{count}<br>({pct:.1f}%)" for count,
                      pct in zip(counts, percentages)],
                textposition='auto',
                marker_color=colors,
                hovertemplate='<b>%{x}</b><br>' +
                             'Count: %{y}<br>' +
                             'Percentage: %{text}<extra></extra>'
            )
        ])

        # Update layout
        fig.update_layout(
            title=dict(
                text="News Sentiment Distribution",
                font=dict(
                    size=self.chart_style['title_font_size'], color=self.colors['dark'])
            ),
            xaxis_title="Sentiment",
            yaxis_title="Number of Articles",
            showlegend=False,
            **self.chart_style,
            height=400
        )

        # Add overall sentiment indicator
        overall_sentiment = sentiment_summary.get(
            'overall_sentiment', 'neutral').title()
        avg_confidence = sentiment_summary.get('average_confidence', 0)

        stats_text = f"""
        <b>Overall Sentiment:</b> {overall_sentiment}<br>
        <b>Average Confidence:</b> {avg_confidence:.1%}<br>
        <b>Total Articles:</b> {sentiment_summary.get('total_articles', 0)}
        """

        fig.add_annotation(
            text=stats_text,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            showarrow=False,
            align="left",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=self.colors['neutral'],
            borderwidth=1,
            font=dict(size=10)
        )

        return fig

    def create_dcf_breakdown_chart(self, dcf_results: Dict) -> go.Figure:
        """
        Create DCF valuation breakdown pie chart

        Args:
            dcf_results: DCF calculation results

        Returns:
            Plotly figure object
        """

        if not dcf_results or 'base_case_valuation' not in dcf_results:
            # Return empty chart if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No DCF data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=self.colors['neutral'])
            )
            fig.update_layout(**self.chart_style, height=400)
            return fig

        base_case = dcf_results['base_case_valuation']
        pv_explicit = base_case.get('pv_explicit_period', 0)
        pv_terminal = base_case.get('pv_terminal_value', 0)
        enterprise_value = base_case.get('enterprise_value', 0)

        if enterprise_value == 0:
            # Return empty chart if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No DCF data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=self.colors['neutral'])
            )
            fig.update_layout(**self.chart_style, height=400)
            return fig

        # Prepare data
        labels = ['Present Value of<br>Explicit Period',
                  'Present Value of<br>Terminal Value']
        values = [pv_explicit, pv_terminal]
        colors = [self.colors['primary'], self.colors['accent']]

        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hovertemplate='<b>%{label}</b><br>' +
            'Value: $%{value:,.0f}<br>' +
            'Percentage: %{percent}<extra></extra>',
            textinfo='label+percent',
            textfont_size=12
        )])

        # Update layout
        fig.update_layout(
            title=dict(
                text="DCF Valuation Breakdown",
                font=dict(
                    size=self.chart_style['title_font_size'], color=self.colors['dark'])
            ),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            ),
            **self.chart_style,
            height=400
        )

        # Add enterprise value annotation
        ev_text = f"<b>Total Enterprise Value:</b><br>${enterprise_value/1e9:.2f}B"

        fig.add_annotation(
            text=ev_text,
            xref="paper", yref="paper",
            x=0.5, y=0.02,
            showarrow=False,
            align="center",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=self.colors['neutral'],
            borderwidth=1,
            font=dict(size=12)
        )

        return fig

    def create_fcf_projection_chart(self, dcf_results: Dict) -> go.Figure:
        """
        Create FCF projection line chart

        Args:
            dcf_results: DCF calculation results

        Returns:
            Plotly figure object
        """

        if not dcf_results or 'base_case_valuation' not in dcf_results:
            # Return empty chart if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No FCF projection data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=self.colors['neutral'])
            )
            fig.update_layout(**self.chart_style, height=400)
            return fig

        base_case = dcf_results['base_case_valuation']
        fcf_projections = base_case.get('fcf_projections', [])
        pv_projections = base_case.get('pv_fcf_projections', [])

        if not fcf_projections:
            # Return empty chart if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No FCF projection data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=self.colors['neutral'])
            )
            fig.update_layout(**self.chart_style, height=400)
            return fig

        # Prepare data
        years = list(range(1, len(fcf_projections) + 1))

        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=1, cols=1,
            specs=[[{"secondary_y": True}]]
        )

        # FCF projections (primary y-axis)
        fig.add_trace(
            go.Scatter(
                x=years,
                y=[fcf/1e9 for fcf in fcf_projections],  # Convert to billions
                mode='lines+markers',
                name='Projected FCF',
                line=dict(color=self.colors['primary'], width=3),
                marker=dict(size=8),
                hovertemplate='<b>Year %{x}</b><br>' +
                'Projected FCF: $%{y:.2f}B<extra></extra>'
            ),
            secondary_y=False
        )

        # Present value of FCF (secondary y-axis)
        if pv_projections:
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=[pv/1e9 for pv in pv_projections],  # Convert to billions
                    mode='lines+markers',
                    name='Present Value FCF',
                    line=dict(
                        color=self.colors['accent'], width=3, dash='dash'),
                    marker=dict(size=8),
                    hovertemplate='<b>Year %{x}</b><br>' +
                    'PV of FCF: $%{y:.2f}B<extra></extra>'
                ),
                secondary_y=True
            )

        # Update layout
        fig.update_layout(
            title=dict(
                text="5-Year Free Cash Flow Projections",
                font=dict(
                    size=self.chart_style['title_font_size'], color=self.colors['dark'])
            ),
            xaxis_title="Year",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            **self.chart_style,
            height=400
        )

        # Update y-axes
        fig.update_yaxes(
            title_text="Projected FCF ($B)",
            secondary_y=False,
            titlefont_color=self.colors['primary']
        )
        fig.update_yaxes(
            title_text="Present Value FCF ($B)",
            secondary_y=True,
            titlefont_color=self.colors['accent']
        )

        return fig

    def create_sentiment_timeline(self, sentiment_trends: Dict) -> go.Figure:
        """
        Create sentiment timeline chart if trend data is available

        Args:
            sentiment_trends: Daily sentiment trend data

        Returns:
            Plotly figure object
        """

        if not sentiment_trends or 'daily_trends' not in sentiment_trends:
            # Return empty chart if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No sentiment timeline data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=self.colors['neutral'])
            )
            fig.update_layout(**self.chart_style, height=400)
            return fig

        daily_trends = sentiment_trends['daily_trends']

        if len(daily_trends) < 2:
            # Return empty chart if insufficient data
            fig = go.Figure()
            fig.add_annotation(
                text="Insufficient timeline data",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=self.colors['neutral'])
            )
            fig.update_layout(**self.chart_style, height=400)
            return fig

        # Prepare data
        dates = [trend['date'] for trend in daily_trends]
        positive_ratios = [trend['positive_ratio']
                           * 100 for trend in daily_trends]
        negative_ratios = [trend['negative_ratio']
                           * 100 for trend in daily_trends]
        neutral_ratios = [trend['neutral_ratio']
                          * 100 for trend in daily_trends]

        # Create stacked area chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=positive_ratios,
            mode='lines',
            name='Positive',
            line=dict(color=self.colors['success'], width=2),
            stackgroup='one',
            hovertemplate='<b>%{x}</b><br>' +
            'Positive: %{y:.1f}%<extra></extra>'
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=neutral_ratios,
            mode='lines',
            name='Neutral',
            line=dict(color=self.colors['neutral'], width=2),
            stackgroup='one',
            hovertemplate='<b>%{x}</b><br>' +
            'Neutral: %{y:.1f}%<extra></extra>'
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=negative_ratios,
            mode='lines',
            name='Negative',
            line=dict(color=self.colors['secondary'], width=2),
            stackgroup='one',
            hovertemplate='<b>%{x}</b><br>' +
            'Negative: %{y:.1f}%<extra></extra>'
        ))

        # Update layout
        fig.update_layout(
            title=dict(
                text="News Sentiment Timeline",
                font=dict(
                    size=self.chart_style['title_font_size'], color=self.colors['dark'])
            ),
            xaxis_title="Date",
            yaxis_title="Sentiment Percentage (%)",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            **self.chart_style,
            height=400
        )

        return fig
