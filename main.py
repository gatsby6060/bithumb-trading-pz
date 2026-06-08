import os
import sys

# Reconfigure stdout/stderr to utf-8 to prevent CP949 encoding errors on Windows when printing emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import asyncio
import signal
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from aiohttp import web


# Import our components
from database.manager import TimescaleDBManager
from exchange.bithumb_rest import BithumbRestClient
from exchange.bithumb_ws import BithumbWebsocketClient
from strategy.engine import StrategyEngine
from strategy.ai_model import FreqaiModel
from execution.risk_manager import RiskManager
from execution.order_executor import OrderExecutor
from execution.manual_sell_verifier import ManualSellVerifier

# Import AI Sentiment components
from ai_engine.sentiment.gemini_analyzer import GeminiSentimentAnalyzer
from ai_engine.sentiment.langchain_analyzer import LangChainSentimentAnalyzer
from ai_engine.agent.robo_agent import RoboAdvisorAgent
from ai_engine.memory.short_term_memory import AgentMemory


# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TradingBotApp")

class WebLogHandler(logging.Handler):
    def __init__(self, log_list_ref):
        super().__init__()
        self.log_list_ref = log_list_ref
    def emit(self, record):
        try:
            self.log_list_ref.append({
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage()
            })
            if len(self.log_list_ref) > 200:
                self.log_list_ref.pop(0)
        except Exception:
            pass

class TradingBotApp:
    def __init__(self):
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.db_manager: Optional[TimescaleDBManager] = None
        self.rest_client: Optional[BithumbRestClient] = None
        self.ws_client: Optional[BithumbWebsocketClient] = None
        self.strategy_engine: Optional[StrategyEngine] = None
        self.ai_model: Optional[FreqaiModel] = None
        self.risk_manager: Optional[RiskManager] = None
        self.order_executor: Optional[OrderExecutor] = None
        self.sell_verifier: Optional[ManualSellVerifier] = None
        
        self.event_queue = asyncio.Queue()
        self.is_running = False
        self.shutdown_triggered = False

        # Configuration (from .env)
        load_dotenv()
        self.access_key = os.getenv("BITHUMB_ACCESS_KEY", "mock_access_key")
        self.secret_key = os.getenv("BITHUMB_SECRET_KEY", "mock_secret_key")
        
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASSWORD", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "bithumb_trading")
        self.db_dsn = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        
        # We will monitor these coins
        self.symbols = ["KRW-BTC", "KRW-ETH"]

        # Real-time state caches
        self.latest_prices = {symbol: 0.0 for symbol in self.symbols}
        self.current_cash = 0.0
        self.current_equity = 0.0
        self.current_positions = []

        # Web server settings
        self.web_port = 8080
        self.ws_clients = set()
        self.web_runner = None
        self.system_logs = []
        self.panic_triggered = False
        self.log_handler = WebLogHandler(self.system_logs)
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        logging.getLogger().addHandler(self.log_handler)

        # In-memory 1-minute OHLCV candle buffer (no DB required)
        # Format: symbol -> list of {time, open, high, low, close, volume}
        self.candle_buffer: Dict[str, list] = {symbol: [] for symbol in self.symbols}
        self._candle_current: Dict[str, Optional[Dict]] = {symbol: None for symbol in self.symbols}
        self.CANDLE_BUFFER_SIZE = 100  # keep last 100 minutes of 1m candles

        # AI Sentiment configurations & state caching
        self.sentiment_analyzer_mode = "langchain"  # Options: "gemini", "langchain", "react"
        self.sentiment_analyzer = None
        self.latest_sentiment = {
            symbol: {
                "sentiment": "Neutral",
                "score": 0.0,
                "summary": "No sentiment analysis performed yet."
            }
            for symbol in self.symbols
        }
        self.last_sentiment_check = {symbol: 0.0 for symbol in self.symbols}
        self.sentiment_check_interval = 300  # 5 minutes


    async def update_account_state(self):
        """
        Fetch real Bithumb accounts and compute total equity, available cash, and active positions.
        Uses live ticker prices for accurate current valuation.
        """
        if not self.rest_client:
            return
            
        try:
            accounts = await self.rest_client.get_accounts()
            if not isinstance(accounts, list):
                logger.error(f"Invalid accounts response structure: {accounts}")
                return
                
            # First pass: collect all non-KRW currencies that have a balance
            currencies_with_balance = [
                acc.get("currency")
                for acc in accounts
                if acc.get("currency") != "KRW"
                and (float(acc.get("balance", 0.0)) + float(acc.get("locked", 0.0))) > 0.0
            ]
            
            # Fetch live ticker prices for all held assets in one batch call
            markets_to_fetch = [f"KRW-{c}" for c in currencies_with_balance]
            live_prices: dict = {}
            if markets_to_fetch:
                live_prices = await self.rest_client.get_tickers(markets_to_fetch)
            
            cash_val = 0.0
            positions = []
            total_equity = 0.0
            
            for acc in accounts:
                currency = acc.get("currency")
                balance = float(acc.get("balance", 0.0))
                locked = float(acc.get("locked", 0.0))
                total_qty = balance + locked
                
                if total_qty <= 0.0:
                    continue
                
                if currency == "KRW":
                    cash_val = total_qty
                    total_equity += total_qty
                else:
                    symbol = f"KRW-{currency}"
                    # Priority: live ticker > cached ws price > avg_buy_price
                    current_price = live_prices.get(symbol, 0.0)
                    if current_price == 0.0:
                        current_price = self.latest_prices.get(symbol, 0.0)
                    
                    avg_buy_price = float(acc.get("avg_buy_price", 0.0))
                    value_in_krw = total_qty * current_price
                    total_equity += value_in_krw
                    
                    if symbol in self.symbols and current_price > 0.0:
                        pnl_pct = 0.0
                        pnl_amount = 0.0
                        if avg_buy_price > 0.0:
                            pnl_pct = ((current_price - avg_buy_price) / avg_buy_price) * 100.0
                            pnl_amount = (current_price - avg_buy_price) * total_qty
                            
                        positions.append({
                            "symbol": symbol,
                            "entry_price": avg_buy_price,
                            "current_price": current_price,
                            "volume": total_qty,
                            "pnl_pct": pnl_pct,
                            "pnl_amount": pnl_amount
                        })
            
            self.current_cash = cash_val
            self.current_equity = total_equity
            self.current_positions = positions
            
            logger.info(f"Account state updated: Cash={self.current_cash:.2f} KRW, Total Equity={self.current_equity:.2f} KRW, Monitored Positions={len(positions)}")
            
        except Exception as e:
            logger.error(f"Failed to update account state: {e}")

    async def initialize(self):
        logger.info("Initializing all system components...")
        self.loop = asyncio.get_running_loop()

        # 1. Database Manager
        self.db_manager = TimescaleDBManager(self.db_dsn)
        try:
            await self.db_manager.initialize()
        except Exception as dbe:
            logger.error(f"Failed to connect to TimescaleDB: {dbe}. Database operations will be bypassed.")
            # We don't crash the bot immediately for testing purposes, but keep going with warnings
            self.db_manager = None

        # 2. Bithumb Rest Client
        self.rest_client = BithumbRestClient(self.access_key, self.secret_key)
        await self.rest_client.initialize()

        # 3. Order Executor
        self.order_executor = OrderExecutor(self.rest_client, self.db_manager)

        # 4. Risk Manager
        self.risk_manager = RiskManager(risk_limit_ratio=0.02) # 2% Rule

        # 5. Freqai Model
        self.ai_model = FreqaiModel("bithumb_lgb_v1")

        # 6. Manual Sell Verifier with 1.5s timeout logic
        # We pass a lambda that runs the ai model's prediction
        self.sell_verifier = ManualSellVerifier(
            ai_prediction_func=lambda: self.ai_model.predict_async([])
        )

        # 7. Strategy Engine (Strategy Mixer)
        self.strategy_engine = StrategyEngine()
        # Initialize default weights: 40% Freqai (AI), 20% Sentiment (LLM), 20% Bollinger, 20% RSI
        default_weights = {"AI": 0.4, "SENTIMENT": 0.2, "BOLLINGER": 0.2, "RSI": 0.2}
        for symbol in self.symbols:
            self.strategy_engine.register_symbol(symbol, default_weights, autopilot_on=True)

        # Initialize Sentiment Analyzer
        self.initialize_sentiment_analyzer()

        # 8. Bithumb Websocket Client
        self.ws_client = BithumbWebsocketClient(self.symbols, self.event_queue)


        # Signal handlers for Graceful Shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                self.loop.add_signal_handler(sig, lambda: asyncio.create_task(self.handle_shutdown_signal(sig)))
            except NotImplementedError:
                # Windows doesn't support add_signal_handler via asyncio loop fully for all signals
                pass

        logger.info("All components initialized successfully.")
        await self.update_account_state()
        
        # Pre-load historical candles so strategy indicators work from the first tick
        await self.prefetch_historical_candles()

    async def prefetch_historical_candles(self):
        """
        Fetch 200 most recent 1-minute candles from Bithumb public API for each monitored symbol.
        Uses current KST time as the 'to' boundary so data is always fresh.
        Populates self.candle_buffer so RSI, Bollinger, MACD etc. compute real signals immediately.
        """
        from datetime import datetime, timezone, timedelta
        
        KST = timezone(timedelta(hours=9))
        now_kst = datetime.now(KST)
        # Format: 'yyyy-MM-dd HH:mm:ss'  — use current minute + 1 to include the current forming candle
        to_str = now_kst.strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"Pre-fetching historical candles (to={to_str} KST) for symbols: {self.symbols}")
        
        for symbol in self.symbols:
            try:
                candles = await self.rest_client.get_candles(
                    market=symbol,
                    unit=1,
                    count=200,
                    to=to_str
                )
                
                if candles:
                    # The last candle (most recent complete minute) goes into the buffer;
                    # the current incomplete candle will be built live from ticks.
                    self.candle_buffer[symbol] = candles  # all 200 as baseline
                    logger.info(f"[{symbol}] Loaded {len(candles)} historical 1m candles. "
                                f"Range: {candles[0]['time'].strftime('%H:%M')} ~ {candles[-1]['time'].strftime('%H:%M')} KST")
                else:
                    logger.warning(f"[{symbol}] No historical candles returned from API.")
                    
            except Exception as e:
                logger.error(f"Failed to prefetch candles for {symbol}: {e}")
        
        logger.info("Historical candle pre-fetch complete. Strategy indicators are ready.")

    def initialize_sentiment_analyzer(self):
        logger.info(f"Initializing AI Sentiment Analyzer (Mode: {self.sentiment_analyzer_mode})...")
        try:
            if self.sentiment_analyzer_mode == "gemini":
                self.sentiment_analyzer = GeminiSentimentAnalyzer()
            elif self.sentiment_analyzer_mode == "langchain":
                self.sentiment_analyzer = LangChainSentimentAnalyzer()
            elif self.sentiment_analyzer_mode == "react":
                self.sentiment_analyzer = RoboAdvisorAgent(verbose=True)
            else:
                logger.error(f"Unknown sentiment mode: {self.sentiment_analyzer_mode}. Defaulting to langchain.")
                self.sentiment_analyzer = LangChainSentimentAnalyzer()
            logger.info("AI Sentiment Analyzer initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize AI Sentiment Analyzer: {e}. Bypassing.")
            self.sentiment_analyzer = None

    def get_recent_memories_for_symbol(self, target_asset: str) -> str:
        try:
            memory = AgentMemory()
            return memory.load_recent_memories(target_asset, limit=5)
        except Exception as e:
            logger.error(f"Failed to load recent memories for {target_asset}: {e}")
            return "메모리를 읽을 수 없습니다."

    async def update_sentiment_in_background(self, symbol: str, price: float):
        if not self.sentiment_analyzer:
            logger.warning("Sentiment Analyzer is not initialized. Skipping update.")
            return

        try:
            target_asset = symbol.split("-")[1]
            keyword_map = {
                "BTC": "비트코인",
                "ETH": "이더리움",
                "XRP": "리플",
                "SOL": "솔라나",
                "ADA": "에이다",
                "DOGE": "도지코인",
            }
            keyword = keyword_map.get(target_asset, target_asset)
            
            logger.info(f"🤖 [SENTIMENT] Fetching latest news for {target_asset}...")
            from data_collectors.news_crawler import NewsCrawler
            crawler = NewsCrawler(keyword)
            news_list = await asyncio.to_thread(crawler.fetch_latest_news)
            
            combined_text = ""
            if news_list:
                target_news = news_list[:10]
                combined_text = "\n".join([
                    f"- [{n['published']}] {n['title']}" for n in target_news
                ])
            else:
                # Fallback to history
                import os, json
                history_file = os.path.join("data", "news_history.json")
                if os.path.exists(history_file):
                    try:
                        with open(history_file, "r", encoding="utf-8") as f:
                            history = json.load(f)
                        history.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
                        target_news = history[:10]
                        combined_text = "\n".join([
                            f"- [{n.get('published', '')}] {n.get('title', '')}" for n in target_news
                        ])
                    except Exception:
                        pass
            
            if not combined_text:
                combined_text = f"{target_asset}에 관한 새로운 뉴스가 없습니다."
                
            logger.info(f"🤖 [SENTIMENT] Running AI analysis for {target_asset} ({self.sentiment_analyzer_mode})...")
            result = await self.sentiment_analyzer.analyze(combined_text, target_asset, price)
            
            self.latest_sentiment[symbol] = {
                "sentiment": result.get("sentiment", "Neutral"),
                "score": float(result.get("score", 0.0)),
                "summary": result.get("summary", "")
            }
            
            # Log inside DB if manager is active
            if self.db_manager:
                try:
                    action_str = f"AI 감성 분석 완료: {result.get('sentiment')} ({result.get('score')})"
                    await self.db_manager.log_ai_activity(symbol, "SENTIMENT_CHECK", action_str)
                except Exception as e:
                    logger.error(f"Failed to log sentiment check activity: {e}")
            
            logger.info(f"🤖 [SENTIMENT] Result for {target_asset}: {result.get('sentiment')} ({result.get('score')}) - Reason: {result.get('summary')}")
            
            # Broadcast to web dashboard
            await self._broadcast_ws({
                "type": "sentiment_update",
                "symbol": symbol,
                "sentiment": result.get("sentiment", "Neutral"),
                "score": float(result.get("score", 0.0)),
                "summary": result.get("summary", ""),
                "past_memory": self.get_recent_memories_for_symbol(target_asset)
            })
            
        except Exception as e:
            logger.error(f"Error updating sentiment in background for {symbol}: {e}")


    async def start(self):
        self.is_running = True
        
        # Start WebSocket connection
        self.ws_client.start()
        
        # Start Web Server
        await self._start_web_server()
        
        # Start Main Event Loop Consumer
        logger.info("Starting main tick consumer loop...")
        await self._consumer_loop()

    async def _consumer_loop(self):
        while self.is_running:
            try:
                # Get the next tick event from the queue
                event = await self.event_queue.get()
                
                event_type = event.get("event_type")
                if event_type == "tick":
                    await self._handle_tick_event(event)
                    
                self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main consumer loop: {e}")

    def _update_candle_buffer(self, symbol: str, price: float, volume: float, ts):
        """
        Build 1-minute OHLCV candles from real-time tick data in memory.
        Each candle covers a 1-minute window.
        """
        if symbol not in self.candle_buffer:
            self.candle_buffer[symbol] = []
            self._candle_current[symbol] = None

        # Determine current minute bucket
        if hasattr(ts, 'replace'):
            minute_key = ts.replace(second=0, microsecond=0)
        else:
            from datetime import datetime
            dt = datetime.fromisoformat(str(ts))
            minute_key = dt.replace(second=0, microsecond=0)

        current = self._candle_current[symbol]

        if current is None or current['time'] != minute_key:
            # New minute: close the old candle and start fresh
            if current is not None:
                self.candle_buffer[symbol].append(current)
                # Trim buffer
                if len(self.candle_buffer[symbol]) > self.CANDLE_BUFFER_SIZE:
                    self.candle_buffer[symbol].pop(0)
            # Open new candle
            self._candle_current[symbol] = {
                'time': minute_key,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume
            }
        else:
            # Update current candle
            current['high'] = max(current['high'], price)
            current['low'] = min(current['low'], price)
            current['close'] = price
            current['volume'] += volume

    async def _handle_tick_event(self, event: Dict[str, Any]):
        symbol = event["symbol"]
        price = event["price"]
        volume = event["volume"]
        ask_bid = event["ask_bid"]
        ts = event["timestamp"]

        logger.debug(f"Tick received: {symbol} | Price: {price} | Vol: {volume} | {ask_bid}")

        # Cache latest price
        self.latest_prices[symbol] = price

        # Trigger periodic background sentiment check (5 minutes interval)
        loop = asyncio.get_running_loop()
        current_time = loop.time()
        if symbol not in self.last_sentiment_check:
            self.last_sentiment_check[symbol] = 0.0
            
        if current_time - self.last_sentiment_check[symbol] > self.sentiment_check_interval:
            self.last_sentiment_check[symbol] = current_time
            asyncio.create_task(self.update_sentiment_in_background(symbol, price))

        # Build in-memory candle from tick
        self._update_candle_buffer(symbol, price, volume, ts)

        # 1. Store raw tick in Database
        if self.db_manager:
            try:
                await self.db_manager.insert_tick(symbol, price, volume, ask_bid, ts)
            except Exception as e:
                logger.error(f"Failed to record tick to database: {e}")

        # 2. Fetch OHLCV candles: DB first, fallback to in-memory buffer
        ohlcv = []
        if self.db_manager:
            try:
                ohlcv = await self.db_manager.get_ohlcv(symbol, interval_minutes=1, limit=30)
            except Exception as e:
                logger.error(f"Failed to retrieve OHLCV: {e}")

        # Fallback: use in-memory candle buffer
        if not ohlcv:
            buffer = list(self.candle_buffer.get(symbol, []))
            # Also include the currently-forming candle
            if self._candle_current.get(symbol):
                buffer = buffer + [self._candle_current[symbol]]
            if buffer:
                ohlcv = buffer
            else:
                # No data at all yet — single tick placeholder
                ohlcv = [{'time': ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': volume}]

        logger.debug(f"OHLCV candles available for {symbol}: {len(ohlcv)}")

        # 3. ML Inference (Async thread pool execution)
        ai_score = 50.0
        if self.ai_model:
            try:
                ai_score = await self.ai_model.predict_async(ohlcv)
            except Exception as e:
                logger.error(f"Freqai prediction error: {e}")

        # Get the latest raw sentiment score [-1, 1], mapping to [0, 100]
        raw_sentiment = self.latest_sentiment.get(symbol, {}).get("score", 0.0)
        sentiment_score_0_100 = 50.0 + (raw_sentiment * 50.0)

        # 4. Strategy Engine Composite Score
        composite_score = self.strategy_engine.calculate_composite_score(symbol, ohlcv, ai_score, sentiment_score_0_100)
        logger.info(f"[{symbol}] Composite Score: {composite_score:.1f} | Candles: {len(ohlcv)} | AI: {ai_score:.1f} | Sentiment: {sentiment_score_0_100:.1f}")
        
        # Broadcast to web dashboard
        await self._broadcast_ws({
            "type": "tick",
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "ask_bid": ask_bid,
            "timestamp": ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
            "ai_score": ai_score,
            "sentiment_score": sentiment_score_0_100,
            "composite_score": composite_score
        })

        
        # 5. Trading Decision
        if composite_score >= 75.0:
            # AUTO BUY: strong buy signal
            logger.info(f"🚨 AUTO BUY TRIGGERED: [{symbol}] Score={composite_score:.2f} (>= 75.0)")
            
            total_equity = self.current_equity
            available_cash = self.current_cash
            stop_loss_price = price * 0.98
            
            safe_size = self.risk_manager.calculate_position_size(total_equity, price, stop_loss_price, available_cash)
            formatted_size = self.risk_manager.format_volume(symbol, safe_size)
            formatted_price = self.risk_manager.format_price(symbol, price)

            if formatted_size > 0.0:
                logger.info(f"Dispatching BUY order: {formatted_size} {symbol} at {formatted_price} KRW (StopLoss: {stop_loss_price} KRW)")
                await self.order_executor.execute_buy(symbol, formatted_price, formatted_size, stop_loss=stop_loss_price)
            else:
                logger.warning(f"AUTO BUY skipped for [{symbol}]: Insufficient cash ({available_cash:.2f} KRW) to place order.")

        elif composite_score <= 25.0:
            # AUTO SELL: strong sell signal — liquidate any open position for this symbol
            logger.info(f"📉 AUTO SELL TRIGGERED: [{symbol}] Score={composite_score:.2f} (<= 25.0)")
            
            # Find held position for this symbol
            held_position = next((p for p in self.current_positions if p["symbol"] == symbol), None)
            
            if held_position and held_position["volume"] > 0.0:
                sell_volume = self.risk_manager.format_volume(symbol, held_position["volume"])
                formatted_price = self.risk_manager.format_price(symbol, price)
                logger.info(f"Dispatching SELL order: {sell_volume} {symbol} at market price ~{formatted_price} KRW")
                await self.order_executor.execute_sell(symbol, formatted_price, sell_volume, is_market=True)
            else:
                logger.info(f"AUTO SELL skipped for [{symbol}]: No position held.")

    async def trigger_manual_sell_flow(self, symbol: str, price: float, volume: float) -> str:
        """
        Public endpoint for UI to call user manual sell orders.
        Implements 1.5s AI short-term verifier holding mechanism (후보고).
        """
        verdict = await self.sell_verifier.verify_manual_sell(symbol, price, volume)
        
        if verdict == "WARN":
            # Retain control and return alert event to UI
            logger.warning(f"Manual sell paused. AI flags bounce. Confirm modal needed for {symbol}.")
            return "SHOW_SELL_WARNING"
        else:
            # Execute immediately
            logger.info(f"AI verification passed (or timed out). Executing manual sell immediately...")
            res = await self.order_executor.execute_sell(symbol, price, volume, is_market=True)
            return "EXECUTED" if res.get("status") != "error" else "FAILED"

    async def _start_web_server(self):
        logger.info(f"Starting Web Server on port {self.web_port}...")
        self.web_app = web.Application()
        self.web_app.add_routes([
            web.get('/ws', self._ws_handler),
            web.get('/api/candles', self._api_candles),
            web.get('/api/dashboard_state', self._api_dashboard_state),
            web.get('/api/ai_activities', self._api_ai_activities),
            web.get('/api/trade_history', self._api_trade_history),
            web.get('/api/system_logs', self._api_system_logs),
            web.get('/api/sentiment_state', self._api_sentiment_state),
            web.post('/api/manual_trade', self._api_manual_trade),
            web.post('/api/manual_sell_verifier', self._api_manual_sell_verifier),
            web.post('/api/update_strategy_weights', self._api_update_strategy_weights),
            web.post('/api/set_autopilot', self._api_set_autopilot),
            web.post('/api/add_symbol', self._api_add_symbol),
            web.post('/api/panic', self._api_panic),
            web.post('/api/set_sentiment_mode', self._api_set_sentiment_mode),
            web.post('/api/trigger_sentiment_update', self._api_trigger_sentiment_update),
        ])

        
        # Serve static files from ./public
        if os.path.exists("./public"):
            self.web_app.router.add_static('/static', path="./public", name='static')
            
            # Helper to serve index.html at root
            async def index_handler(request):
                return web.FileResponse('./public/index.html')
            self.web_app.router.add_get('/', index_handler)
            
        self.web_runner = web.AppRunner(self.web_app)
        await self.web_runner.setup()
        site = web.TCPSite(self.web_runner, '0.0.0.0', self.web_port)
        await site.start()
        logger.info(f"Web Server running at http://localhost:{self.web_port}/")

    async def _stop_web_server(self):
        if self.web_runner:
            logger.info("Stopping Web Server...")
            await self.web_runner.cleanup()
            self.web_runner = None

    async def _broadcast_ws(self, data: Dict[str, Any]):
        if not self.ws_clients:
            return
        msg = json.dumps(data)
        for ws in list(self.ws_clients):
            try:
                await ws.send_str(msg)
            except Exception:
                self.ws_clients.discard(ws)

    async def _ws_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.ws_clients.add(ws)
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    pass
        finally:
            self.ws_clients.discard(ws)
        return ws

    async def _api_candles(self, request):
        symbol = request.rel_url.query.get("symbol", "KRW-BTC")
        limit = int(request.rel_url.query.get("limit", 100))
        
        buffer = self.candle_buffer.get(symbol, [])
        current = self._candle_current.get(symbol)
        
        candles_to_send = list(buffer)
        if current:
            candles_to_send.append(current)
            
        candles_to_send = candles_to_send[-limit:]
        
        result = []
        for c in candles_to_send:
            t = c['time']
            t_str = t.isoformat() if hasattr(t, 'isoformat') else str(t)
            result.append({
                'time': t_str,
                'open': c['open'],
                'high': c['high'],
                'low': c['low'],
                'close': c['close'],
                'volume': c['volume']
            })
            
        return web.json_response(result)

    async def _api_dashboard_state(self, request):
        # Update account state on demand
        await self.update_account_state()
        
        state = {
            "equity": self.current_equity,
            "cash": self.current_cash,
            "risk_limit": self.risk_manager.risk_limit_ratio if self.risk_manager else 0.02,
            "current_risk": 0.0,
            "daily_pnl": 0.0,
            "positions": self.current_positions,
            "symbols": self.symbols,
            "weights": self.strategy_engine.symbol_settings,
            "autopilot": self.strategy_engine.autopilot_modes,
            "status": "PANIC" if self.panic_triggered else ("RUNNING" if self.is_running else "STOPPED")
        }
        return web.json_response(state)

    async def _api_ai_activities(self, request):
        if self.db_manager:
            logs = await self.db_manager.get_ai_activities(limit=50)
            for l in logs:
                if isinstance(l.get("timestamp"), datetime):
                    l["timestamp"] = l["timestamp"].isoformat()
            return web.json_response(logs)
        return web.json_response([])

    async def _api_trade_history(self, request):
        if self.db_manager:
            trades = await self.db_manager.get_trades(limit=50)
            for t in trades:
                if isinstance(t.get("timestamp"), datetime):
                    t["timestamp"] = t["timestamp"].isoformat()
            return web.json_response(trades)
        return web.json_response([])

    async def _api_system_logs(self, request):
        return web.json_response(self.system_logs)

    async def _api_sentiment_state(self, request):
        symbol = request.rel_url.query.get("symbol", "KRW-BTC")
        target_asset = symbol.split("-")[1]
        
        # Load recent memories
        memories = self.get_recent_memories_for_symbol(target_asset)
        
        # Fetch news list from news_history.json
        import os, json
        news_list = []
        history_file = os.path.join("data", "news_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    news_list = json.load(f)
                news_list.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
                # Keep top 10
                news_list = news_list[:10]
            except Exception:
                pass
                
        state = {
            "mode": self.sentiment_analyzer_mode,
            "latest_sentiment": self.latest_sentiment,
            "past_memory": memories,
            "news_list": news_list
        }
        return web.json_response(state)

    async def _api_set_sentiment_mode(self, request):
        try:
            data = await request.json()
            mode = data.get("mode")
            if mode not in ["gemini", "langchain", "react"]:
                return web.json_response({"status": "error", "message": "Invalid sentiment mode"}, status=400)
                
            self.sentiment_analyzer_mode = mode
            self.initialize_sentiment_analyzer()
            
            if self.db_manager:
                action_str = f"AI 감성 분석 모드 변경: {mode.upper()}"
                await self.db_manager.log_ai_activity("GLOBAL", "SENTIMENT_MODE_CHANGE", action_str)
                
            return web.json_response({"status": "success", "mode": self.sentiment_analyzer_mode})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)

    async def _api_trigger_sentiment_update(self, request):
        try:
            data = await request.json()
            symbol = data.get("symbol", "KRW-BTC")
            price = self.latest_prices.get(symbol, 0.0)
            if price == 0.0:
                # Fallback to fetching ticker price
                try:
                    price_info = await self.rest_client.get_tickers([symbol])
                    price = float(price_info.get(symbol, 0.0))
                except Exception:
                    pass
            
            # Run background task immediately
            asyncio.create_task(self.update_sentiment_in_background(symbol, price))
            return web.json_response({"status": "success"})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)


    async def _api_manual_trade(self, request):
        try:
            data = await request.json()
            symbol = data.get("symbol")
            side = data.get("side")
            price = float(data.get("price", 0.0))
            volume = float(data.get("volume", 0.0))
            
            if side.upper() == "BUY":
                res = await self.order_executor.execute_buy(symbol, price, volume)
            else:
                res = await self.order_executor.execute_sell(symbol, price, volume, is_market=True)
                
            return web.json_response({"status": "success", "result": res})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)

    async def _api_manual_sell_verifier(self, request):
        try:
            data = await request.json()
            symbol = data.get("symbol")
            price = float(data.get("price", 0.0))
            volume = float(data.get("volume", 0.0))
            
            verdict = await self.trigger_manual_sell_flow(symbol, price, volume)
            return web.json_response({"status": "success", "verdict": verdict})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)

    async def _api_update_strategy_weights(self, request):
        try:
            data = await request.json()
            symbol = data.get("symbol")
            weights = data.get("weights")
            self.strategy_engine.update_weights(symbol, weights)
            
            if self.db_manager:
                action_str = f"전략 가중치 수동 변경: {weights}"
                await self.db_manager.log_ai_activity(symbol, "WEIGHT_SWAP", action_str)
                
            return web.json_response({"status": "success"})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)

    async def _api_set_autopilot(self, request):
        try:
            data = await request.json()
            symbol = data.get("symbol")
            enabled = bool(data.get("enabled"))
            self.strategy_engine.set_autopilot_mode(symbol, enabled)
            
            if self.db_manager:
                action_str = f"오토파일럿 모드 설정: {enabled}"
                await self.db_manager.log_ai_activity(symbol, "AUTOPILOT_TOGGLE", action_str)
                
            return web.json_response({"status": "success"})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)

    async def _api_add_symbol(self, request):
        try:
            data = await request.json()
            symbol = data.get("symbol")
            weights = data.get("weights", {"AI": 0.5, "BOLLINGER": 0.3, "RSI": 0.2})
            
            if symbol not in self.symbols:
                self.symbols.append(symbol)
                self.strategy_engine.register_symbol(symbol, weights, autopilot_on=True)
                
                self.ws_client.symbols = self.symbols
                await self.ws_client.stop()
                self.ws_client.start()
                
                if self.db_manager:
                    await self.db_manager.log_ai_activity(symbol, "SYMBOL_ADD", "신규 감시 종목 추가 및 초기 전략 설정 완료")
                    
            return web.json_response({"status": "success"})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)

    async def _api_panic(self, request):
        try:
            self.panic_triggered = True
            self.is_running = False
            if self.ws_client:
                asyncio.create_task(self.ws_client.stop())
            if self.order_executor:
                asyncio.create_task(self.order_executor.flatten_positions())
            return web.json_response({"status": "success"})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)

    async def handle_shutdown_signal(self, sig):
        if self.shutdown_triggered:
            return
        self.shutdown_triggered = True
        logger.warning(f"Received termination signal ({sig.name if hasattr(sig, 'name') else sig}). Initiating shutdown...")
        await self.stop()

    async def stop(self):
        self.is_running = False
        
        # Stop Web Server
        await self._stop_web_server()
        
        # 1. Stop Websocket
        if self.ws_client:
            await self.ws_client.stop()
            
        # 2. Trigger OrderExecutor PANIC Flatten Routine
        if self.order_executor:
            # Cancels all active orders and panic-sells all positions to KRW
            await self.order_executor.flatten_positions()

        # 3. Close REST session
        if self.rest_client:
            await self.rest_client.close()

        # 4. Shutdown AI Model thread pool
        if self.ai_model:
            self.ai_model.shutdown()

        # 5. Close DB pool
        if self.db_manager:
            await self.db_manager.close()

        logger.info("Graceful shutdown sequence complete.")
        
        # Stop the running event loop
        try:
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            pass
        
        sys.exit(0)

# Execution Entry Point
if __name__ == "__main__":
    app = TradingBotApp()
    
    # On Windows, Ctrl+C handling fallback
    def win_sigint_handler(sig, frame):
        logger.warning("Ctrl+C detected on Windows. Initiating shutdown...")
        # Since we are in a sync signal handler, schedule the async stop loop
        asyncio.run_coroutine_threadsafe(app.stop(), asyncio.get_event_loop())

    if sys.platform == "win32":
        signal.signal(signal.SIGINT, win_sigint_handler)

    async def run():
        await app.initialize()
        await app.start()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt caught. Closing...")
