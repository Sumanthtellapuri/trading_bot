"""
Binance Futures Testnet REST API client.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logging_config import get_logger


from dotenv import load_dotenv
load_dotenv()

logger = get_logger("client")

TESTNET_BASE_URL = "https://demo-fapi.binance.com"
DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "DELETE"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class BinanceAPIError(Exception):
    def __init__(self, code: int, message: str, http_status: int = 0):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(f"[{code}] {message} (HTTP {http_status})")


class BinanceFuturesClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: str = TESTNET_BASE_URL,
    ):
        self.api_key = api_key or os.environ.get("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("BINANCE_API_SECRET", "")
        self.base_url = base_url.rstrip("/")

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "API key and secret are required. "
                "Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables."
            )

        self._session = _build_session()
        self._session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })
        logger.info("BinanceFuturesClient initialised (base_url=%s)", self.base_url)

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: Dict[str, Any]) -> str:
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = True,
    ) -> Dict[str, Any]:
        params = params or {}

        if signed:
            params["timestamp"] = self._timestamp()
            params["recvWindow"] = 10000
            params["signature"] = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        logger.info("-> REQUEST  %s %s | params=%s", method, endpoint,
                    {k: v for k, v in params.items() if k != "signature"})

        try:
            if method == "GET":
                response = self._session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            elif method == "POST":
                response = self._session.post(url, data=params, timeout=DEFAULT_TIMEOUT)
            elif method == "DELETE":
                response = self._session.delete(url, params=params, timeout=DEFAULT_TIMEOUT)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.info("<- RESPONSE %s %s | status=%s body=%s",
                        method, endpoint, response.status_code, response.text[:500])

            data = response.json()

            if isinstance(data, dict) and data.get("code", 0) < 0:
                raise BinanceAPIError(
                    code=data["code"],
                    message=data.get("msg", "Unknown error"),
                    http_status=response.status_code,
                )

            response.raise_for_status()
            return data

        except BinanceAPIError:
            raise
        except requests.exceptions.Timeout:
            logger.error("Request timed out: %s %s", method, endpoint)
            raise
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error: %s %s | %s", method, endpoint, exc)
            raise
        except requests.exceptions.RequestException as exc:
            logger.error("Request failed: %s %s | %s", method, endpoint, exc)
            raise

    def get_server_time(self) -> Dict[str, Any]:
        return self._request("GET", "/fapi/v1/time", signed=False)

    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/exchangeInfo", params=params, signed=False)

    def get_account(self) -> Dict[str, Any]:
        return self._request("GET", "/fapi/v2/account")

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        if reduce_only:
            params["reduceOnly"] = "true"

        logger.info(
            "Placing order: symbol=%s side=%s type=%s qty=%s price=%s",
            symbol, side, order_type, quantity, price,
        )

        # Only MARKET and LIMIT are supported on demo-fapi testnet
        return self._request("POST", "/fapi/v1/order", params=params)

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("DELETE", "/fapi/v1/order", params=params)

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("GET", "/fapi/v1/order", params=params)