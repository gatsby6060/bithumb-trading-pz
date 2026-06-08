import logging
import asyncio
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# Try loading asyncpg (might not be installed or needed if fallback to SQLite)
try:
    import asyncpg
except ImportError:
    asyncpg = None

logger = logging.getLogger("TimescaleDBManager")

class TimescaleDBManager:
    def __init__(self, dsn: str, sqlite_db_path: str = "bithumb_trading.db"):
        """
        dsn: PostgreSQL connection string
        sqlite_db_path: Fallback SQLite database file path
        """
        self.dsn = dsn
        self.sqlite_db_path = sqlite_db_path
        self.pool: Optional[Any] = None
        self.use_sqlite = False
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def initialize(self):
        """
        Initialize connection pool. If PostgreSQL/TimescaleDB connection fails,
        automatically fall back to local SQLite to ensure 100% execution success.
        """
        if asyncpg is None:
            logger.warning("asyncpg module not found. Falling back to local SQLite database.")
            self.use_sqlite = True
            await self._initialize_sqlite()
            return

        try:
            logger.info("Attempting to connect to TimescaleDB...")
            # Try to connect with a short timeout to prevent long hanging
            self.pool = await asyncio.wait_for(
                asyncpg.create_pool(dsn=self.dsn, min_size=1, max_size=5),
                timeout=3.0
            )
            # Create necessary tables and views for PostgreSQL
            await self._create_postgres_tables()
            logger.info("Connected to TimescaleDB successfully.")
        except (Exception, asyncio.TimeoutError) as e:
            logger.warning(f"Could not connect to TimescaleDB ({e}). Falling back to local SQLite database.")
            self.use_sqlite = True
            await self._initialize_sqlite()

    async def close(self):
        if self.pool and not self.use_sqlite:
            logger.info("Closing TimescaleDB Connection Pool...")
            await self.pool.close()
            self.pool = None
        self.executor.shutdown(wait=False)

    async def _create_postgres_tables(self):
        async with self.pool.acquire() as conn:
            # Create tick_data
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tick_data (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    trade_price NUMERIC(20, 8) NOT NULL,
                    trade_volume NUMERIC(20, 8) NOT NULL,
                    ask_bid TEXT NOT NULL
                );
            """)

            # Try to turn it into a TimescaleDB hypertable
            try:
                extension_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'timescaledb');"
                )
                if extension_exists:
                    is_hyper = await conn.fetchval("""
                        SELECT EXISTS(
                            SELECT 1 FROM _timescaledb_catalog.hypertable 
                            WHERE table_name = 'tick_data'
                        );
                    """)
                    if not is_hyper:
                        await conn.execute("SELECT create_hypertable('tick_data', 'time');")
                        logger.info("Created TimescaleDB hypertable for tick_data.")
            except Exception as e:
                logger.warning(f"Failed to create hypertable: {e}")

            # Create ohlcv_1m view
            try:
                view_exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_matviews WHERE matviewname = 'ohlcv_1m'
                    );
                """)
                if not view_exists:
                    await conn.execute("""
                        CREATE MATERIALIZED VIEW ohlcv_1m
                        WITH (timescaledb.continuous) AS
                        SELECT
                            time_bucket('1 minute', time) AS bucket,
                            symbol,
                            first(trade_price, time) AS open,
                            max(trade_price) AS high,
                            min(trade_price) AS low,
                            last(trade_price, time) AS close,
                            sum(trade_volume) AS volume
                        FROM tick_data
                        GROUP BY bucket, symbol;
                    """)
                    logger.info("Created continuous aggregate view ohlcv_1m.")
            except Exception as e:
                logger.warning(f"Failed to create continuous aggregate ohlcv_1m: {e}")

            # AI Activity Log
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_activity_log (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT NOT NULL
                );
            """)

            # Trade History Log
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    price NUMERIC(20, 8) NOT NULL,
                    volume NUMERIC(20, 8) NOT NULL,
                    fee NUMERIC(20, 8) DEFAULT 0.0,
                    pnl NUMERIC(20, 8) DEFAULT 0.0
                );
            """)

    async def _initialize_sqlite(self):
        """
        Set up SQLite database schema in a non-blocking thread executor.
        """
        logger.info(f"Initializing local SQLite database: {self.sqlite_db_path}")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self.executor, self._create_sqlite_tables)

    def _create_sqlite_tables(self):
        conn = sqlite3.connect(self.sqlite_db_path)
        try:
            cursor = conn.cursor()
            # SQLite does not support hypertable or TIMESTAMPTZ, we use standard TEXT/TIMESTAMP
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tick_data (
                    time TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    trade_price REAL NOT NULL,
                    trade_volume REAL NOT NULL,
                    ask_bid TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL NOT NULL,
                    fee REAL DEFAULT 0.0,
                    pnl REAL DEFAULT 0.0
                );
            """)
            conn.commit()
            logger.info("SQLite schema initialized successfully.")
        except Exception as e:
            logger.error(f"Error creating SQLite tables: {e}")
        finally:
            conn.close()

    async def insert_tick(self, symbol: str, price: float, volume: float, ask_bid: str, timestamp: Optional[datetime] = None):
        timestamp = timestamp or datetime.utcnow()
        
        if self.use_sqlite:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                self.executor, 
                self._insert_tick_sqlite, 
                symbol, price, volume, ask_bid, timestamp.isoformat()
            )
            return

        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tick_data (time, symbol, trade_price, trade_volume, ask_bid)
                VALUES ($1, $2, $3, $4, $5)
                """,
                timestamp, symbol, price, volume, ask_bid
            )

    def _insert_tick_sqlite(self, symbol: str, price: float, volume: float, ask_bid: str, ts_str: str):
        conn = sqlite3.connect(self.sqlite_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tick_data (time, symbol, trade_price, trade_volume, ask_bid) VALUES (?, ?, ?, ?, ?)",
                (ts_str, symbol, price, volume, ask_bid)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"SQLite tick insert failed: {e}")
        finally:
            conn.close()

    async def get_ohlcv(self, symbol: str, interval_minutes: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        if self.use_sqlite:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self.executor, 
                self._get_ohlcv_sqlite, 
                symbol, interval_minutes, limit
            )

        if not self.pool:
            return []

        async with self.pool.acquire() as conn:
            try:
                if interval_minutes == 1:
                    rows = await conn.fetch(
                        "SELECT bucket as time, open, high, low, close, volume FROM ohlcv_1m WHERE symbol = $1 ORDER BY bucket DESC LIMIT $2",
                        symbol, limit
                    )
                else:
                    rows = await conn.fetch(
                        f"SELECT time_bucket('{interval_minutes} minute', time) AS time, first(trade_price, time) AS open, max(trade_price) AS high, min(trade_price) AS low, last(trade_price, time) AS close, sum(trade_volume) AS volume FROM tick_data WHERE symbol = $1 GROUP BY time ORDER BY time DESC LIMIT $2",
                        symbol, limit
                    )
                return [
                    {"time": r["time"], "open": float(r["open"]), "high": float(r["high"]), "low": float(r["low"]), "close": float(r["close"]), "volume": float(r["volume"])}
                    for r in rows
                ]
            except Exception as e:
                logger.error(f"PostgreSQL OHLCV fetch failed: {e}")
                return []

    def _get_ohlcv_sqlite(self, symbol: str, interval_minutes: int, limit: int) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.sqlite_db_path)
        try:
            cursor = conn.cursor()
            # SQLite standard dynamic OHLCV grouping (grouping by minute bucket using strftime)
            # Standard ISO string is 'YYYY-MM-DDTHH:MM:SS.mmmmmm'
            # We crop the seconds for 1-minute bucket: 'YYYY-MM-DDTHH:MM'
            cursor.execute(
                f"""
                SELECT 
                    strftime('%Y-%m-%dT%H:%M:00', time) AS bucket,
                    trade_price AS open,
                    max(trade_price) AS high,
                    min(trade_price) AS low,
                    trade_price AS close,
                    sum(trade_volume) AS volume
                FROM tick_data
                WHERE symbol = ?
                GROUP BY bucket
                ORDER BY bucket DESC
                LIMIT ?
                """,
                (symbol, limit)
            )
            rows = cursor.fetchall()
            return [
                {
                    "time": r[0],
                    "open": float(r[1]),
                    "high": float(r[2]),
                    "low": float(r[3]),
                    "close": float(r[4]),
                    "volume": float(r[5])
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"SQLite OHLCV fetch failed: {e}")
            return []
        finally:
            conn.close()

    async def log_ai_activity(self, symbol: str, action: str, reason: str):
        if self.use_sqlite:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, self._log_ai_activity_sqlite, symbol, action, reason)
            return

        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO ai_activity_log (symbol, action, reason) VALUES ($1, $2, $3)",
                symbol, action, reason
            )

    def _log_ai_activity_sqlite(self, symbol: str, action: str, reason: str):
        conn = sqlite3.connect(self.sqlite_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ai_activity_log (symbol, action, reason) VALUES (?, ?, ?)",
                (symbol, action, reason)
            )
            conn.commit()
            logger.info(f"AI Activity Logged (SQLite): [{symbol}] {action} - Reason: {reason}")
        except Exception as e:
            logger.error(f"SQLite log AI activity failed: {e}")
        finally:
            conn.close()

    async def get_ai_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        if self.use_sqlite:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(self.executor, self._get_ai_activities_sqlite, limit)

        if not self.pool:
            return []

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, timestamp, symbol, action, reason FROM ai_activity_log ORDER BY timestamp DESC LIMIT $1",
                limit
            )
            return [dict(r) for r in rows]

    def _get_ai_activities_sqlite(self, limit: int) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.sqlite_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, timestamp, symbol, action, reason FROM ai_activity_log ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": r[1],
                    "symbol": r[2],
                    "action": r[3],
                    "reason": r[4]
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"SQLite fetch AI activities failed: {e}")
            return []
        finally:
            conn.close()

    async def insert_trade(self, symbol: str, side: str, price: float, volume: float, fee: float = 0.0, pnl: float = 0.0):
        timestamp = datetime.utcnow()
        if self.use_sqlite:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                self.executor,
                self._insert_trade_sqlite,
                symbol, side, price, volume, fee, pnl, timestamp.isoformat()
            )
            return

        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO trade_history (timestamp, symbol, side, price, volume, fee, pnl)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                timestamp, symbol, side, price, volume, fee, pnl
            )

    def _insert_trade_sqlite(self, symbol: str, side: str, price: float, volume: float, fee: float, pnl: float, ts_str: str):
        conn = sqlite3.connect(self.sqlite_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO trade_history (timestamp, symbol, side, price, volume, fee, pnl) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ts_str, symbol, side, price, volume, fee, pnl)
            )
            conn.commit()
            logger.info(f"Trade Logged (SQLite): {side} {volume} {symbol} at {price} KRW")
        except Exception as e:
            logger.error(f"SQLite trade insert failed: {e}")
        finally:
            conn.close()

    async def get_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        if self.use_sqlite:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(self.executor, self._get_trades_sqlite, limit)

        if not self.pool:
            return []

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, timestamp, symbol, side, price, volume, fee, pnl FROM trade_history ORDER BY timestamp DESC LIMIT $1",
                limit
            )
            return [dict(r) for r in rows]

    def _get_trades_sqlite(self, limit: int) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.sqlite_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, timestamp, symbol, side, price, volume, fee, pnl FROM trade_history ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": r[1],
                    "symbol": r[2],
                    "side": r[3],
                    "price": float(r[4]),
                    "volume": float(r[5]),
                    "fee": float(r[6]),
                    "pnl": float(r[7])
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"SQLite fetch trades failed: {e}")
            return []
        finally:
            conn.close()
