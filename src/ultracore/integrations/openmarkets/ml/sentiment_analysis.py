"""Sentiment Analysis for Market Intelligence"""
from transformers import pipeline

from ultracore.ml.base import BaseMLModel


class SentimentAnalyzer(BaseMLModel):
    """
    Analyze market sentiment from news and social media.
    
    Uses transformer models (BERT, FinBERT) for financial sentiment analysis.
    """
    
    def __init__(self):
        super().__init__(
            model_name="sentiment_analyzer",
            model_type="nlp",
            version="1.0.0"
        )
        # Use FinBERT for financial sentiment
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert"
        )
    
    async def analyze_text(self, text: str) -> Dict:
        """Analyze sentiment of financial text."""
        result = self.sentiment_pipeline(text)[0]
        
        return {
            "sentiment": result["label"],  # positive, negative, neutral
            "confidence": result["score"],
            "text": text
        }
    
    async def analyze_news(self, news_articles: List[str]) -> Dict:
        """Aggregate sentiment from multiple news articles."""
        sentiments = [await self.analyze_text(article) for article in news_articles]
        
        # Aggregate
        positive = sum(1 for s in sentiments if s["sentiment"] == "positive")
        negative = sum(1 for s in sentiments if s["sentiment"] == "negative")
        neutral = sum(1 for s in sentiments if s["sentiment"] == "neutral")
        
        return {
            "overall_sentiment": "bullish" if positive > negative else "bearish",
            "positive_ratio": positive / len(sentiments),
            "negative_ratio": negative / len(sentiments),
            "confidence": np.mean([s["confidence"] for s in sentiments])
        }
