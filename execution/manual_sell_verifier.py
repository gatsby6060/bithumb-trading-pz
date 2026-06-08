import asyncio
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger("ManualSellVerifier")

class ManualSellVerifier:
    def __init__(self, ai_prediction_func: Callable[[], asyncio.Future]):
        """
        ai_prediction_func: A callable that returns an awaitable Freqai model prediction (returns a score or bounce probability)
        """
        self.ai_prediction_func = ai_prediction_func
        self.timeout = 1.5  # Strict 1.5s timeout constraint

    async def verify_manual_sell(self, symbol: str, price: float, volume: float) -> str:
        """
        Verifies if a manual sell is safe to execute or if a warning should be displayed.
        Returns one of:
        - "EXECUTE": AI says it is safe to sell, or verifier timed out/errored (fallback).
        - "WARN": AI detected an immediate bounce/support level. Trigger confirmation modal in UI.
        """
        logger.info(f"Initiating AI verify (후보고) for manual sell on {symbol}...")
        
        try:
            # Wrap with strict 1.5s timeout
            ai_score = await asyncio.wait_for(self.ai_prediction_func(), timeout=self.timeout)
            logger.info(f"AI short-term verifier returned score: {ai_score:.2f} in time.")
            
            # If AI score is very high (e.g. > 70.0), it suggests strong upward momentum or immediate support bounce.
            # In this case, warn the user.
            if ai_score >= 70.0:
                logger.warning(f"AI Verifier flags bounce probability: {ai_score:.1f}%. Recommending WARN.")
                return "WARN"
            else:
                return "EXECUTE"
                
        except asyncio.TimeoutError:
            # Fallback exception handler: If AI verifier lags (>1.5s), execute the user order immediately to preserve responsiveness.
            logger.warning(f"AI Verifier timed out (> {self.timeout}s). Fallback: EXECUTE user order immediately.")
            return "EXECUTE"
            
        except Exception as e:
            logger.error(f"AI Verifier encountered an error: {e}. Fallback: EXECUTE user order immediately.")
            return "EXECUTE"
