import numpy as np
import pandas as pd
from typing import List, Dict, Any
from strategy.base import BaseStrategy

class RSIStrategy(BaseStrategy):
    def calculate_score(self, ohlcv: List[Dict[str, Any]]) -> float:
        if len(ohlcv) < 15:
            return 50.0  # Neutral
        
        df = pd.DataFrame(ohlcv)
        close = df['close']
        
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Translate RSI (0~100) to strategy score (0~100)
        # Low RSI (oversold) -> Buy signal (high score)
        # High RSI (overbought) -> Sell signal (low score)
        if current_rsi <= 30:
            # Oversold, strong buy signal
            return 80.0 + (30 - current_rsi) * 0.67  # Max 100
        elif current_rsi >= 70:
            # Overbought, strong sell signal
            return 20.0 - (current_rsi - 70) * 0.67  # Min 0
        else:
            # Linear mapping between 30 and 70 to 80 and 20
            return 80.0 - (current_rsi - 30) * 1.5

class BollingerBandsStrategy(BaseStrategy):
    def calculate_score(self, ohlcv: List[Dict[str, Any]]) -> float:
        if len(ohlcv) < 20:
            return 50.0
        
        df = pd.DataFrame(ohlcv)
        close = df['close']
        
        sma = close.rolling(window=20).mean()
        std = close.rolling(window=20).std()
        
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std
        
        current_close = close.iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        band_width = current_upper - current_lower + 1e-9
        position = (current_close - current_lower) / band_width
        
        # Position: 0 at lower band, 1 at upper band
        # Below lower band (position <= 0) -> Strong buy (100)
        # Above upper band (position >= 1) -> Strong sell (0)
        score = (1 - position) * 100.0
        return max(0.0, min(100.0, score))

class MACDStrategy(BaseStrategy):
    def calculate_score(self, ohlcv: List[Dict[str, Any]]) -> float:
        if len(ohlcv) < 26:
            return 50.0
        
        df = pd.DataFrame(ohlcv)
        close = df['close']
        
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        hist = current_macd - current_signal
        
        # Pos hist -> Bullish (score > 50)
        # Neg hist -> Bearish (score < 50)
        score = 50.0 + (hist / (close.iloc[-1] * 0.01 + 1e-9)) * 50.0
        return max(0.0, min(100.0, score))

# Dynamic Mock Indicators mapping to simulate 50+ strategy library
class GenericIndicatorStrategy(BaseStrategy):
    def calculate_score(self, ohlcv: List[Dict[str, Any]]) -> float:
        if len(ohlcv) < 5:
            return 50.0
        # Simple simulated signal based on recent return direction
        df = pd.DataFrame(ohlcv)
        returns = df['close'].pct_change().dropna()
        avg_ret = returns.tail(5).mean()
        
        # Map returns to 0 ~ 100
        score = 50.0 + avg_ret * 5000.0
        return max(0.0, min(100.0, score))

def get_strategy_instance(name: str, config: Dict[str, Any] = None) -> BaseStrategy:
    config = config or {}
    name_upper = name.upper()
    if name_upper == "RSI":
        return RSIStrategy(name, config)
    elif name_upper in ("BOLLINGER", "BB", "BBANDS"):
        return BollingerBandsStrategy(name, config)
    elif name_upper == "MACD":
        return MACDStrategy(name, config)
    else:
        # Fallback to simulated indicator to cover 50+ strategy list
        return GenericIndicatorStrategy(name, config)
