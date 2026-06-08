import asyncio
import logging
import random
import sys
from datetime import datetime
from main import TradingBotApp

# Setup logging to print to stdout with INFO level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SimulationRunner")

class MockRestClient:
    async def initialize(self):
        pass
    async def close(self):
        pass
    async def place_order(self, market: str, side: str, order_type: str, price=None, volume=None, client_order_id=None):
        logger.info(f"[Mock REST] Order placed: {side} {volume} {market} at {price} KRW")
        return {"status": "success", "order_id": f"mock-order-{random.randint(1000, 9999)}"}
    async def get_accounts(self):
        return [
            {"currency": "KRW", "balance": "10000000.0"},
            {"currency": "BTC", "balance": "0.05"},
            {"currency": "ETH", "balance": "0.5"}
        ]
    async def cancel_order(self, order_id=None, client_order_id=None):
        logger.info(f"[Mock REST] Order canceled: {order_id or client_order_id}")
        return {"status": "success"}

async def mock_websocket_feed(event_queue: asyncio.Queue, is_running_flag):
    btc_price = 92000000.0
    eth_price = 4500000.0
    
    logger.info("Starting Mock WebSocket Tick Generator Feed...")
    
    while is_running_flag():
        # Generate slightly fluctuating prices
        btc_price += random.uniform(-100000.0, 150000.0) # Upward bias to trigger buy
        eth_price += random.uniform(-5000.0, 8000.0)
        
        # Randomly choose BTC or ETH
        symbol = "KRW-BTC" if random.random() < 0.5 else "KRW-ETH"
        price = btc_price if symbol == "KRW-BTC" else eth_price
        volume = random.uniform(0.01, 0.5) if symbol == "KRW-BTC" else random.uniform(0.1, 2.0)
        ask_bid = "BID" if random.random() < 0.55 else "ASK"
        
        tick_event = {
            "event_type": "tick",
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "ask_bid": ask_bid,
            "timestamp": datetime.utcnow()
        }
        
        # Push to queue
        event_queue.put_nowait(tick_event)
        await asyncio.sleep(0.5) # Send tick every 0.5 seconds

async def run_simulation():
    app = TradingBotApp()
    
    # Initialize components
    await app.initialize()
    
    # Replace the real REST client with our mock
    app.rest_client = MockRestClient()
    app.order_executor.rest_client = app.rest_client
    
    # Start Websocket client (mocked logic)
    # We override the ws_client.start to run our mock_websocket_feed
    ws_running = True
    ws_feed_task = asyncio.create_task(mock_websocket_feed(app.event_queue, lambda: ws_running))
    
    # We replace ws_client.stop to stop the mock feed
    async def mock_ws_stop():
        nonlocal ws_running
        ws_running = False
        ws_feed_task.cancel()
        try:
            await ws_feed_task
        except asyncio.CancelledError:
            pass
        logger.info("Mock WebSocket Feed stopped.")
        
    app.ws_client.stop = mock_ws_stop
    
    # Run the main tick consumer loop in the background
    app.is_running = True
    consumer_task = asyncio.create_task(app._consumer_loop())
    logger.info("Simulation main consumer loop started.")
    
    # Run simulation for 12 seconds
    await asyncio.sleep(12.0)
    
    # Test manual sell flow verifier!
    logger.info("--------------------------------------------------")
    logger.info("Testing Manual Sell Flow (후보고) via UI Trigger...")
    verdict = await app.trigger_manual_sell_flow("KRW-BTC", 92500000.0, 0.01)
    logger.info(f"Manual Sell Flow Verdict: {verdict}")
    logger.info("--------------------------------------------------")
    
    # Stop the app
    logger.info("Stopping simulation...")
    await app.stop()
    consumer_task.cancel()
    
if __name__ == "__main__":
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        logger.info("Simulation ended by user.")
    except Exception as e:
        logger.error(f"Simulation error: {e}", exc_info=True)
