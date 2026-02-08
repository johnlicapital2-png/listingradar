import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import yaml
import os

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("Warning: pytrends not available, using mock data only")

from storage.db import TrendData, get_db

class GoogleTrendsCollector:
    """
    Collects Google Trends search volume data for keywords.
    Focuses on detecting search volume acceleration (rate of change).
    """
    
    def __init__(self, config_path="config.yaml"):
        self.config = self.load_config(config_path)
        self.enabled = self.config.get('google_trends', {}).get('enabled', True)
        self.use_mock = not PYTRENDS_AVAILABLE or self.config.get('google_trends', {}).get('mock_data', False)
        
        if self.enabled and not self.use_mock:
            self.pytrends = TrendReq(hl='en-US', tz=360)
        
        # Sample trending keywords for mock data
        self.trending_keywords = [
            "wireless earbuds", "air fryer", "yoga mat", "protein powder",
            "face masks", "hand sanitizer", "standing desk", "ring light",
            "bluetooth speaker", "coffee grinder", "resistance bands",
            "essential oils", "foam roller", "water bottle", "phone case"
        ]
    
    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def generate_mock_trend_data(self, keywords: List[str]) -> List[Dict]:
        """
        Generate mock Google Trends data with realistic patterns.
        Some keywords will have acceleration, others will be declining.
        """
        trend_data = []
        
        for keyword in keywords:
            # Generate 5 data points over the last 5 weeks
            base_volume = random.randint(10, 80)
            
            # 40% chance of acceleration, 40% stable, 20% declining
            trend_type = random.choices(['accelerating', 'stable', 'declining'], 
                                      weights=[40, 40, 20])[0]
            
            volumes = []
            for week in range(5):
                if trend_type == 'accelerating':
                    # Exponential-ish growth
                    volume = base_volume * (1.2 ** week) + random.randint(-5, 10)
                elif trend_type == 'declining':
                    # Declining trend
                    volume = base_volume * (0.85 ** week) + random.randint(-3, 5)
                else:
                    # Stable with noise
                    volume = base_volume + random.randint(-10, 10)
                
                volumes.append(max(0, min(100, volume)))
            
            # Calculate velocity (change between last two data points)
            velocity = volumes[-1] - volumes[-2] if len(volumes) >= 2 else 0
            
            # Create trend data entry
            trend_data.append({
                'keyword': keyword,
                'platform': 'google_trends',
                'volume_score': volumes[-1],  # Latest volume
                'velocity_score': velocity,
                'sentiment_score': 0.5,  # Neutral for Google Trends
                'timestamp': datetime.utcnow()
            })
        
        return trend_data
    
    def fetch_real_trends_data(self, keywords: List[str]) -> List[Dict]:
        """
        Fetch real Google Trends data using pytrends.
        """
        if not PYTRENDS_AVAILABLE or self.use_mock:
            return self.generate_mock_trend_data(keywords)
        
        trend_data = []
        
        try:
            # Batch keywords (pytrends can handle up to 5 at once)
            keyword_batches = [keywords[i:i+5] for i in range(0, len(keywords), 5)]
            
            for batch in keyword_batches:
                self.pytrends.build_payload(batch, timeframe='today 3-m', geo='US')
                
                # Get interest over time
                interest_df = self.pytrends.interest_over_time()
                
                if not interest_df.empty:
                    for keyword in batch:
                        if keyword in interest_df.columns:
                            values = interest_df[keyword].tolist()
                            
                            # Calculate velocity (recent change)
                            velocity = 0
                            if len(values) >= 2:
                                velocity = values[-1] - values[-2]
                            
                            trend_data.append({
                                'keyword': keyword,
                                'platform': 'google_trends',
                                'volume_score': values[-1] if values else 0,
                                'velocity_score': velocity,
                                'sentiment_score': 0.5,  # Neutral
                                'timestamp': datetime.utcnow()
                            })
                
                # Be nice to Google's servers
                import time
                time.sleep(1)
        
        except Exception as e:
            print(f"Error fetching Google Trends data: {e}")
            # Fall back to mock data
            return self.generate_mock_trend_data(keywords)
        
        return trend_data
    
    def get_trending_queries(self, category: str = None) -> List[str]:
        """
        Get currently trending search queries from Google Trends.
        """
        if self.use_mock or not PYTRENDS_AVAILABLE:
            # Return random sample of our trending keywords
            return random.sample(self.trending_keywords, 10)
        
        try:
            # Get trending searches
            trending_df = self.pytrends.trending_searches(pn='united_states')
            if not trending_df.empty:
                # Filter for product-related searches (basic filtering)
                product_keywords = []
                for query in trending_df[0].tolist()[:20]:
                    query_lower = query.lower()
                    # Simple filter for product-related terms
                    if any(word in query_lower for word in 
                          ['buy', 'best', 'review', 'price', 'deal', 'sale', 'product']):
                        product_keywords.append(query)
                
                return product_keywords[:10]
        
        except Exception as e:
            print(f"Error getting trending queries: {e}")
        
        return random.sample(self.trending_keywords, 10)
    
    def extract_keywords_from_products(self, db: Session) -> List[str]:
        """
        Extract keywords from product titles in our database.
        """
        from storage.db import Product
        
        products = db.query(Product).limit(50).all()
        keywords = set()
        
        for product in products:
            if product.title:
                # Extract first few words from product title
                words = product.title.lower().split()[:3]
                keyword = " ".join(words)
                keywords.add(keyword)
        
        return list(keywords)
    
    def update_trends_database(self, db: Session) -> int:
        """
        Update database with fresh Google Trends data.
        """
        if not self.enabled:
            return 0
        
        # Get keywords to track
        keywords = []
        
        # Add keywords from our products
        keywords.extend(self.extract_keywords_from_products(db))
        
        # Add general trending queries
        keywords.extend(self.get_trending_queries())
        
        # Remove duplicates and limit
        keywords = list(set(keywords))[:20]
        
        if not keywords:
            keywords = self.trending_keywords[:10]  # Fallback
        
        # Fetch trends data
        trend_data = self.fetch_real_trends_data(keywords)
        
        # Store in database
        stored_count = 0
        for data in trend_data:
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
    
    def get_accelerating_keywords(self, db: Session, limit: int = 10) -> List[Dict]:
        """
        Get keywords with highest search acceleration in the last week.
        """
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        accelerating = db.query(TrendData).filter(
            TrendData.platform == 'google_trends',
            TrendData.timestamp > week_ago,
            TrendData.velocity_score > 5  # Positive acceleration
        ).order_by(TrendData.velocity_score.desc()).limit(limit).all()
        
        return [
            {
                'keyword': t.keyword,
                'velocity': t.velocity_score,
                'volume': t.volume_score,
                'timestamp': t.timestamp
            }
            for t in accelerating
        ]

# Global collector instance
trends_collector = GoogleTrendsCollector()