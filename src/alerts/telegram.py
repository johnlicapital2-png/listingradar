import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import yaml
import os

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: python-telegram-bot not available, alerts will only print to console")

from storage.db import Alert, Product, TrendData, get_db

class TelegramAlerter:
    """
    Sends momentum alerts via Telegram bot.
    Falls back to console logging if Telegram is not available.
    """
    
    def __init__(self, config_path="config.yaml"):
        self.config = self.load_config(config_path)
        self.bot_token = self.config.get('telegram', {}).get('bot_token')
        self.chat_id = self.config.get('telegram', {}).get('chat_id')
        self.momentum_threshold = self.config.get('scoring', {}).get('momentum_threshold', 60)
        self.confidence_threshold = self.config.get('scoring', {}).get('confidence_threshold', 70)
        
        self.bot = None
        if TELEGRAM_AVAILABLE and self.bot_token and self.bot_token != "YOUR_BOT_TOKEN_HERE":
            self.bot = Bot(token=self.bot_token)
        else:
            print("Telegram bot not configured, using console alerts only")
    
    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    async def send_telegram_message(self, message: str, parse_mode='Markdown') -> bool:
        """
        Send a message via Telegram bot.
        """
        if not self.bot or not self.chat_id:
            print(f"[TELEGRAM ALERT] {message}")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            return True
        
        except TelegramError as e:
            print(f"Telegram error: {e}")
            print(f"[CONSOLE ALERT] {message}")
            return False
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            print(f"[CONSOLE ALERT] {message}")
            return False
    
    def format_momentum_alert(self, product: Product, alert_type: str = "momentum_spike") -> str:
        """
        Format a product momentum alert for Telegram.
        """
        # Determine emoji based on momentum score
        if product.momentum_score >= 80:
            emoji = "🚀"
        elif product.momentum_score >= 60:
            emoji = "📈"
        else:
            emoji = "⚡"
        
        # Format BSR change
        bsr_change = ""
        if product.bsr_current and product.bsr_previous:
            change = product.bsr_previous - product.bsr_current
            if change > 0:
                bsr_change = f" (↗️ +{change:,} ranks)"
            else:
                bsr_change = f" (↘️ {change:,} ranks)"
        
        # Build alert message
        message = f"""{emoji} **MOMENTUM ALERT**
        
**Product:** {product.title[:60]}...
**ASIN:** `{product.asin}`
**Category:** {product.category}
**Price:** ${product.price:.2f}

📊 **Momentum Score:** {product.momentum_score:.1f}/100
🎯 **Confidence:** {product.confidence_level.upper()}
📉 **BSR:** #{product.bsr_current:,}{bsr_change}

🔗 **Amazon:** [View Product](https://amazon.com/dp/{product.asin})

*Alert triggered at {datetime.now().strftime('%H:%M:%S')}*"""
        
        return message
    
    def format_trends_digest(self, top_products: List[Product], 
                           trending_keywords: List[Dict]) -> str:
        """
        Format daily trends digest.
        """
        message = "📊 **DAILY TRENDS DIGEST**\n\n"
        
        # Top momentum products
        if top_products:
            message += "🔥 **TOP MOMENTUM PRODUCTS:**\n"
            for i, product in enumerate(top_products[:5], 1):
                score_emoji = "🚀" if product.momentum_score >= 80 else "📈"
                message += f"{i}. {score_emoji} {product.title[:40]}... ({product.momentum_score:.1f}/100)\n"
            message += "\n"
        
        # Trending keywords
        if trending_keywords:
            message += "🔍 **TRENDING SEARCHES:**\n"
            for i, keyword in enumerate(trending_keywords[:5], 1):
                velocity = keyword.get('velocity', 0)
                velocity_emoji = "⚡" if velocity > 10 else "📊"
                message += f"{i}. {velocity_emoji} {keyword['keyword']} (+{velocity:.1f})\n"
            message += "\n"
        
        message += f"*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
        
        return message
    
    async def send_momentum_alert(self, product: Product, db: Session) -> bool:
        """
        Send a momentum spike alert for a specific product.
        """
        # Check if we already sent an alert for this product recently
        recent_alert = db.query(Alert).filter(
            Alert.product_asin == product.asin,
            Alert.sent_at > datetime.utcnow() - timedelta(hours=6)
        ).first()
        
        if recent_alert:
            return False  # Don't spam alerts
        
        # Format and send alert
        message = self.format_momentum_alert(product)
        sent = await self.send_telegram_message(message)
        
        # Log alert in database
        alert = Alert(
            product_asin=product.asin,
            alert_type="momentum_spike",
            message=message,
            momentum_score=product.momentum_score,
            confidence=product.confidence_level,
            telegram_sent=sent
        )
        db.add(alert)
        db.commit()
        
        return sent
    
    async def send_daily_digest(self, db: Session) -> bool:
        """
        Send daily trends digest.
        """
        # Get top momentum products from last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        top_products = db.query(Product).filter(
            Product.last_updated > yesterday,
            Product.momentum_score > 40
        ).order_by(Product.momentum_score.desc()).limit(10).all()
        
        # Get trending keywords
        trending_keywords = db.query(TrendData).filter(
            TrendData.platform == 'google_trends',
            TrendData.timestamp > yesterday,
            TrendData.velocity_score > 0
        ).order_by(TrendData.velocity_score.desc()).limit(10).all()
        
        trending_kw_list = [
            {
                'keyword': t.keyword,
                'velocity': t.velocity_score,
                'volume': t.volume_score
            }
            for t in trending_keywords
        ]
        
        # Format and send digest
        message = self.format_trends_digest(top_products, trending_kw_list)
        return await self.send_telegram_message(message)
    
    async def check_and_send_alerts(self, db: Session) -> int:
        """
        Check for products that should trigger momentum alerts.
        Returns number of alerts sent.
        """
        # Find products that crossed momentum threshold
        alert_worthy = db.query(Product).filter(
            Product.momentum_score >= self.momentum_threshold,
            Product.confidence_level.in_(['medium', 'high']),
            Product.is_trending == True
        ).all()
        
        alerts_sent = 0
        
        for product in alert_worthy:
            try:
                sent = await self.send_momentum_alert(product, db)
                if sent:
                    alerts_sent += 1
            except Exception as e:
                print(f"Error sending alert for {product.asin}: {e}")
        
        return alerts_sent
    
    def send_test_alert(self):
        """
        Send a test alert to verify Telegram integration.
        """
        test_message = """🧪 **TEST ALERT**

ListingRadar is online and ready to track momentum!

📊 **Features Active:**
• Amazon BSR tracking
• Google Trends monitoring  
• Momentum scoring engine
• Real-time alerts

*Test sent at {time}*""".format(time=datetime.now().strftime('%H:%M:%S'))
        
        return asyncio.run(self.send_telegram_message(test_message))

# Global alerter instance
telegram_alerter = TelegramAlerter()