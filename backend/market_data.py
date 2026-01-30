import os
import requests
import pandas as pd
from datetime import datetime, timedelta

class MarketDataClient:
    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env file")
    
    async def get_bars(self, symbol, timeframe='2Min', limit=50):
        """Get historical bars from Alpaca"""
        
        headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key
        }
        
        # Alpaca data API endpoint
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
        
        # Calculate start time (get enough bars)
        end = datetime.now()
        start = end - timedelta(days=2)  # Get last 2 days of data
        
        params = {
            'timeframe': timeframe,
            'start': start.isoformat() + 'Z',
            'end': end.isoformat() + 'Z',
            'limit': limit,
            'feed': 'iex',  # Use IEX for real-time free data
            'adjustment': 'raw'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Alpaca API error for {symbol}: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            
            if 'bars' not in data or not data['bars']:
                print(f"No bar data for {symbol}")
                return None
            
            # Convert to DataFrame
            bars = []
            for bar in data['bars']:
                bars.append({
                    'time': pd.to_datetime(bar['t']),
                    'open': float(bar['o']),
                    'high': float(bar['h']),
                    'low': float(bar['l']),
                    'close': float(bar['c']),
                    'volume': int(bar['v'])
                })
            
            df = pd.DataFrame(bars)
            
            # Get last N bars
            if len(df) > limit:
                df = df.tail(limit)
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None