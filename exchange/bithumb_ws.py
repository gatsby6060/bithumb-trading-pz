import asyncio
import json
import logging
import aiohttp
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any

logger = logging.getLogger("BithumbWebsocketClient")

class BithumbWebsocketClient:
    def __init__(self, symbols: List[str], event_queue: asyncio.Queue, base_url: str = "wss://ws-api.bithumb.com/websocket/v1"):
        """
        symbols: List of symbols to subscribe (e.g. ['KRW-BTC', 'KRW-ETH'])
        event_queue: asyncio.Queue to push parsed tick events
        """
        self.symbols = symbols
        self.event_queue = event_queue
        self.base_url = base_url
        self.is_running = False
        self.ws_task: Optional[asyncio.Task] = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.ws_task = asyncio.create_task(self._connect_and_loop())
        logger.info("Bithumb Websocket Client started.")

    async def stop(self):
        self.is_running = False
        if self.ws_task:
            self.ws_task.cancel()
            try:
                await self.ws_task
            except asyncio.CancelledError:
                pass
            self.ws_task = None
        logger.info("Bithumb Websocket Client stopped.")

    async def _connect_and_loop(self):
        backoff = 1.0
        while self.is_running:
            try:
                async with aiohttp.ClientSession() as session:
                    # Bithumb public WS does not require authentication
                    # heartbeat parameter handles keeping connection alive (automatic ping/pong in aiohttp)
                    async with session.ws_connect(self.base_url, heartbeat=30.0) as ws:
                        logger.info(f"Connected to Bithumb Websocket at {self.base_url}")
                        backoff = 1.0  # Reset backoff on successful connection
                        
                        # Subscribe to trades
                        subscribe_payload = [
                            {"ticket": "bithumb-trading-bot-client"},
                            {
                                "type": "trade",
                                "codes": self.symbols,
                                "is_only_realtime": True
                            }
                        ]
                        await ws.send_str(json.dumps(subscribe_payload))
                        logger.info(f"Subscription sent for symbols: {self.symbols}")

                        async for msg in ws:
                            if not self.is_running:
                                break
                            
                            if msg.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
                                try:
                                    if msg.type == aiohttp.WSMsgType.BINARY:
                                        raw_data = msg.data.decode('utf-8')
                                    else:
                                        raw_data = msg.data
                                    data = json.loads(raw_data)
                                    # Parse trade tick data
                                    if isinstance(data, dict) and data.get("type") == "trade":
                                        self._process_trade_message(data)
                                except Exception as parse_err:
                                    logger.error(f"Error parsing message: {parse_err} | raw: {msg.data}")
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                logger.warning("Websocket connection closed by server.")
                                break
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                logger.error("Websocket connection error.")
                                break
            except asyncio.CancelledError:
                logger.info("Websocket connection loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Websocket error in loop: {e}")
                
            if self.is_running:
                logger.info(f"Attempting to reconnect in {backoff} seconds...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)

    def _process_trade_message(self, data: Dict[str, Any]):
        """
        Process the trade tick data from Bithumb.
        Data format:
        {
          "type": "trade",
          "code": "KRW-BTC",
          "trade_price": 91200000.0,
          "trade_volume": 0.005,
          "ask_bid": "BID",
          "trade_date": "2026-06-07",
          "trade_time": "12:30:00",
          "timestamp": 1780834318000
        }
        """
        try:
            symbol = data.get("code")
            price = float(data.get("trade_price"))
            volume = float(data.get("trade_volume"))
            ask_bid = data.get("ask_bid")  # 'ASK' (sell) or 'BID' (buy)
            ts_ms = data.get("timestamp")
            
            # Standardize timestamp
            if ts_ms:
                dt = datetime.fromtimestamp(ts_ms / 1000.0)
            else:
                dt = datetime.utcnow()

            tick_event = {
                "event_type": "tick",
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "ask_bid": ask_bid,
                "timestamp": dt
            }

            # Non-blocking push to queue
            self.event_queue.put_nowait(tick_event)
        except Exception as e:
            logger.error(f"Failed to process trade message: {e} | data: {data}")
