import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("RiskManager")

class RiskManager:
    def __init__(self, risk_limit_ratio: float = 0.02):
        """
        risk_limit_ratio: Max loss allowed per trade as fraction of total equity (default: 2%)
        """
        self.risk_limit_ratio = risk_limit_ratio

    def calculate_position_size(self, total_equity: float, entry_price: float, stop_loss_price: float, available_balance: float) -> float:
        """
        Calculates safe position size based on the 2% risk rule.
        Max Loss = Total Equity * 0.02
        Position Size = Max Loss / (Entry Price - Stop Loss Price)
        """
        if entry_price <= stop_loss_price:
            logger.warning("Stop loss price must be below entry price for a buy order.")
            return 0.0

        max_loss = total_equity * self.risk_limit_ratio
        loss_per_coin = entry_price - stop_loss_price
        
        # Safe position size in coin units
        position_size = max_loss / loss_per_coin
        
        # Double check if we have enough available cash balance
        required_cash = position_size * entry_price
        if required_cash > available_balance:
            logger.info(f"Calculated size ({position_size} coins) requires {required_cash} KRW, but only {available_balance} KRW available. Sizing down.")
            position_size = available_balance / entry_price
            
        return position_size

    def format_volume(self, symbol: str, volume: float) -> float:
        """
        Formats volume based on coin-specific tick size/precision rules.
        Typically BTC/ETH have higher precision (e.g. 4 decimals), XRP has lower (e.g. 1 decimal).
        """
        # Simple rule: BTC has 4 decimals, others 2, XRP 1 decimal.
        if "BTC" in symbol:
            return round(volume, 4)
        elif "ETH" in symbol:
            return round(volume, 4)
        elif "XRP" in symbol:
            return round(volume, 1)
        else:
            return round(volume, 2)

    def format_price(self, symbol: str, price: float) -> float:
        """
        Format price based on Bithumb tick size rules.
        """
        # Bithumb tick sizes:
        # > 2,000,000 KRW: tick size 1000
        # 1,000,000 ~ 2,000,000 KRW: tick size 500
        # 500,000 ~ 1,000,000 KRW: tick size 100
        # < 1,000 KRW: tick size 1 or 0.1
        if price >= 2000000:
            return float(int(price / 1000) * 1000)
        elif price >= 1000000:
            return float(int(price / 500) * 500)
        elif price >= 500000:
            return float(int(price / 100) * 100)
        elif price >= 100000:
            return float(int(price / 50) * 50)
        elif price >= 10000:
            return float(int(price / 10) * 10)
        elif price >= 1000:
            return float(int(price / 1) * 1)
        else:
            return float(round(price, 1))
