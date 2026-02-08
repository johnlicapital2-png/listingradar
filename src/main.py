#!/usr/bin/env python3
"""
ListingRadar - Main application entry point
Coordinates data collection, momentum scoring, and alerts.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
import yaml
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Import our modules
import storage.db as db_module
from storage.db import get_db
import collectors.amazon as amazon_module
import collectors.google_trends as trends_module
import scoring.engine as scoring_module
import alerts.telegram as telegram_module
import dashboard.app as dashboard_module

# Get instances
db_manager = db_module.db_manager
amazon_collector = amazon_module.amazon_collector
trends_collector = trends_module.trends_collector
scoring_engine = scoring_module.scoring_engine
telegram_alerter = telegram_module.telegram_alerter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ListingRadarApp:
    """
    Main ListingRadar application orchestrator.
    """
    
    def __init__(self, config_path="config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.scheduler = AsyncIOScheduler()
        self.running = False
        
        # Initialize components
        self.setup_scheduler()
        
    def load_config(self) -> dict:
        """Load configuration from YAML file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self.get_default_config()
    
    def get_default_config(self) -> dict:
        """Return default configuration."""
        return {
            'database': {'url': 'sqlite:///listing_radar.db'},
            'scheduler': {
                'amazon_check_interval': 300,
                'trends_check_interval': 900,
                'scoring_update_interval': 600,
                'alert_check_interval': 300
            },
            'dashboard': {'host': '127.0.0.1', 'port': 8000}
        }
    
    def setup_scheduler(self):
        """Set up scheduled tasks."""
        intervals = self.config.get('scheduler', {})
        
        # Amazon data collection
        self.scheduler.add_job(
            self.collect_amazon_data,
            IntervalTrigger(seconds=intervals.get('amazon_check_interval', 300)),
            id='amazon_collector',
            name='Amazon BSR Collection'
        )
        
        # Google Trends data collection
        self.scheduler.add_job(
            self.collect_trends_data,
            IntervalTrigger(seconds=intervals.get('trends_check_interval', 900)),
            id='trends_collector',
            name='Google Trends Collection'
        )
        
        # Momentum scoring updates
        self.scheduler.add_job(
            self.update_momentum_scores,
            IntervalTrigger(seconds=intervals.get('scoring_update_interval', 600)),
            id='momentum_scorer',
            name='Momentum Score Updates'
        )
        
        # Alert checking
        self.scheduler.add_job(
            self.check_alerts,
            IntervalTrigger(seconds=intervals.get('alert_check_interval', 300)),
            id='alert_checker',
            name='Alert Checking'
        )
        
        # Daily digest (9 AM daily)
        self.scheduler.add_job(
            self.send_daily_digest,
            'cron',
            hour=9,
            minute=0,
            id='daily_digest',
            name='Daily Trends Digest'
        )
    
    async def collect_amazon_data(self):
        """Collect Amazon BSR data."""
        logger.info("Starting Amazon data collection...")
        try:
            db = next(get_db())
            updated_count = amazon_collector.update_product_database(db)
            logger.info(f"Updated {updated_count} Amazon products")
        except Exception as e:
            logger.error(f"Error collecting Amazon data: {e}")
        finally:
            db.close()
    
    async def collect_trends_data(self):
        """Collect Google Trends data."""
        logger.info("Starting Google Trends data collection...")
        try:
            db = next(get_db())
            updated_count = trends_collector.update_trends_database(db)
            logger.info(f"Updated {updated_count} trend data points")
        except Exception as e:
            logger.error(f"Error collecting trends data: {e}")
        finally:
            db.close()
    
    async def update_momentum_scores(self):
        """Update momentum scores for all products."""
        logger.info("Updating momentum scores...")
        try:
            db = next(get_db())
            updated_products = scoring_engine.batch_update_momentum_scores(db)
            
            high_momentum = [p for p in updated_products if p.momentum_score > 60]
            logger.info(f"Updated {len(updated_products)} products, {len(high_momentum)} high momentum")
            
        except Exception as e:
            logger.error(f"Error updating momentum scores: {e}")
        finally:
            db.close()
    
    async def check_alerts(self):
        """Check for and send momentum alerts."""
        logger.info("Checking for momentum alerts...")
        try:
            db = next(get_db())
            alerts_sent = await telegram_alerter.check_and_send_alerts(db)
            if alerts_sent > 0:
                logger.info(f"Sent {alerts_sent} momentum alerts")
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
        finally:
            db.close()
    
    async def send_daily_digest(self):
        """Send daily trends digest."""
        logger.info("Sending daily trends digest...")
        try:
            db = next(get_db())
            sent = await telegram_alerter.send_daily_digest(db)
            if sent:
                logger.info("Daily digest sent successfully")
            else:
                logger.warning("Daily digest failed to send")
        except Exception as e:
            logger.error(f"Error sending daily digest: {e}")
        finally:
            db.close()
    
    async def run_initial_collection(self):
        """Run initial data collection on startup."""
        logger.info("Running initial data collection...")
        
        # Collect some initial data
        await self.collect_amazon_data()
        await self.collect_trends_data()
        await asyncio.sleep(2)
        await self.update_momentum_scores()
        
        logger.info("Initial collection complete")
    
    async def start(self):
        """Start the ListingRadar application."""
        if self.running:
            return
        
        logger.info("Starting ListingRadar...")
        
        # Initialize database
        db_manager.init_db()
        
        # Run initial collection
        await self.run_initial_collection()
        
        # Start scheduler
        self.scheduler.start()
        self.running = True
        
        logger.info("ListingRadar started successfully!")
        logger.info(f"Scheduled tasks: {len(self.scheduler.get_jobs())}")
        
        # Send test alert if Telegram is configured
        try:
            if telegram_alerter.bot:
                telegram_alerter.send_test_alert()
                logger.info("Test Telegram alert sent")
        except Exception as e:
            logger.warning(f"Could not send test alert: {e}")
    
    async def stop(self):
        """Stop the application."""
        if not self.running:
            return
        
        logger.info("Stopping ListingRadar...")
        
        self.scheduler.shutdown()
        db_manager.close()
        self.running = False
        
        logger.info("ListingRadar stopped")
    
    def get_status(self) -> dict:
        """Get application status."""
        jobs = []
        if self.running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                })
        
        return {
            'running': self.running,
            'jobs': jobs,
            'database': 'connected' if db_manager.engine else 'disconnected',
            'telegram': 'configured' if telegram_alerter.bot else 'not configured'
        }

async def main():
    """Main entry point."""
    # Create config file if it doesn't exist
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'config.yaml')
    config_example_path = os.path.join(project_root, 'config.yaml.example')
    
    if not os.path.exists(config_path):
        logger.info("Creating default config.yaml...")
        with open(config_example_path, 'r') as example:
            with open(config_path, 'w') as config:
                config.write(example.read())
        logger.info("Config created. Please edit config.yaml with your API keys.")
    
    # Initialize app
    app = ListingRadarApp()
    
    try:
        # Start ListingRadar
        await app.start()
        
        # Start web dashboard in background
        dashboard_config = app.config.get('dashboard', {})
        dashboard_app = dashboard_module.create_app()
        
        import uvicorn
        config = uvicorn.Config(
            dashboard_app,
            host=dashboard_config.get('host', '127.0.0.1'),
            port=dashboard_config.get('port', 8000),
            log_level='info'
        )
        server = uvicorn.Server(config)
        
        logger.info(f"Starting dashboard at http://{config.host}:{config.port}")
        
        # Run both the scheduler and web server
        await asyncio.gather(
            server.serve(),
            keep_running()
        )
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
    finally:
        await app.stop()

async def keep_running():
    """Keep the main loop running."""
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())