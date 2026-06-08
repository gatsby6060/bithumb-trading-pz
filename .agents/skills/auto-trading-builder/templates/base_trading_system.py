import abc
import threading
import queue
import time
from typing import Dict, List, Any

class BaseStrategy(abc.ABC):
    def __init__(self, name: str):
        self.name = name
    @abc.abstractmethod
    def generate_signal(self, stock_data: Dict[str, Any]) -> str:
        pass

class BaseRiskManager(abc.ABC):
    def __init__(self, name: str):
        self.name = name
    @abc.abstractmethod
    def check_risk(self, stock_info: Dict[str, Any], current_signal: str) -> bool:
        pass

class CompositeStrategy(BaseStrategy):
    def __init__(self, strategies: List[BaseStrategy], logic: str = "AND"):
        super().__init__("Composite")
        self.strategies = strategies
        self.logic = logic
    def generate_signal(self, stock_data: Dict[str, Any]) -> str:
        signals = [s.generate_signal(stock_data) for s in self.strategies]
        if self.logic == "AND":
            return "BUY" if all(s == "BUY" for s in signals) else ("SELL" if any(s == "SELL" for s in signals) else "HOLD")
        return "BUY" if any(s == "BUY" for s in signals) else ("SELL" if all(s == "SELL" for s in signals) else "HOLD")

class StockThread(threading.Thread):
    def __init__(self, ticker: str, strategy: BaseStrategy, risk: BaseRiskManager, data_q: queue.Queue, order_q: queue.Queue, acc_lock: threading.Lock, acc_info: Dict):
        super().__init__()
        self.ticker, self.strategy, self.risk, self.data_q, self.order_q, self.acc_lock, self.acc_info = ticker, strategy, risk, data_q, order_q, acc_lock, acc_info
        self._stop = threading.Event()
    def run(self):
        while not self._stop.is_set():
            try:
                data = self.data_q.get(timeout=1)
                # Logic here...
                self.data_q.task_done()
            except queue.Empty: pass
    def stop(self): self._stop.set()
