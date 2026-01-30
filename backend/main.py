from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from market_data import MarketDataClient
from strategy import Strategy920
from database import Database
from notifications import NotificationService
import pytz

load_dotenv()

app = FastAPI()

# Enable CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
market_data = MarketDataClient()
strategy = Strategy920()
db = Database()
notifier = NotificationService()

# Watchlist
MAG_7 = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA']

@app.get("/")
async def root():
    return {"status": "920 Strategy Engine Running", "version": "1.0"}

@app.get("/status")
async def get_status():
    """Get current status of all tickers"""
    status = {}
    for ticker in MAG_7:
        bars = await market_data.get_bars(ticker, timeframe='2Min', limit=50)
        if bars is not None and len(bars) > 0:
            trend = strategy.get_trend_status(bars)
            status[ticker] = trend
        else:
            status[ticker] = "ERROR"
    return status

@app.get("/alerts")
async def get_alerts(limit: int = 50):
    """Get recent alerts"""
    alerts = db.get_recent_alerts(limit)
    return alerts

@app.post("/scan")
async def scan_markets():
    """Manually trigger a market scan"""
    alerts = await run_scan()
    return {"alerts_found": len(alerts), "alerts": alerts}

async def run_scan():
    """Main scanning logic"""
    alerts = []
    
    # Check if market is open and after 10 AM ET
    if not is_market_time():
        print("Market closed or before 10 AM ET")
        return alerts
    
    for ticker in MAG_7:
        try:
            # Get 2-minute bars
            bars = await market_data.get_bars(ticker, timeframe='2Min', limit=50)
            
            if bars is None or len(bars) < 30:
                continue
            
            # Run 920 strategy
            setup = strategy.analyze(ticker, bars)
            
            if setup and setup['score'] >= 70:
                # Save to database
                db.save_alert(setup)
                
                # Send push notification
                await notifier.send_alert(setup)
                
                alerts.append(setup)
                print(f"🚨 ALERT: {ticker} {setup['direction']} @ {setup['entry']:.2f} (Score: {setup['score']})")
        
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")
    
    return alerts

def is_market_time():
    """Check if market is open and after 10 AM ET"""
    et_tz = pytz.timezone('America/New_York')
    now_et = datetime.now(et_tz)
    
    # Check if weekday
    if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Market hours: 9:30 AM - 4:00 PM ET
    # We want: after 10:00 AM ET
    hour = now_et.hour
    minute = now_et.minute
    
    if hour < 10:
        return False
    if hour >= 16:
        return False
    
    return True

async def background_scanner():
    """Run scanner every 2 minutes during market hours"""
    while True:
        try:
            if is_market_time():
                print(f"Scanning at {datetime.now()}")
                await run_scan()
                await asyncio.sleep(120)  # 2 minutes
            else:
                # Check every 5 minutes when market closed
                await asyncio.sleep(300)
        except Exception as e:
            print(f"Scanner error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    import uvicorn
    
    # Start background scanner in separate task
    import threading
    def run_background():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(background_scanner())
    
    scanner_thread = threading.Thread(target=run_background, daemon=True)
    scanner_thread.start()
    
    # Start FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)