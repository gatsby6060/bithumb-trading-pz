import logging
from typing import Dict, Any, List, Optional
from strategy.indicators import get_strategy_instance
from strategy.base import BaseStrategy

logger = logging.getLogger("StrategyEngine")

class StrategyEngine:
    def __init__(self):
        # symbol -> strategy_name -> weight float
        # weights sum should ideally be 1.0
        self.symbol_settings: Dict[str, Dict[str, float]] = {}
        # Cached strategy instances per symbol: symbol -> strategy_name -> BaseStrategy
        self.strategy_instances: Dict[str, Dict[str, BaseStrategy]] = {}
        # Autopilot modes per symbol: symbol -> bool (True: AI manages weights, False: Manual slider weights)
        self.autopilot_modes: Dict[str, bool] = {}

    def register_symbol(self, symbol: str, initial_weights: Dict[str, float], autopilot_on: bool = False):
        """
        Register a coin symbol and set up its initial strategy mixer weights.
        initial_weights format: {"RSI": 0.3, "BOLLINGER": 0.4, "MACD": 0.1, "AI": 0.2}
        At most 10 strategies are mixed.
        """
        if len(initial_weights) > 10:
            raise ValueError("Mixer capacity limit exceeded. Maximum of 10 strategies can be mixed.")

        self.symbol_settings[symbol] = initial_weights
        self.autopilot_modes[symbol] = autopilot_on
        self.strategy_instances[symbol] = {}
        
        # Instantiate indicator strategies
        for name in initial_weights.keys():
            if name.upper() != "AI":
                self.strategy_instances[symbol][name] = get_strategy_instance(name)
        
        logger.info(f"Registered symbol '{symbol}' with strategy weights: {initial_weights} (Autopilot: {autopilot_on})")

    def update_weights(self, symbol: str, new_weights: Dict[str, float]):
        """
        Hot-swap strategy weights in memory without restarting the bot loop.
        """
        if len(new_weights) > 10:
            raise ValueError("Mixer capacity limit exceeded. Maximum of 10 strategies can be mixed.")

        if symbol not in self.symbol_settings:
            logger.warning(f"Symbol {symbol} is not registered. Registering now.")
            self.strategy_instances[symbol] = {}

        self.symbol_settings[symbol] = new_weights
        
        # Instantiate any new strategies that were not previously cached
        for name in new_weights.keys():
            if name.upper() != "AI" and name not in self.strategy_instances[symbol]:
                self.strategy_instances[symbol][name] = get_strategy_instance(name)
                
        # Clean up any removed strategy instances
        removed_strategies = [k for k in self.strategy_instances[symbol].keys() if k not in new_weights]
        for name in removed_strategies:
            del self.strategy_instances[symbol][name]

        logger.info(f"Hot-swapped strategy weights for '{symbol}': {new_weights}")

    def set_autopilot_mode(self, symbol: str, enabled: bool):
        self.autopilot_modes[symbol] = enabled
        logger.info(f"Autopilot mode for '{symbol}' set to: {enabled}")

    def calculate_composite_score(self, symbol: str, ohlcv: List[Dict[str, Any]], ai_score: float, sentiment_score: float = 50.0) -> float:
        """
        Calculate composite trading score (0.0 to 100.0) based on weighted average of mixed strategies.
        If a strategy calculation fails, it defaults to neutral (50.0).
        """
        if symbol not in self.symbol_settings:
            return 50.0 # Neutral fallback

        weights = self.symbol_settings[symbol]
        if not weights:
            return 50.0

        total_weight = sum(weights.values())
        if total_weight == 0:
            return 50.0

        composite_score = 0.0
        for name, weight in weights.items():
            if name.upper() == "AI":
                score = ai_score
            elif name.upper() == "SENTIMENT":
                score = sentiment_score
            else:
                strategy_inst = self.strategy_instances[symbol].get(name)
                if strategy_inst:
                    try:
                        score = strategy_inst.calculate_score(ohlcv)
                    except Exception as e:
                        logger.error(f"Error executing strategy '{name}' for '{symbol}': {e}")
                        score = 50.0  # Fallback to neutral
                else:
                    score = 50.0

            composite_score += score * weight

        # Normalize score
        final_score = composite_score / total_weight
        return final_score

