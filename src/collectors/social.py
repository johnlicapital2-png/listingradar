import random
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import httpx
from bs4 import BeautifulSoup
import yaml
import os

from storage.db import TrendData, get_db

class SocialSignalsCollector:
    """
    Collects social media signals from Reddit and TikTok.
    Uses mock data for demonstration, with placeholders for real API integration.
    """
    
    def __init__(self, config_path="config.yaml"):
        self.config = self.load_config(config_path)
        self.reddit_enabled = self.config.get('social', {}).get('reddit', {}).get('enabled', False)
        self.tiktok_enabled = self.config.get('social', {}).get('tiktok', {}).get('enabled', False)
        self.use_mock = (
            self.config.get('social', {}).get('reddit', {}).get('mock_data', True) or
            self.config.get('social', {}).get('tiktok', {}).get('mock_data', True)
        )
        
        # E-commerce related subreddits to monitor
        self.ecommerce_subreddits = [
            'amazonFBA', 'dropshipping', 'ecommerce', 'entrepreneur',
            'smallbusiness', 'passive_income', 'onlinemarketing', 'shopify'
        ]
        
        # Common product-related keywords
        self.product_keywords = [
            'wireless earbuds', 'air fryer', 'yoga mat', 'protein powder',
            'face masks', 'hand sanitizer', 'phone case', 'bluetooth speaker',
            'coffee maker', 'resistance bands', 'essential oils', 'foam roller',
            'standing desk', 'ring light', 'water bottle', 'massage gun'
        ]
    
    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def generate_mock_reddit_data(self, keywords: List[str]) -> List[Dict]:
        """
        Generate mock Reddit mention data with realistic patterns.
        """
        reddit_data = []
        
        for keyword in keywords:
            # Simulate Reddit mentions with varying buzz levels
            mention_count = random.randint(0, 50)
            
            # Simulate sentiment (0.0 = negative, 0.5 = neutral, 1.0 = positive)
            # E-commerce discussions tend to be more analytical (neutral to positive)
            sentiment = random.uniform(0.3, 0.8)
            
            # Volume score based on mentions
            volume_score = min(100, mention_count * 2)
            
            reddit_data.append({
                'keyword': keyword,
                'platform': 'reddit',
                'volume_score': volume_score,
                'velocity_score': random.uniform(-10, 20),  # Rate of change in mentions
                'sentiment_score': sentiment,
                'timestamp': datetime.utcnow(),
                'raw_mentions': mention_count
            })
        
        return reddit_data
    
    def generate_mock_tiktok_data(self, keywords: List[str]) -> List[Dict]:
        """
        Generate mock TikTok trend data.
        """
        tiktok_data = []
        
        for keyword in keywords:
            # TikTok tends to have more viral, explosive trends
            base_views = random.randint(1000, 100000)
            
            # 20% chance of viral trend
            if random.random() < 0.2:
                base_views *= random.randint(5, 50)  # Viral multiplier
            
            # Volume score based on views
            volume_score = min(100, base_views / 1000)
            
            # TikTok sentiment tends to be more positive/enthusiastic
            sentiment = random.uniform(0.4, 0.9)
            
            tiktok_data.append({
                'keyword': keyword,
                'platform': 'tiktok',
                'volume_score': volume_score,
                'velocity_score': random.uniform(-5, 30),  # TikTok can spike fast
                'sentiment_score': sentiment,
                'timestamp': datetime.utcnow(),
                'raw_views': base_views
            })
        
        return tiktok_data
    
    def scrape_reddit_mentions(self, keyword: str, subreddits: List[str] = None) -> Dict:
        """
        Scrape Reddit for product mentions (placeholder implementation).
        In production, use Reddit API or PRAW library.
        """
        if self.use_mock or not self.reddit_enabled:
            return self.generate_mock_reddit_data([keyword])[0]
        
        # Placeholder for real Reddit scraping
        # In production, you'd use:
        # 1. Reddit API (requires API key)
        # 2. PRAW (Python Reddit API Wrapper) 
        # 3. Pushshift API for historical data
        
        subreddits = subreddits or self.ecommerce_subreddits
        total_mentions = 0
        total_sentiment = 0
        
        try:
            # This is a placeholder - implement actual Reddit API calls
            # Example with Reddit API:
            # import praw
            # reddit = praw.Reddit(...)
            # for subreddit in subreddits:
            #     for submission in reddit.subreddit(subreddit).search(keyword, limit=100):
            #         # Analyze submission and comments
            #         # Calculate sentiment, count mentions
            
            # For now, return mock data
            return self.generate_mock_reddit_data([keyword])[0]
            
        except Exception as e:
            print(f"Error scraping Reddit for '{keyword}': {e}")
            return self.generate_mock_reddit_data([keyword])[0]
    
    def scrape_tiktok_trends(self, keyword: str) -> Dict:
        """
        Scrape TikTok for trend data (placeholder implementation).
        In production, use TikTok API or unofficial scraping methods.
        """
        if self.use_mock or not self.tiktok_enabled:
            return self.generate_mock_tiktok_data([keyword])[0]
        
        # Placeholder for real TikTok scraping
        # In production, you'd use:
        # 1. TikTok for Business API (limited access)
        # 2. Unofficial TikTok API libraries
        # 3. Web scraping with proper headers/proxies
        
        try:
            # This is a placeholder - implement actual TikTok data collection
            # Example scraping approach:
            # headers = {'User-Agent': '...'}
            # url = f'https://www.tiktok.com/search?q={keyword}'
            # response = httpx.get(url, headers=headers)
            # Parse JSON/HTML for video counts, engagement
            
            return self.generate_mock_tiktok_data([keyword])[0]
            
        except Exception as e:
            print(f"Error scraping TikTok for '{keyword}': {e}")
            return self.generate_mock_tiktok_data([keyword])[0]
    
    def extract_trending_hashtags(self) -> List[str]:
        """
        Extract currently trending hashtags from TikTok.
        """
        if self.use_mock:
            # Return mock trending hashtags related to products
            trending = [
                '#amazonfinds', '#tiktokmademebuyit', '#productreview', 
                '#smallbusiness', '#affiliatemarketing', '#dropshipping',
                '#amazonhaul', '#dealoftheday', '#musthave', '#trending'
            ]
            return random.sample(trending, 5)
        
        # Placeholder for real hashtag extraction
        try:
            # In production, scrape TikTok trending page or use API
            return ['#amazonfinds', '#tiktokmademebuyit', '#productreview']
        except Exception as e:
            print(f"Error getting trending hashtags: {e}")
            return []
    
    def analyze_social_sentiment(self, text: str) -> float:
        """
        Simple sentiment analysis for social media posts.
        Returns score between 0.0 (negative) and 1.0 (positive).
        """
        # Simple keyword-based sentiment analysis
        positive_words = [
            'love', 'amazing', 'great', 'awesome', 'fantastic', 'perfect',
            'excellent', 'recommend', 'best', 'good', 'happy', 'satisfied'
        ]
        
        negative_words = [
            'hate', 'terrible', 'awful', 'worst', 'bad', 'disappointing',
            'scam', 'fake', 'poor', 'broken', 'useless', 'waste'
        ]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.5  # Neutral
        
        sentiment = positive_count / (positive_count + negative_count)
        return sentiment
    
    def update_social_database(self, db: Session, keywords: List[str] = None) -> int:
        """
        Update database with fresh social media signal data.
        """
        if not keywords:
            keywords = self.product_keywords[:10]  # Limit for demo
        
        social_data = []
        
        # Collect Reddit data
        if self.reddit_enabled or self.use_mock:
            reddit_data = self.generate_mock_reddit_data(keywords)
            social_data.extend(reddit_data)
        
        # Collect TikTok data
        if self.tiktok_enabled or self.use_mock:
            tiktok_data = self.generate_mock_tiktok_data(keywords)
            social_data.extend(tiktok_data)
        
        # Store in database
        stored_count = 0
        for data in social_data:
            trend_entry = TrendData(
                keyword=data['keyword'],
                platform=data['platform'],
                volume_score=data['volume_score'],
                velocity_score=data['velocity_score'],
                sentiment_score=data['sentiment_score'],
                timestamp=data['timestamp']
            )
            db.add(trend_entry)
            stored_count += 1
        
        db.commit()
        return stored_count
    
    def get_viral_products(self, db: Session, platform: str = None, 
                          days: int = 7) -> List[Dict]:
        """
        Get products that are going viral on social media.
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(TrendData).filter(
            TrendData.timestamp > since,
            TrendData.velocity_score > 10  # High velocity = viral potential
        )
        
        if platform:
            query = query.filter(TrendData.platform == platform)
        else:
            query = query.filter(TrendData.platform.in_(['reddit', 'tiktok']))
        
        viral_trends = query.order_by(TrendData.velocity_score.desc()).limit(10).all()
        
        return [
            {
                'keyword': t.keyword,
                'platform': t.platform,
                'velocity': t.velocity_score,
                'volume': t.volume_score,
                'sentiment': t.sentiment_score,
                'timestamp': t.timestamp
            }
            for t in viral_trends
        ]

# Global collector instance
social_collector = SocialSignalsCollector()