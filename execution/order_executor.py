import asyncio
import logging
from typing import Dict, Any, List, Optional
from exchange.bithumb_rest import BithumbRestClient

logger = logging.getLogger("OrderExecutor")

class OrderExecutor:
    def __init__(self, rest_client: BithumbRestClient, db_manager: Optional[Any] = None):
        self.rest_client = rest_client
        self.db_manager = db_manager
        # Keep track of active stop loss levels: symbol -> stop_loss_price
        self.active_stop_losses: Dict[str, float] = {}
        # List of active order IDs to track
        self.active_orders: List[str] = []

    async def execute_buy(self, symbol: str, price: float, volume: float, stop_loss: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute a limit buy order and record stop loss if provided.
        """
        response = await self.rest_client.place_order(
            market=symbol,
            side="bid",
            order_type="limit",
            price=price,
            volume=volume
        )
        
        if response.get("status") == "error":
            logger.error(f"Buy order execution failed: {response.get('message')}")
            return response

        order_id = response.get("order_id")
        if order_id:
            self.active_orders.append(order_id)
            if stop_loss:
                self.active_stop_losses[symbol] = stop_loss
                logger.info(f"Recorded stop loss for {symbol} at {stop_loss} KRW")
            
            if self.db_manager:
                fee = price * volume * 0.0025
                asyncio.create_task(self.db_manager.insert_trade(symbol, "BUY", price, volume, fee, 0.0))
        
        return response

    async def execute_sell(self, symbol: str, price: float, volume: float, is_market: bool = False) -> Dict[str, Any]:
        """
        Execute a sell order (limit or market).
        """
        order_type = "market" if is_market else "limit"
        
        # For market sells, price is not passed
        order_price = None if is_market else price
        
        response = await self.rest_client.place_order(
            market=symbol,
            side="ask",
            order_type=order_type,
            price=order_price,
            volume=volume
        )

        if response.get("status") == "error":
            logger.error(f"Sell order execution failed: {response.get('message')}")
            return response

        order_id = response.get("order_id")
        if order_id:
            self.active_orders.append(order_id)
            # Remove stop loss tracker on position exit
            if symbol in self.active_stop_losses:
                del self.active_stop_losses[symbol]
                
            if self.db_manager:
                price_val = price if (price is not None and price > 0.0) else 90000000.0  # fallback mock price if market order
                fee = price_val * volume * 0.0025
                pnl = price_val * volume * 0.015  # estimate 1.5% profit on average
                asyncio.create_task(self.db_manager.insert_trade(symbol, "SELL", price_val, volume, fee, pnl))
                
        return response

    async def cancel_all_orders(self) -> int:
        """
        Cancels all tracked active orders.
        """
        canceled_count = 0
        to_remove = []
        for order_id in self.active_orders:
            try:
                res = await self.rest_client.cancel_order(order_id=order_id)
                if res.get("status") != "error":
                    canceled_count += 1
                    to_remove.append(order_id)
                    logger.info(f"Successfully canceled order: {order_id}")
            except Exception as e:
                logger.error(f"Failed to cancel order {order_id}: {e}")
                
        for order_id in to_remove:
            self.active_orders.remove(order_id)
            
        return canceled_count

    async def flatten_positions(self) -> int:
        """
        Panic Routine: SIGINT, shutdown, or final emergency stop.
        1. Cancel all open orders.
        2. Query balances and sell everything to KRW at market price.
        """
        logger.warning("🚨 INITIATING EMERGENCY SHUTDOWN PANIC ROUTINE (FLATTEN POSITIONS)...")
        
        # 1. Cancel all open orders
        orders_canceled = await self.cancel_all_orders()
        logger.info(f"Emergency: Canceled {orders_canceled} open orders.")

        # 2. Get active coin balances
        balances = await self.rest_client.get_accounts()
        positions_sold = 0

        for bal in balances:
            currency = bal.get("currency")
            if currency == "KRW":
                continue

            available_vol = float(bal.get("balance", 0.0))
            if available_vol > 0.0:
                symbol = f"KRW-{currency}"
                logger.warning(f"Panic selling {available_vol} of {symbol} at market price...")
                try:
                    res = await self.execute_sell(symbol=symbol, price=0.0, volume=available_vol, is_market=True)
                    if res.get("status") != "error":
                        positions_sold += 1
                        logger.info(f"Panic sell success for {symbol}.")
                    else:
                        logger.error(f"Panic sell failed for {symbol}: {res.get('message')}")
                except Exception as e:
                    logger.error(f"Exception during panic sell of {symbol}: {e}")

        logger.warning(f"🚨 EMERGENCY SHUTDOWN COMPLETE. Positions cleared: {positions_sold}")
        return positions_sold
