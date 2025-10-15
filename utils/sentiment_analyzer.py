"""
Sentiment analysis module using Hugging Face transformers
Analyzes financial news headlines for sentiment classification
"""

import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')


class SentimentAnalyzer:
    """Main sentiment analysis class for financial news"""

    def __init__(self):
        self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        self.pipeline = None
        self.tokenizer = None
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the Hugging Face sentiment analysis model"""
        try:
            # Use pipeline for easy sentiment analysis
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                return_all_scores=True,
                device=0 if torch.cuda.is_available() else -1
            )

            # Also load tokenizer and model separately for more control
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name)

            if torch.cuda.is_available():
                self.model = self.model.cuda()

        except Exception as e:
            print(f"Error initializing sentiment model: {str(e)}")
            # Fallback to a simpler approach if model loading fails
            self.pipeline = None

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment results
        """
        if not self.pipeline:
            return self._fallback_sentiment(text)

        try:
            # Clean and truncate text if too long
            cleaned_text = self._clean_text(text)
            if len(cleaned_text) > 512:  # Model limit
                cleaned_text = cleaned_text[:512]

            # Get sentiment scores
            results = self.pipeline(cleaned_text)

            # Extract positive and negative scores
            positive_score = 0
            negative_score = 0

            for result in results[0]:
                if result['label'] == 'POSITIVE':
                    positive_score = result['score']
                elif result['label'] == 'NEGATIVE':
                    negative_score = result['score']

            # Determine overall sentiment
            if positive_score > negative_score:
                sentiment = 'positive'
                confidence = positive_score
            else:
                sentiment = 'negative'
                confidence = negative_score

            # Check if confidence is low (neutral zone)
            if confidence < 0.6:
                sentiment = 'neutral'
                confidence = 1 - confidence

            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'positive_score': positive_score,
                'negative_score': negative_score,
                'text': cleaned_text
            }

        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return self._fallback_sentiment(text)

    def analyze_news_batch(self, news_articles: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for a batch of news articles

        Args:
            news_articles: List of news article dictionaries

        Returns:
            List of articles with sentiment analysis results
        """
        analyzed_articles = []

        for article in news_articles:
            # Combine title and summary for analysis
            text_to_analyze = f"{article.get('title', '')} {article.get('summary', '')}"

            sentiment_result = self.analyze_sentiment(text_to_analyze)

            # Add sentiment results to article
            analyzed_article = article.copy()
            analyzed_article.update(sentiment_result)
            analyzed_articles.append(analyzed_article)

        return analyzed_articles

    def get_sentiment_summary(self, analyzed_articles: List[Dict]) -> Dict:
        """
        Generate summary statistics for sentiment analysis

        Args:
            analyzed_articles: List of analyzed articles

        Returns:
            Dictionary with sentiment summary
        """
        if not analyzed_articles:
            return {
                'total_articles': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'positive_percentage': 0,
                'negative_percentage': 0,
                'neutral_percentage': 0,
                'average_confidence': 0,
                'overall_sentiment': 'neutral'
            }

        total_articles = len(analyzed_articles)
        positive_count = sum(
            1 for article in analyzed_articles if article['sentiment'] == 'positive')
        negative_count = sum(
            1 for article in analyzed_articles if article['sentiment'] == 'negative')
        neutral_count = sum(
            1 for article in analyzed_articles if article['sentiment'] == 'neutral')

        # Calculate percentages
        positive_percentage = (positive_count / total_articles) * 100
        negative_percentage = (negative_count / total_articles) * 100
        neutral_percentage = (neutral_count / total_articles) * 100

        # Calculate average confidence
        average_confidence = sum(article['confidence']
                                 for article in analyzed_articles) / total_articles

        # Determine overall sentiment
        if positive_count > negative_count and positive_count > neutral_count:
            overall_sentiment = 'positive'
        elif negative_count > positive_count and negative_count > neutral_count:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'

        return {
            'total_articles': total_articles,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_percentage': positive_percentage,
            'negative_percentage': negative_percentage,
            'neutral_percentage': neutral_percentage,
            'average_confidence': average_confidence,
            'overall_sentiment': overall_sentiment
        }

    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis"""
        if not text:
            return ""

        # Basic text cleaning
        import re

        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)

        return text.strip()

    def _fallback_sentiment(self, text: str) -> Dict:
        """
        Fallback sentiment analysis using simple keyword matching
        Used when the main model fails to load
        """
        positive_keywords = [
            'bullish', 'positive', 'growth', 'increase', 'rise', 'gain', 'profit',
            'strong', 'outperform', 'buy', 'upgrade', 'beat', 'exceed', 'surge',
            'rally', 'optimistic', 'favorable', 'success', 'win', 'breakthrough'
        ]

        negative_keywords = [
            'bearish', 'negative', 'decline', 'decrease', 'fall', 'loss', 'drop',
            'weak', 'underperform', 'sell', 'downgrade', 'miss', 'disappoint',
            'crash', 'plunge', 'pessimistic', 'unfavorable', 'concern', 'risk',
            'warning', 'trouble', 'problem', 'crisis'
        ]

        text_lower = text.lower()

        positive_count = sum(
            1 for keyword in positive_keywords if keyword in text_lower)
        negative_count = sum(
            1 for keyword in negative_keywords if keyword in text_lower)

        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(0.8, 0.5 + (positive_count * 0.1))
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(0.8, 0.5 + (negative_count * 0.1))
        else:
            sentiment = 'neutral'
            confidence = 0.5

        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_score': positive_count / max(1, positive_count + negative_count),
            'negative_score': negative_count / max(1, positive_count + negative_count),
            'text': text
        }

    def get_sentiment_trends(self, analyzed_articles: List[Dict]) -> Dict:
        """
        Analyze sentiment trends over time (if timestamps available)

        Args:
            analyzed_articles: List of analyzed articles with timestamps

        Returns:
            Dictionary with trend analysis
        """
        if not analyzed_articles:
            return {}

        # Group articles by date (if available)
        from collections import defaultdict
        import datetime

        daily_sentiments = defaultdict(list)

        for article in analyzed_articles:
            try:
                if 'published' in article and article['published']:
                    # Parse date (simplified)
                    date_str = article['published'][:10]  # Get YYYY-MM-DD part
                    daily_sentiments[date_str].append(article['sentiment'])
            except:
                continue

        # Calculate daily sentiment scores
        trend_data = []
        for date, sentiments in daily_sentiments.items():
            positive_ratio = sentiments.count('positive') / len(sentiments)
            negative_ratio = sentiments.count('negative') / len(sentiments)
            neutral_ratio = sentiments.count('neutral') / len(sentiments)

            trend_data.append({
                'date': date,
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'neutral_ratio': neutral_ratio,
                'article_count': len(sentiments)
            })

        # Sort by date
        trend_data.sort(key=lambda x: x['date'])

        return {
            'daily_trends': trend_data,
            'trend_period': f"{trend_data[0]['date']} to {trend_data[-1]['date']}" if trend_data else "No data"
        }
