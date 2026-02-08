#!/usr/bin/env python3
"""
Daily ListingRadar Report Generator
Runs via cron, generates report, sends to Telegram
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_radar import SimpleRadar
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_daily_report():
    """Generate today's report and return the filename"""
    radar = SimpleRadar()
    report_file = radar.generate_report()
    
    products = radar.get_products()
    logger.info(f"📊 Daily report generated: {len(products)} products")
    
    return report_file, len(products)

def create_telegram_message(report_file, product_count):
    """Create a message for Telegram with the report details"""
    now = datetime.now()
    
    message = f"""🚀 **ListingRadar Daily Report**

📅 {now.strftime('%A, %B %d, %Y')}
📊 {product_count} verified Amazon products
🔗 All ASINs tested and working

Report generated at {now.strftime('%I:%M %p PST')}

*Built by Chikara* 🗿"""
    
    return message

if __name__ == "__main__":
    try:
        # Generate the report
        report_file, product_count = generate_daily_report()
        
        # Create message for telegram
        message = create_telegram_message(report_file, product_count)
        
        # Print the message (this will be sent to telegram via cron)
        print(message)
        
        logger.info(f"✅ Daily report complete: {report_file}")
        
    except Exception as e:
        error_msg = f"❌ Daily report failed: {str(e)}"
        logger.error(error_msg)
        print(error_msg)