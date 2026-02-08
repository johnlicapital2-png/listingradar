import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.db import Product, TrendData, get_db

class MomentumScoringEngine:
    """
    Core momentum scoring engine that analyzes products across multiple signals
    and assigns a 0-100 momentum score with confidence levels.
    """
    
    def __init__(self):
        self.weights = {
            'bsr_velocity': 0.35,      # Amazon BSR movement
            'search_acceleration': 0.25, # Google Trends velocity 
            'social_buzz': 0.20,        # Reddit/TikTok mentions
            'competition_density': 0.20  # New listings in category
        }
    
    def calculate_bsr_velocity_score(self, current_bsr: int, previous_bsr: int, 
                                   hours_elapsed: float = 24.0) -> Tuple[float, str]:
        """
        Calculate BSR velocity score. Lower BSR = better rank.
        Rapid improvement (BSR going down) = high score.
        """
        if not previous_bsr or current_bsr <= 0:
            return 0.0, "insufficient_data"
        
        # BSR improvement (rank going down is good)
        bsr_change = previous_bsr - current_bsr
        if bsr_change <= 0:
            return max(0, 20 - abs(bsr_change) / 1000), "declining"
        
        # Calculate velocity (rank improvement per hour)
        velocity = bsr_change / hours_elapsed
        
        # Score based on velocity, capped at 100
        if velocity > 100:  # Rapid climb
            score = min(100, 70 + math.log10(velocity) * 10)
            confidence = "high"
        elif velocity > 10:  # Moderate climb
            score = min(80, 40 + velocity * 2)
            confidence = "medium"
        elif velocity > 1:   # Slow climb
            score = min(60, 20 + velocity * 10)
            confidence = "low"
        else:
            score = max(0, velocity * 20)
            confidence = "low"
        
        return score, confidence
    
    def calculate_search_acceleration_score(self, keyword: str, 
                                          db: Session) -> Tuple[float, str]:
        """
        Calculate Google Trends search volume acceleration.
        We care about the derivative (rate of change) more than absolute volume.
        """
        # Get recent trend data for this keyword
        recent_data = db.query(TrendData).filter(
            TrendData.keyword == keyword,
            TrendData.platform == "google_trends",
            TrendData.timestamp > datetime.utcnow() - timedelta(days=30)
        ).order_by(TrendData.timestamp.desc()).limit(5).all()
        
        if len(recent_data) < 2:
            return 0.0, "insufficient_data"
        
        # Calculate acceleration (change in velocity)
        volumes = [d.volume_score for d in reversed(recent_data)]
        
        # Simple acceleration calculation
        if len(volumes) >= 3:
            recent_velocity = volumes[-1] - volumes[-2]
            previous_velocity = volumes[-2] - volumes[-3]
            acceleration = recent_velocity - previous_velocity
            
            if acceleration > 10:
                score = min(100, 60 + acceleration * 2)
                confidence = "high"
            elif acceleration > 5:
                score = min(80, 40 + acceleration * 4)
                confidence = "medium"
            elif acceleration > 0:
                score = min(60, 20 + acceleration * 8)
                confidence = "low"
            else:
                score = max(0, 30 + acceleration * 5)  # Negative acceleration
                confidence = "low"
        else:
            # Fallback to simple velocity
            velocity = volumes[-1] - volumes[0]
            score = max(0, min(70, velocity * 2))
            confidence = "low"
        
        return score, confidence
    
    def calculate_social_buzz_score(self, keyword: str, 
                                  db: Session) -> Tuple[float, str]:
        """
        Calculate social media buzz score from Reddit/TikTok mentions.
        """
        # Get recent social data
        recent_social = db.query(TrendData).filter(
            TrendData.keyword == keyword,
            TrendData.platform.in_(["reddit", "tiktok"]),
            TrendData.timestamp > datetime.utcnow() - timedelta(days=7)
        ).all()
        
        if not recent_social:
            return 0.0, "no_data"
        
        # Aggregate social signals
        total_mentions = sum(d.volume_score for d in recent_social)
        avg_sentiment = sum(d.sentiment_score for d in recent_social) / len(recent_social)
        
        # Calculate buzz score
        mention_score = min(50, total_mentions * 2)
        sentiment_boost = max(-20, min(20, (avg_sentiment - 0.5) * 40))
        
        score = mention_score + sentiment_boost
        
        if score > 60:
            confidence = "high"
        elif score > 30:
            confidence = "medium"
        else:
            confidence = "low"
        
        return max(0, score), confidence
    
    def calculate_competition_score(self, category: str, 
                                  db: Session) -> Tuple[float, str]:
        """
        Calculate competition density score.
        More new products entering = validation of trend.
        """
        # Count new products in category in last 30 days
        new_products = db.query(Product).filter(
            Product.category == category,
            Product.first_seen > datetime.utcnow() - timedelta(days=30)
        ).count()
        
        # Score based on new entrants
        if new_products > 50:
            score = min(100, 70 + new_products * 0.5)
            confidence = "high"
        elif new_products > 20:
            score = min(80, 40 + new_products * 1.5)
            confidence = "medium"
        elif new_products > 5:
            score = min(60, 20 + new_products * 3)
            confidence = "low"
        else:
            score = max(0, new_products * 10)
            confidence = "low"
        
        return score, confidence
    
    def calculate_composite_momentum_score(self, product: Product, 
                                         db: Session) -> Tuple[float, str]:
        """
        Calculate the final composite momentum score (0-100) with confidence level.
        """
        scores = {}
        confidences = []
        
        # BSR velocity score
        if product.bsr_current and product.bsr_previous:
            scores['bsr_velocity'], conf = self.calculate_bsr_velocity_score(
                product.bsr_current, product.bsr_previous
            )
            confidences.append(conf)
        else:
            scores['bsr_velocity'] = 0
        
        # Search acceleration (use product title as keyword)
        if product.title:
            keyword = product.title.split()[0:3]  # First 3 words
            keyword_str = " ".join(keyword).lower()
            scores['search_acceleration'], conf = self.calculate_search_acceleration_score(
                keyword_str, db
            )
            confidences.append(conf)
        else:
            scores['search_acceleration'] = 0
        
        # Social buzz
        if product.title:
            scores['social_buzz'], conf = self.calculate_social_buzz_score(
                keyword_str, db
            )
            confidences.append(conf)
        else:
            scores['social_buzz'] = 0
        
        # Competition density
        if product.category:
            scores['competition_density'], conf = self.calculate_competition_score(
                product.category, db
            )
            confidences.append(conf)
        else:
            scores['competition_density'] = 0
        
        # Calculate weighted composite score
        composite_score = sum(
            scores[key] * self.weights[key] 
            for key in scores.keys()
        )
        
        # Determine overall confidence
        high_conf = confidences.count("high")
        med_conf = confidences.count("medium")
        
        if high_conf >= 2:
            overall_confidence = "high"
        elif high_conf >= 1 or med_conf >= 2:
            overall_confidence = "medium"
        else:
            overall_confidence = "low"
        
        return min(100, max(0, composite_score)), overall_confidence
    
    def update_product_momentum(self, product_id: int, db: Session) -> Optional[Product]:
        """
        Update momentum score for a specific product.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None
        
        momentum_score, confidence = self.calculate_composite_momentum_score(product, db)
        
        product.momentum_score = momentum_score
        product.confidence_level = confidence
        product.last_updated = datetime.utcnow()
        
        # Mark as trending if score > 60
        product.is_trending = momentum_score > 60
        
        db.commit()
        return product
    
    def batch_update_momentum_scores(self, db: Session) -> List[Product]:
        """
        Update momentum scores for all products.
        """
        products = db.query(Product).all()
        updated = []
        
        for product in products:
            momentum_score, confidence = self.calculate_composite_momentum_score(product, db)
            
            product.momentum_score = momentum_score
            product.confidence_level = confidence
            product.last_updated = datetime.utcnow()
            product.is_trending = momentum_score > 60
            
            updated.append(product)
        
        db.commit()
        return updated

# Global scoring engine instance
scoring_engine = MomentumScoringEngine()