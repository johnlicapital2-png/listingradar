from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import json

from storage.db import get_db, Product, TrendData, Alert
from scoring.engine import scoring_engine

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="ListingRadar",
        description="Trend momentum tracking for Amazon & Shopify",
        version="1.0.0"
    )
    
    # Mount static files
    import os
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Templates
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    templates = Jinja2Templates(directory=templates_dir)
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request, category: Optional[str] = None, db: Session = Depends(get_db)):
        """Main dashboard page."""

        # Base query for products
        product_query = db.query(Product)
        if category:
            product_query = product_query.filter(Product.category == category)

        # Get top momentum products
        top_products = product_query.filter(
            Product.momentum_score > 30
        ).order_by(Product.momentum_score.desc()).limit(10).all()

        # Get distinct categories for the filter dropdown
        categories = db.query(Product.category).distinct().all()
        # Flatten the list of tuples
        category_list = [c[0] for c in categories if c[0]]

        # Get recent alerts
        recent_alerts = db.query(Alert).order_by(
            Alert.sent_at.desc()
        ).limit(5).all()

        # Get trending keywords
        week_ago = datetime.utcnow() - timedelta(days=7)
        trending_keywords = db.query(TrendData).filter(
            TrendData.platform == 'google_trends',
            TrendData.timestamp > week_ago,
            TrendData.velocity_score > 0
        ).order_by(TrendData.velocity_score.desc()).limit(10).all()
        
        # Stats
        total_products = db.query(Product).count()
        trending_products = db.query(Product).filter(Product.is_trending == True).count()
        total_alerts = db.query(Alert).filter(
            Alert.sent_at > datetime.utcnow() - timedelta(days=1)
        ).count()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "top_products": top_products,
            "recent_alerts": recent_alerts,
            "trending_keywords": trending_keywords,
            "stats": {
                "total_products": total_products,
                "trending_products": trending_products,
                "daily_alerts": total_alerts
            },
            "categories": category_list,
            "selected_category": category
        })
    
    @app.get("/api/products", response_model=List[dict])
    async def get_products(skip: int = 0, limit: int = 50, 
                          trending_only: bool = False,
                          db: Session = Depends(get_db)):
        """Get products with pagination."""
        
        query = db.query(Product)
        
        if trending_only:
            query = query.filter(Product.is_trending == True)
        
        products = query.order_by(Product.momentum_score.desc()).offset(skip).limit(limit).all()
        
        return [
            {
                "id": p.id,
                "asin": p.asin,
                "title": p.title,
                "category": p.category,
                "price": p.price,
                "bsr_current": p.bsr_current,
                "bsr_previous": p.bsr_previous,
                "bsr_velocity": p.bsr_velocity,
                "momentum_score": p.momentum_score,
                "confidence_level": p.confidence_level,
                "is_trending": p.is_trending,
                "last_updated": p.last_updated.isoformat() if p.last_updated else None
            }
            for p in products
        ]
    
    @app.get("/api/trends", response_model=List[dict])
    async def get_trends(platform: Optional[str] = None,
                        days: int = 7,
                        db: Session = Depends(get_db)):
        """Get trend data."""
        
        since = datetime.utcnow() - timedelta(days=days)
        query = db.query(TrendData).filter(TrendData.timestamp > since)
        
        if platform:
            query = query.filter(TrendData.platform == platform)
        
        trends = query.order_by(TrendData.timestamp.desc()).limit(100).all()
        
        return [
            {
                "id": t.id,
                "keyword": t.keyword,
                "platform": t.platform,
                "volume_score": t.volume_score,
                "velocity_score": t.velocity_score,
                "sentiment_score": t.sentiment_score,
                "timestamp": t.timestamp.isoformat()
            }
            for t in trends
        ]
    
    @app.get("/api/alerts", response_model=List[dict])
    async def get_alerts(days: int = 7, db: Session = Depends(get_db)):
        """Get recent alerts."""
        
        since = datetime.utcnow() - timedelta(days=days)
        alerts = db.query(Alert).filter(
            Alert.sent_at > since
        ).order_by(Alert.sent_at.desc()).limit(50).all()
        
        return [
            {
                "id": a.id,
                "product_asin": a.product_asin,
                "alert_type": a.alert_type,
                "message": a.message,
                "momentum_score": a.momentum_score,
                "confidence": a.confidence,
                "sent_at": a.sent_at.isoformat(),
                "telegram_sent": a.telegram_sent
            }
            for a in alerts
        ]
    
    @app.get("/api/momentum-chart/{product_id}")
    async def get_momentum_chart(product_id: int, db: Session = Depends(get_db)):
        """Get momentum score history for charting."""
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # For now, return mock chart data
        # In production, you'd track momentum score over time
        chart_data = {
            "labels": ["7 days ago", "6 days ago", "5 days ago", "4 days ago", "3 days ago", "2 days ago", "Yesterday", "Today"],
            "data": [30, 35, 42, 48, 55, 61, 67, product.momentum_score or 0]
        }
        
        return chart_data
    
    @app.get("/api/stats")
    async def get_stats(db: Session = Depends(get_db)):
        """Get dashboard statistics."""
        
        # Basic counts
        total_products = db.query(Product).count()
        trending_products = db.query(Product).filter(Product.is_trending == True).count()
        
        # Recent activity
        day_ago = datetime.utcnow() - timedelta(days=1)
        daily_alerts = db.query(Alert).filter(Alert.sent_at > day_ago).count()
        
        # Momentum distribution
        high_momentum = db.query(Product).filter(Product.momentum_score >= 70).count()
        med_momentum = db.query(Product).filter(
            Product.momentum_score >= 40,
            Product.momentum_score < 70
        ).count()
        low_momentum = db.query(Product).filter(Product.momentum_score < 40).count()
        
        return {
            "total_products": total_products,
            "trending_products": trending_products,
            "daily_alerts": daily_alerts,
            "momentum_distribution": {
                "high": high_momentum,
                "medium": med_momentum,
                "low": low_momentum
            }
        }
    
    @app.post("/api/test-alert")
    async def test_alert():
        """Send test Telegram alert."""
        from alerts.telegram import telegram_alerter
        
        try:
            success = telegram_alerter.send_test_alert()
            return {"success": success, "message": "Test alert sent" if success else "Alert failed"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    return app