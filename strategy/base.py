from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseStrategy(ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    @abstractmethod
    def calculate_score(self, ohlcv: List[Dict[str, Any]]) -> float:
        """
        Calculate strategy score/signal strength.
        ohlcv: List of OHLCV dictionaries in chronological order (oldest to newest)
        Returns: A score between 0.0 and 100.0.
                 - 0.0 means strong sell/bearish signal
                 - 50.0 means neutral/hold signal
                 - 100.0 means strong buy/bullish signal
        """
        pass
