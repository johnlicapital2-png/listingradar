#!/usr/bin/env python3
"""
ListingRadar - Verified Amazon Products Data Source
Built by Chikara - No fake ASINs, only verified working products
"""

import requests
import sqlite3
from datetime import datetime
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductVerifier:
    def __init__(self, db_path='verified_products.db'):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Create the database table for verified products"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verified_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                price TEXT,
                verified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")
    
    def verify_asin(self, asin):
        """Verify that an ASIN returns a valid Amazon product page"""
        url = f"https://www.amazon.com/dp/{asin}"
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            # Amazon returns 200 even for invalid ASINs, but with different content
            if response.status_code == 200:
                content = response.text.lower()
                # Check for indicators of a valid product page
                valid_indicators = [
                    'add to cart',
                    'buy now', 
                    'product details',
                    'customer reviews'
                ]
                invalid_indicators = [
                    'page not found',
                    'dogs of amazon',
                    'error'
                ]
                
                has_valid = any(indicator in content for indicator in valid_indicators)
                has_invalid = any(indicator in content for indicator in invalid_indicators)
                
                if has_valid and not has_invalid:
                    logger.info(f"✅ ASIN {asin} is valid")
                    return True
                else:
                    logger.warning(f"❌ ASIN {asin} appears invalid")
                    return False
            else:
                logger.warning(f"❌ ASIN {asin} returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error verifying ASIN {asin}: {e}")
            return False
    
    def add_product(self, asin, title, category, price=None):
        """Add a product only if ASIN is verified as working"""
        logger.info(f"Verifying product: {title} ({asin})")
        
        if not self.verify_asin(asin):
            logger.error(f"❌ Skipping {asin} - failed verification")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO verified_products 
                (asin, title, category, price, verified_date, last_checked)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (asin, title, category, price))
            conn.commit()
            conn.close()
            logger.info(f"✅ Added verified product: {title}")
            return True
        except Exception as e:
            logger.error(f"❌ Database error adding {asin}: {e}")
            return False
    
    def get_verified_products(self, limit=20):
        """Get all verified products from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT asin, title, category, price, verified_date 
            FROM verified_products 
            WHERE status = 'active' 
            ORDER BY verified_date DESC 
            LIMIT ?
        ''', (limit,))
        products = cursor.fetchall()
        conn.close()
        return products

def seed_verified_products():
    """Seed the database with a small set of known working Amazon best-sellers"""
    verifier = ProductVerifier()
    
    # Start with a small, manually curated list of popular Amazon products
    # These are products that are consistently top sellers and likely to be stable
    test_products = [
        ("B07ZPKN6YR", "Apple AirPods Pro (2nd Generation)", "Electronics"),
        ("B085RWZ2GY", "Crest 3D Whitestrips, 44 Strips", "Health & Personal Care"),
        ("B01DFKBG54", "Anker Portable Charger", "Electronics"),
        ("B08N5WRWNW", "Echo Dot (4th Gen, 2020)", "Electronics"),
        ("B084DWG2VQ", "Apple iPhone Lightning to 3.5mm Adapter", "Electronics"),
    ]
    
    logger.info("Starting verification of seed products...")
    verified_count = 0
    
    for asin, title, category in test_products:
        if verifier.add_product(asin, title, category):
            verified_count += 1
        time.sleep(2)  # Be respectful to Amazon
    
    logger.info(f"✅ Verification complete. {verified_count}/{len(test_products)} products verified and added.")
    
    # Show what we have
    products = verifier.get_verified_products()
    if products:
        logger.info("📋 Verified products in database:")
        for asin, title, category, price, verified_date in products:
            logger.info(f"  • {title} ({asin}) - {category}")
    else:
        logger.error("❌ No verified products found. All ASINs may be invalid.")

if __name__ == "__main__":
    seed_verified_products()