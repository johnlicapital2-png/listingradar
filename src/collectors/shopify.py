import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import httpx
from bs4 import BeautifulSoup
import yaml
import os
import asyncio

from storage.db import ShopifyStore, get_db

class ShopifyStoreCollector:
    """
    Discovers trending Shopify stores and products.
    Uses mock data for demonstration, with placeholders for real discovery methods.
    """
    
    def __init__(self, config_path="config.yaml"):
        self.config = self.load_config(config_path)
        self.enabled = self.config.get('shopify', {}).get('enabled', False)
        self.use_mock = self.config.get('shopify', {}).get('mock_data', True)
        
        # Sample Shopify stores for mock data
        self.sample_stores = [
            "gymshark.com", "allbirds.com", "mvmt.com", "bombas.com",
            "casper.com", "warbyparker.com", "away.com", "glossier.com",
            "outdoor-voices.com", "kotn.com", "everlane.com", "rothys.com"
        ]
        
        # Common Shopify store indicators
        self.shopify_indicators = [
            'myshopify.com',
            'cdn.shopify.com',
            'shopifycdn.com',
            'Shopify.theme',
            'window.Shopify'
        ]
    
    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def generate_mock_stores(self, count: int = 15) -> List[Dict]:
        """
        Generate mock Shopify store data with realistic metrics.
        """
        mock_stores = []
        
        categories = [
            "Fashion & Apparel", "Health & Beauty", "Home & Garden",
            "Electronics", "Sports & Fitness", "Food & Beverage",
            "Jewelry & Accessories", "Pet Supplies", "Baby & Kids"
        ]
        
        for i in range(count):
            # Generate store name
            store_name = random.choice([
                "TrendCo", "ModernBrand", "EcoStyle", "PureLife", "FlexFit",
                "SmartHome", "ActiveWear", "UrbanChic", "NaturalVibes", "TechHub"
            ]) + random.choice(["", "Co", "Store", "Shop", "Brand"])
            
            # Generate URL (some real, some generated)
            if i < len(self.sample_stores):
                url = self.sample_stores[i]
            else:
                url = f"{store_name.lower().replace(' ', '')}.com"
            
            # Generate realistic metrics
            product_count = random.randint(50, 2000)
            
            # Momentum score based on various factors
            # New stores or those with rapid growth get higher scores
            base_momentum = random.uniform(20, 90)
            
            # 25% chance of high momentum (trending store)
            if random.random() < 0.25:
                momentum_score = random.uniform(70, 95)
            else:
                momentum_score = base_momentum
            
            mock_stores.append({
                'store_name': store_name,
                'url': url,
                'category': random.choice(categories),
                'product_count': product_count,
                'momentum_score': momentum_score,
                'estimated_revenue': random.randint(10000, 10000000),
                'social_followers': random.randint(1000, 500000),
                'last_checked': datetime.utcnow() - timedelta(hours=random.randint(1, 24))
            })
        
        return mock_stores
    
    def check_if_shopify_store(self, url: str) -> bool:
        """
        Check if a given URL is a Shopify store by looking for indicators.
        """
        if self.use_mock:
            # For demo purposes, assume all sampled URLs are Shopify stores
            return True
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = httpx.get(f'https://{url}', headers=headers, timeout=10, follow_redirects=True)
            
            # Check for Shopify indicators in HTML
            page_content = response.text.lower()
            
            for indicator in self.shopify_indicators:
                if indicator.lower() in page_content:
                    return True
            
            # Check response headers
            if 'server' in response.headers:
                server = response.headers['server'].lower()
                if 'shopify' in server:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error checking if {url} is Shopify store: {e}")
            return False
    
    def discover_stores_via_builtwith(self, limit: int = 50) -> List[str]:
        """
        Discover Shopify stores using BuiltWith-style technology detection.
        Placeholder for real BuiltWith API integration.
        """
        if self.use_mock:
            # Return sample stores with some variation
            return random.sample(self.sample_stores * 2, min(limit, len(self.sample_stores * 2)))
        
        # Placeholder for real BuiltWith API
        # In production, you'd use:
        # 1. BuiltWith API (paid service)
        # 2. Wappalyzer API
        # 3. Custom web scraping to find Shopify stores
        
        try:
            # Example BuiltWith API call (requires API key):
            # url = "https://api.builtwith.com/v20/api.json"
            # params = {
            #     'KEY': 'your_api_key',
            #     'LOOKUP': 'shopify.com',
            #     'HIDETEXT': 'yes',
            #     'HIDEDL': 'yes'
            # }
            # response = httpx.get(url, params=params)
            # Parse response for Shopify store URLs
            
            return self.sample_stores[:limit]
            
        except Exception as e:
            print(f"Error discovering stores: {e}")
            return self.sample_stores[:limit]
    
    def analyze_store_momentum(self, url: str) -> Dict:
        """
        Analyze a Shopify store's momentum by checking various metrics.
        """
        if self.use_mock:
            return self.generate_mock_stores(1)[0]
        
        try:
            momentum_data = {
                'store_name': url.replace('.com', '').replace('.', '').title(),
                'url': url,
                'product_count': 0,
                'momentum_score': 0,
                'last_checked': datetime.utcnow()
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            # Get store homepage
            response = httpx.get(f'https://{url}', headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract store name
            title_tag = soup.find('title')
            if title_tag:
                momentum_data['store_name'] = title_tag.text.strip()
            
            # Estimate product count (check sitemap or collection pages)
            try:
                sitemap_response = httpx.get(f'https://{url}/sitemap_products_1.xml', timeout=5)
                if sitemap_response.status_code == 200:
                    # Count product URLs in sitemap
                    product_count = sitemap_response.text.count('<loc>')
                    momentum_data['product_count'] = product_count
            except:
                pass
            
            # Calculate basic momentum score based on available data
            base_score = 30
            
            # More products = higher potential momentum
            if momentum_data['product_count'] > 500:
                base_score += 20
            elif momentum_data['product_count'] > 100:
                base_score += 10
            
            # Check for "new" or "trending" indicators
            page_text = soup.get_text().lower()
            if any(word in page_text for word in ['new', 'trending', 'viral', 'popular']):
                base_score += 15
            
            momentum_data['momentum_score'] = min(100, base_score)
            
            return momentum_data
            
        except Exception as e:
            print(f"Error analyzing store {url}: {e}")
            return self.generate_mock_stores(1)[0]
    
    def find_trending_products_on_store(self, store_url: str) -> List[Dict]:
        """
        Find trending products on a specific Shopify store.
        """
        if self.use_mock:
            # Generate mock trending products
            products = []
            for i in range(5):
                products.append({
                    'title': f"Trending Product {i+1}",
                    'price': random.uniform(19.99, 199.99),
                    'url': f"{store_url}/products/trending-product-{i+1}",
                    'momentum_score': random.uniform(60, 95)
                })
            return products
        
        try:
            # In production, you'd:
            # 1. Scrape the store's /collections/all or /products.json
            # 2. Look for "bestseller", "trending", "popular" collections
            # 3. Check social signals for specific products
            # 4. Monitor inventory changes (fast selling = trending)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            # Try to get products JSON (many Shopify stores expose this)
            products_url = f'https://{store_url}/products.json?limit=50'
            response = httpx.get(products_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                products_data = response.json()
                trending_products = []
                
                for product in products_data.get('products', [])[:10]:
                    # Simple momentum calculation based on available data
                    momentum = 50  # Base score
                    
                    # Check if it's recently created
                    created_at = product.get('created_at', '')
                    if created_at:
                        # Add momentum for recent products
                        momentum += 10
                    
                    # Check variants count (more options = more popular?)
                    variants_count = len(product.get('variants', []))
                    momentum += min(20, variants_count * 2)
                    
                    trending_products.append({
                        'title': product.get('title', 'Unknown Product'),
                        'price': float(product.get('variants', [{}])[0].get('price', 0)),
                        'url': f"https://{store_url}/products/{product.get('handle')}",
                        'momentum_score': min(100, momentum)
                    })
                
                return trending_products
            
            return []
            
        except Exception as e:
            print(f"Error finding trending products on {store_url}: {e}")
            return []
    
    def update_stores_database(self, db: Session) -> int:
        """
        Update database with fresh Shopify store data.
        """
        if not self.enabled and not self.use_mock:
            return 0
        
        # Discover new stores
        discovered_urls = self.discover_stores_via_builtwith(20)
        
        updated_count = 0
        
        for url in discovered_urls:
            # Check if store exists in database
            existing_store = db.query(ShopifyStore).filter(
                ShopifyStore.url == url
            ).first()
            
            # Analyze store momentum
            store_data = self.analyze_store_momentum(url)
            
            if existing_store:
                # Update existing store
                existing_store.store_name = store_data['store_name']
                existing_store.product_count = store_data['product_count']
                existing_store.momentum_score = store_data['momentum_score']
                existing_store.last_checked = datetime.utcnow()
            else:
                # Create new store entry
                new_store = ShopifyStore(
                    store_name=store_data['store_name'],
                    url=store_data['url'],
                    product_count=store_data['product_count'],
                    momentum_score=store_data['momentum_score'],
                    last_checked=datetime.utcnow()
                )
                db.add(new_store)
            
            updated_count += 1
        
        db.commit()
        return updated_count
    
    def get_trending_stores(self, db: Session, limit: int = 10) -> List[ShopifyStore]:
        """
        Get Shopify stores with highest momentum scores.
        """
        return db.query(ShopifyStore).filter(
            ShopifyStore.momentum_score > 60
        ).order_by(ShopifyStore.momentum_score.desc()).limit(limit).all()
    
    def get_new_stores(self, db: Session, days: int = 7, limit: int = 10) -> List[ShopifyStore]:
        """
        Get recently discovered Shopify stores.
        """
        since = datetime.utcnow() - timedelta(days=days)
        return db.query(ShopifyStore).filter(
            ShopifyStore.last_checked > since
        ).order_by(ShopifyStore.last_checked.desc()).limit(limit).all()

# Global collector instance
shopify_collector = ShopifyStoreCollector()