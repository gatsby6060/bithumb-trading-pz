import time
import uuid
import hashlib
import jwt
import urllib.parse
import aiohttp
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List

logger = logging.getLogger("BithumbRestClient")

class BithumbRestClient:
    def __init__(self, access_key: str, secret_key: str, base_url: str = "https://api.bithumb.com"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    def _generate_auth_header(self, query_params: Optional[Dict[str, Any]] = None, body_params: Optional[Dict[str, Any]] = None) -> str:
        nonce = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)
        
        payload = {
            "access_key": self.access_key,
            "nonce": nonce,
            "timestamp": timestamp
        }
        
        serialized = ""
        if query_params:
            query_list = []
            for k, v in query_params.items():
                if isinstance(v, list):
                    for val in v:
                        query_list.append((f"{k}[]", str(val)))
                else:
                    query_list.append((k, str(v)))
            serialized = urllib.parse.urlencode(query_list)
        elif body_params:
            body_list = []
            for k, v in body_params.items():
                if isinstance(v, list):
                    for val in v:
                        body_list.append((f"{k}[]", str(val)))
                else:
                    body_list.append((k, str(v)))
            serialized = urllib.parse.urlencode(body_list)
            
        if serialized:
            query_hash = hashlib.sha512(serialized.encode('utf-8')).hexdigest()
            payload["query_hash"] = query_hash
            payload["query_hash_alg"] = "SHA512"
            
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return f"Bearer {token}"

    async def _request(self, method: str, path: str, query_params: Optional[Dict[str, Any]] = None, body_params: Optional[Dict[str, Any]] = None, retries: int = 3) -> Dict[str, Any]:
        """
        Execute an HTTP request with automatic retry on 429 Rate Limit.
        """
        if not self.session:
            await self.initialize()

        url = f"{self.base_url}{path}"
        
        # Format authorization headers
        auth_header = self._generate_auth_header(query_params, body_params)
        headers = {
            "Authorization": auth_header,
        }

        # Handle body parameters format
        data_payload = None
        if body_params:
            headers["Content-Type"] = "application/json"
            data_payload = json.dumps(body_params)

        # Build clean query parameters string for Bithumb URL
        url_params = None
        if query_params:
            # Query param parsing for HTTP get parameters
            query_list = []
            for k, v in query_params.items():
                if isinstance(v, list):
                    for val in v:
                        query_list.append((f"{k}[]", str(val)))
                else:
                    query_list.append((k, str(v)))
            url_params = query_list

        backoff = 0.5
        for attempt in range(retries):
            try:
                async with self.session.request(
                    method, 
                    url, 
                    params=url_params, 
                    data=data_payload, 
                    headers=headers
                ) as response:
                    
                    if response.status == 429:
                        logger.warning(f"HTTP 429 Too Many Requests. Retrying in {backoff}s...")
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                        
                    response_json = await response.json()
                    
                    if response.status not in (200, 201):
                        err_msg = response_json.get("error", {}).get("message", "Unknown error")
                        logger.error(f"API Error ({response.status}) on {path}: {err_msg}")
                        return {"status": "error", "code": response.status, "message": err_msg}
                        
                    return response_json
            except aiohttp.ClientError as ce:
                logger.error(f"Network error on attempt {attempt+1}: {ce}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(backoff)
                backoff *= 2

        return {"status": "error", "code": 429, "message": "Rate limit retries exhausted"}

    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all asset balances in Bithumb account.
        Endpoint: GET /v1/accounts
        """
        response = await self._request("GET", "/v1/accounts")
        if isinstance(response, list):
            return response
        if isinstance(response, dict) and response.get("status") == "error":
            logger.error(f"Failed to fetch accounts: {response.get('message')}")
            return []
        return []

    async def get_valid_krw_markets(self) -> set:
        """
        Fetch the set of all valid KRW-* market codes from Bithumb.
        Endpoint: GET /v1/market/all (public, no auth)
        """
        url = f"{self.base_url}/v1/market/all"
        try:
            if not self.session:
                await self.initialize()
            async with self.session.get(url) as response:
                data = await response.json()
                if isinstance(data, list):
                    return {item["market"] for item in data if item["market"].startswith("KRW-")}
        except Exception as e:
            logger.error(f"Failed to fetch valid markets: {e}")
        return set()

    async def get_candles(self, market: str, unit: int = 1, count: int = 200, to: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch minute candles from Bithumb public API.
        Endpoint: GET /v1/candles/minutes/{unit}  (no auth required)
        
        Args:
            market: Market code, e.g. 'KRW-BTC'
            unit:   Candle unit in minutes (1, 3, 5, 10, 15, 30, 60, 240)
            count:  Number of candles to fetch (max 200 per request)
            to:     KST datetime string 'yyyy-MM-dd HH:mm:ss' to fetch candles BEFORE this time.
                    If None, fetches the most recent candles.
        
        Returns:
            List of candles in ascending time order:
            [{'time': datetime, 'open': float, 'high': float, 'low': float, 'close': float, 'volume': float}, ...]
        """
        from datetime import datetime, timezone, timedelta
        
        url = f"{self.base_url}/v1/candles/minutes/{unit}"
        params = {"market": market, "count": count}
        if to:
            params["to"] = to

        try:
            if not self.session:
                await self.initialize()
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                if not isinstance(data, list):
                    logger.error(f"Unexpected candle response for {market}: {data}")
                    return []
                
                KST = timezone(timedelta(hours=9))
                candles = []
                for item in reversed(data):  # API returns newest-first; reverse to ascending
                    try:
                        kst_str = item.get("candle_date_time_kst", "")
                        if kst_str:
                            dt = datetime.fromisoformat(kst_str).replace(tzinfo=KST)
                        else:
                            dt = datetime.fromtimestamp(item["timestamp"] / 1000, tz=KST)
                        
                        candles.append({
                            "time":   dt,
                            "open":   float(item.get("opening_price", 0)),
                            "high":   float(item.get("high_price", 0)),
                            "low":    float(item.get("low_price", 0)),
                            "close":  float(item.get("trade_price", 0)),
                            "volume": float(item.get("candle_acc_trade_volume", 0)),
                        })
                    except Exception as parse_err:
                        logger.warning(f"Failed to parse candle item: {parse_err}")
                
                return candles

        except Exception as e:
            logger.error(f"Failed to fetch candles for {market}: {e}")
            return []


    async def get_tickers(self, markets: List[str]) -> Dict[str, float]:
        """
        Fetch current trade prices for a list of market codes (e.g. ['KRW-BTC', 'KRW-ETH']).
        Endpoint: GET /v1/ticker (public, no auth required)
        Returns a dict: { 'KRW-BTC': 93821000.0, ... }
        Only requests markets that are valid KRW pairs on Bithumb (filters out delisted/unlisted).
        """
        if not markets:
            return {}
        
        # Filter to only valid markets to avoid 404 from unlisted currencies
        valid_markets = await self.get_valid_krw_markets()
        valid_requested = [m for m in markets if m in valid_markets]
        
        if not valid_requested:
            return {}
        
        codes_param = ",".join(valid_requested)
        url = f"{self.base_url}/v1/ticker"
        
        result = {}
        try:
            if not self.session:
                await self.initialize()
            async with self.session.get(url, params={"markets": codes_param}) as response:
                data = await response.json()
                if isinstance(data, list):
                    result = {item["market"]: float(item.get("trade_price", 0.0)) for item in data}
                else:
                    logger.error(f"Unexpected ticker response: {data}")
        except Exception as e:
            logger.error(f"Failed to fetch tickers for {valid_requested}: {e}")
        
        return result

    async def place_order(self, market: str, side: str, order_type: str, price: Optional[float] = None, volume: Optional[float] = None, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a new order.
        Endpoint: POST /v2/orders
        side: 'bid' (buy) or 'ask' (sell)
        order_type: 'limit' (limit order), 'price' (market buy), 'market' (market sell)
        """
        body = {
            "market": market,
            "side": side,
            "order_type": order_type
        }
        if price is not None:
            body["price"] = str(price)
        if volume is not None:
            body["volume"] = str(volume)
        if client_order_id:
            body["client_order_id"] = client_order_id

        logger.info(f"Placing order: market={market}, side={side}, type={order_type}, price={price}, volume={volume}")
        return await self._request("POST", "/v2/orders", body_params=body)

    async def cancel_order(self, order_id: Optional[str] = None, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an active order.
        Endpoint: DELETE /v2/order
        One of order_id or client_order_id must be provided.
        """
        params = {}
        if order_id:
            params["order_id"] = order_id
        elif client_order_id:
            params["client_order_id"] = client_order_id
        else:
            raise ValueError("Either order_id or client_order_id must be provided to cancel order.")

        logger.info(f"Cancelling order: order_id={order_id}, client_order_id={client_order_id}")
        return await self._request("DELETE", "/v2/order", query_params=params)

    async def get_order(self, order_id: Optional[str] = None, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get details of a specific order.
        Endpoint: GET /v1/order
        """
        params = {}
        if order_id:
            params["uuid"] = order_id
        elif client_order_id:
            params["client_order_id"] = client_order_id
        else:
            raise ValueError("Either order_id (uuid) or client_order_id must be provided to fetch order details.")

        return await self._request("GET", "/v1/order", query_params=params)
