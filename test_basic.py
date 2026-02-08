#!/usr/bin/env python3
"""
Basic test script for ListingRadar components.
Run this to verify everything is working before starting the full app.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storage.db import db_manager, get_db
from collectors.amazon import amazon_collector
from collectors.google_trends import trends_collector
from collectors.social import social_collector
from collectors.shopify import shopify_collector
from scoring.engine import scoring_engine

def test_database():
    """Test database initialization."""
    print("🔧 Testing database...")
    
    try:
        db_manager.init_db()
        db = next(get_db())
        print("✅ Database connected successfully")
        
        # Test basic query
        from storage.db import Product
        count = db.query(Product).count()
        print(f"✅ Current products in database: {count}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_collectors():
    """Test data collectors."""
    print("\n📊 Testing data collectors...")
    
    try:
        db = next(get_db())
        
        # Test Amazon collector
        print("Testing Amazon BSR collector...")
        amazon_count = amazon_collector.update_product_database(db)
        print(f"✅ Amazon collector added/updated {amazon_count} products")
        
        # Test Google Trends collector  
        print("Testing Google Trends collector...")
        trends_count = trends_collector.update_trends_database(db)
        print(f"✅ Trends collector added {trends_count} trend data points")
        
        # Test Social collector
        print("Testing Social signals collector...")
        social_count = social_collector.update_social_database(db, ['test product'])
        print(f"✅ Social collector added {social_count} social signals")
        
        # Test Shopify collector
        print("Testing Shopify store collector...")
        shopify_count = shopify_collector.update_stores_database(db)
        print(f"✅ Shopify collector added/updated {shopify_count} stores")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Collectors test failed: {e}")
        return False

def test_scoring_engine():
    """Test momentum scoring engine."""
    print("\n🎯 Testing momentum scoring engine...")
    
    try:
        db = next(get_db())
        
        # Update momentum scores for all products
        updated_products = scoring_engine.batch_update_momentum_scores(db)
        print(f"✅ Updated momentum scores for {len(updated_products)} products")
        
        # Show some example scores
        high_momentum = [p for p in updated_products if p.momentum_score > 60]
        if high_momentum:
            print(f"✅ Found {len(high_momentum)} high momentum products:")
            for product in high_momentum[:3]:
                print(f"   • {product.title[:40]}... - Score: {product.momentum_score:.1f}/100")
        else:
            print("✅ No high momentum products found (normal for initial run)")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Scoring engine test failed: {e}")
        return False

def test_telegram_alerter():
    """Test Telegram alerter (without sending)."""
    print("\n📱 Testing Telegram alerter...")
    
    try:
        from alerts.telegram import telegram_alerter
        
        # Check if Telegram is configured
        if telegram_alerter.bot_token and telegram_alerter.bot_token != "YOUR_BOT_TOKEN_HERE":
            print("✅ Telegram bot token configured")
            if telegram_alerter.chat_id:
                print("✅ Telegram chat ID configured")
                print("🚨 Note: Use the web dashboard to send a test alert")
            else:
                print("⚠️  Telegram chat ID not configured")
        else:
            print("⚠️  Telegram bot not configured (using console alerts only)")
        
        return True
        
    except Exception as e:
        print(f"❌ Telegram alerter test failed: {e}")
        return False

def test_dashboard():
    """Test dashboard components."""
    print("\n🌐 Testing dashboard...")
    
    try:
        from dashboard.app import create_app
        app = create_app()
        print("✅ Dashboard app created successfully")
        print("✅ FastAPI application ready")
        print("💡 Start with: python src/main.py")
        print("💡 Then visit: http://localhost:8000")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 ListingRadar Basic Test Suite\n")
    
    tests = [
        ("Database", test_database),
        ("Data Collectors", test_collectors),
        ("Scoring Engine", test_scoring_engine),
        ("Telegram Alerter", test_telegram_alerter),
        ("Dashboard", test_dashboard)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📋 Test Results:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! ListingRadar is ready to run.")
        print("\nNext steps:")
        print("1. Edit config.yaml with your Telegram bot token")
        print("2. Run: python src/main.py")
        print("3. Visit: http://localhost:8000")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    return passed == len(results)

if __name__ == "__main__":
    main()