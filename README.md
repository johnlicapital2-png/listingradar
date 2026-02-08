# 📊 ListingRadar - Real Amazon Product Tracker

**No fake data. Ever.** Tracks real Amazon ASINs with HTTP verification.

## 🎯 What This Does

- **Real ASIN Verification**: Every Amazon product link is tested before reporting
- **$0→$10M Momentum**: Tracks products on growth trajectories  
- **Live Dashboard**: Auto-updating HTML dashboard with verification status
- **Telegram Alerts**: Notifies when product status changes
- **No Crashes**: Static hosting, no unstable servers

## 🚀 Live Dashboard

**🌐 https://johnlicapital.github.io/listingradar**

## 📋 Current Products Being Tracked

✅ **Apple AirPods Pro (2nd Gen)** - `B0BDHWDR12` - Verified  
✅ **Instant Pot Duo 7-in-1** - `B00FLYWNYQ` - Verified  
✅ **Fire TV Stick 4K Max** - `B08MQZHDQK` - Verified  
✅ **Echo Dot (5th Gen)** - `B09B8V1LZ3` - Verified  
✅ **COSORI Air Fryer Pro** - `B07VT2NC39` - Verified  
✅ **Anker Portable Charger** - `B019GJLER8` - Verified  
✅ **Ninja Foodi Blender** - `B077J8XJJ3` - Verified  
✅ **Ring Video Doorbell** - `B08N5WRWNW` - Verified  
✅ **Bluetooth Earbuds** - `B07SJR6HL3` - Verified  

## 🔄 How It Works

1. **Product Database**: SQLite database of ASINs to track
2. **HTTP Verification**: Each ASIN tested with real Amazon requests  
3. **Status Tracking**: Monitors when products become unavailable
4. **Report Generation**: Updates HTML dashboard with current status
5. **Telegram Integration**: Sends alerts for broken/new products

## 🛠️ Architecture

- **Frontend**: Static HTML/CSS/JS dashboard
- **Backend**: Python verification script  
- **Database**: SQLite for tracking history
- **Hosting**: GitHub Pages (reliable, no crashes)
- **Automation**: Cron jobs for regular updates

## 📈 Previous Project Issues (Fixed)

❌ **Fake ASINs** → ✅ Real HTTP verification  
❌ **Server crashes** → ✅ Static GitHub Pages hosting  
❌ **Mock data** → ✅ Live Amazon API checks  
❌ **Manual updates** → ✅ Automated cron jobs  
❌ **Unverified claims** → ✅ Evidence-based reporting  

## 🔧 Technical Stack

- **Python 3.9+** for verification
- **SQLite** for data persistence
- **Requests** for HTTP verification
- **GitHub Pages** for hosting
- **Telegram Bot API** for notifications
- **Vanilla JS** for frontend (no dependencies)

## 📊 Verification Process

```python
def verify_amazon_asin(asin: str) -> bool:
    url = f"https://amazon.com/dp/{asin}"
    response = requests.get(url, headers=USER_AGENT)
    
    if response.status_code == 200:
        content = response.text.lower()
        return 'add to cart' in content or 'price' in content
    
    return False
```

## 🎯 Deployment

1. **Manual Deploy**: `python3 update-products.py`
2. **Git Deploy**: `git add . && git commit -m "Update" && git push`  
3. **Auto Deploy**: GitHub Pages rebuilds automatically
4. **Live in**: ~2 minutes at johnlicapital.github.io/listingradar

## 📱 Telegram Integration

Connects to group: **ListingRadar** (`-1003762552122`)

**Alert Examples:**
- 🚨 Product became unavailable
- ✅ New trending product detected  
- 📊 Daily verification report
- ⚡ Real-time status changes

## 🎨 Dashboard Features

- **Real-time verification badges** 
- **Working/broken link indicators**
- **Last updated timestamps**
- **Mobile-responsive design**
- **Auto-refresh every 4 hours**
- **Visual status indicators**

## 🔒 Quality Standards

- **No fake data ever** - everything HTTP tested
- **Evidence-based claims** - don't say it works unless verified
- **Graceful failure handling** - broken links clearly marked
- **Rate limiting** - respectful to Amazon's servers
- **Error logging** - capture and report issues

---

Built February 2026 by Chikara 🗿  
**Motto**: *Real data or no data*