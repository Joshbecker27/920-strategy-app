import pandas as pd
import numpy as np

class Strategy920:
    def __init__(self, tolerance=0.0015):
        self.tolerance = tolerance
    
    def analyze(self, ticker, bars_df):
        """
        Analyze bars for 920 setup
        Returns setup dict if valid, None otherwise
        """
        if len(bars_df) < 30:
            return None
        
        # Make a copy to avoid warnings
        df = bars_df.copy()
        
        # Calculate indicators
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
        
        # Check for long setup
        long_setup = self._check_long_setup(ticker, df)
        if long_setup:
            return long_setup
        
        # Check for short setup
        short_setup = self._check_short_setup(ticker, df)
        if short_setup:
            return short_setup
        
        return None
    
    def _check_long_setup(self, ticker, df):
        """Check for long 920 setup"""
        idx = len(df) - 1
        lookback = 12
        score = 0
        
        # A) Trend qualification
        ema9_above_count = sum(df['ema9'].iloc[-lookback:] > df['ema20'].iloc[-lookback:])
        price_above_ema9 = sum(df['close'].iloc[-lookback:] > df['ema9'].iloc[-lookback:])
        
        # Count EMA crosses
        crosses = 0
        for i in range(len(df) - 30, len(df)):
            if i > 0:
                prev_state = df['ema9'].iloc[i-1] > df['ema20'].iloc[i-1]
                curr_state = df['ema9'].iloc[i] > df['ema20'].iloc[i]
                if prev_state != curr_state:
                    crosses += 1
        
        # Trend not qualified
        if ema9_above_count < 10 or crosses > 2:
            return None
        
        # Score trend
        score += int(25 * (ema9_above_count / 12))
        score += int(20 * (price_above_ema9 / 12))
        if crosses <= 1:
            score += 15
        
        # B) Pullback to EMA20
        current_low = df['low'].iloc[idx]
        current_ema20 = df['ema20'].iloc[idx]
        
        if not (current_low <= current_ema20 * (1 + self.tolerance)):
            return None
        
        # C) VWAP confluence
        current_vwap = df['vwap'].iloc[idx]
        vwap_near_ema20 = abs(current_vwap - current_ema20) / current_ema20 <= self.tolerance
        if vwap_near_ema20:
            score += 20
        
        # D) Entry confirmation
        current_close = df['close'].iloc[idx]
        reclaims_ema20 = current_close > current_ema20
        
        candle_range = df['high'].iloc[idx] - df['low'].iloc[idx]
        close_position = (current_close - df['low'].iloc[idx]) / candle_range if candle_range > 0 else 0
        bullish_momentum = current_close > df['open'].iloc[idx] and close_position >= 0.5
        
        if not (reclaims_ema20 and bullish_momentum):
            return None
        
        score += 10
        
        # E) Time bonus
        score += 10
        
        # Quality filter
        if score < 70:
            return None
        
        # Calculate levels
        swing_low = df['low'].iloc[max(0, idx-3):idx+1].min()
        buffer = current_close * 0.0005
        stop = swing_low - buffer
        
        hod = df['high'].max()
        
        return {
            'ticker': ticker,
            'direction': 'LONG',
            'score': score,
            'entry': float(current_close),
            'stop': float(stop),
            'target1': float(df['ema9'].iloc[idx]),
            'target2': float(hod),
            'ema9': float(df['ema9'].iloc[idx]),
            'ema20': float(current_ema20),
            'vwap': float(current_vwap),
            'price': float(current_close),
            'time': df['time'].iloc[idx],
            'reason': [
                f"Trend: {ema9_above_count}/12 bars EMA9>EMA20",
                f"Price respects EMA9: {price_above_ema9}/12",
                "✓ VWAP confluence" if vwap_near_ema20 else "",
                "Reclaimed EMA20 with momentum",
                "✓ Clean trend" if crosses <= 1 else ""
            ]
        }
    
    def _check_short_setup(self, ticker, df):
        """Check for short 920 setup (mirror of long)"""
        idx = len(df) - 1
        lookback = 12
        score = 0
        
        # A) Trend qualification (SHORT)
        ema9_below_count = sum(df['ema9'].iloc[-lookback:] < df['ema20'].iloc[-lookback:])
        price_below_ema9 = sum(df['close'].iloc[-lookback:] < df['ema9'].iloc[-lookback:])
        
        crosses = 0
        for i in range(len(df) - 30, len(df)):
            if i > 0:
                prev_state = df['ema9'].iloc[i-1] < df['ema20'].iloc[i-1]
                curr_state = df['ema9'].iloc[i] < df['ema20'].iloc[i]
                if prev_state != curr_state:
                    crosses += 1
        
        if ema9_below_count < 10 or crosses > 2:
            return None
        
        score += int(25 * (ema9_below_count / 12))
        score += int(20 * (price_below_ema9 / 12))
        if crosses <= 1:
            score += 15
        
        # B) Pullback to EMA20 (from below)
        current_high = df['high'].iloc[idx]
        current_ema20 = df['ema20'].iloc[idx]
        
        if not (current_high >= current_ema20 * (1 - self.tolerance)):
            return None
        
        # C) VWAP confluence
        current_vwap = df['vwap'].iloc[idx]
        vwap_near_ema20 = abs(current_vwap - current_ema20) / current_ema20 <= self.tolerance
        if vwap_near_ema20:
            score += 20
        
        # D) Entry confirmation
        current_close = df['close'].iloc[idx]
        breaks_ema20 = current_close < current_ema20
        
        candle_range = df['high'].iloc[idx] - df['low'].iloc[idx]
        close_position = (current_close - df['low'].iloc[idx]) / candle_range if candle_range > 0 else 0
        bearish_momentum = current_close < df['open'].iloc[idx] and close_position <= 0.5
        
        if not (breaks_ema20 and bearish_momentum):
            return None
        
        score += 10
        score += 10  # Time bonus
        
        if score < 70:
            return None
        
        # Calculate levels
        swing_high = df['high'].iloc[max(0, idx-3):idx+1].max()
        buffer = current_close * 0.0005
        stop = swing_high + buffer
        
        lod = df['low'].min()
        
        return {
            'ticker': ticker,
            'direction': 'SHORT',
            'score': score,
            'entry': float(current_close),
            'stop': float(stop),
            'target1': float(df['ema9'].iloc[idx]),
            'target2': float(lod),
            'ema9': float(df['ema9'].iloc[idx]),
            'ema20': float(current_ema20),
            'vwap': float(current_vwap),
            'price': float(current_close),
            'time': df['time'].iloc[idx],
            'reason': [
                f"Trend: {ema9_below_count}/12 bars EMA9<EMA20",
                f"Price respects EMA9: {price_below_ema9}/12",
                "✓ VWAP confluence" if vwap_near_ema20 else "",
                "Broke EMA20 with momentum",
                "✓ Clean trend" if crosses <= 1 else ""
            ]
        }
    
    def get_trend_status(self, df):
        """Get current trend status for a ticker"""
        if len(df) < 20:
            return "NEUTRAL"
        
        # Make a copy
        df = df.copy()
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        
        if df['ema9'].iloc[-1] > df['ema20'].iloc[-1]:
            return "LONG-ELIGIBLE"
        elif df['ema9'].iloc[-1] < df['ema20'].iloc[-1]:
            return "SHORT-ELIGIBLE"
        else:
            return "NEUTRAL"