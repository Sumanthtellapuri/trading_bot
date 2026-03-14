"""
Order placement and result formatting logic.

Separates business logic from both the HTTP client and the CLI layer.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .client import BinanceFuturesClient, BinanceAPIError
from .logging_config import get_logger

logger = get_logger("orders")


# ---------------------------------------------------------------------------
# Result formatting
# ---------------------------------------------------------------------------

def format_order_response(response: Dict[str, Any]) -> str:
    """
    Produce a human-readable summary of a Binance order response.

    Handles both filled (MARKET) and resting (LIMIT) orders gracefully.
    """
    order_id = response.get("orderId", "N/A")
    status = response.get("status", "N/A")
    symbol = response.get("symbol", "N/A")
    side = response.get("side", "N/A")
    order_type = response.get("type", "N/A")
    orig_qty = response.get("origQty", "N/A")
    executed_qty = response.get("executedQty", "0")
    avg_price = response.get("avgPrice", None)
    price = response.get("price", "N/A")
    stop_price = response.get("stopPrice", None)
    time_in_force = response.get("timeInForce", "N/A")
    update_time = response.get("updateTime", "N/A")

    lines = [
        "",
        "╔══════════════════════════════════════════════════════╗",
        "║              ORDER RESPONSE SUMMARY                 ║",
        "╚══════════════════════════════════════════════════════╝",
        f"  Order ID      : {order_id}",
        f"  Status        : {status}",
        f"  Symbol        : {symbol}",
        f"  Side          : {side}",
        f"  Type          : {order_type}",
        f"  Orig Qty      : {orig_qty}",
        f"  Executed Qty  : {executed_qty}",
    ]

    if avg_price is not None and float(avg_price) > 0:
        lines.append(f"  Avg Price      : {avg_price}")
    elif order_type == "LIMIT":
        lines.append(f"  Limit Price    : {price}")

    if stop_price:
        lines.append(f"  Stop Price     : {stop_price}")

    lines.append(f"  Time-in-Force  : {time_in_force}")
    lines.append(f"  Update Time    : {update_time}")
    lines.append("═" * 56)

    return "\n".join(lines)


def format_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
    stop_price: Optional[float],
) -> str:
    """Print what we're about to send before hitting the API."""
    lines = [
        "",
        "┌──────────────────────────────────────────────────────┐",
        "│              ORDER REQUEST SUMMARY                   │",
        "└──────────────────────────────────────────────────────┘",
        f"  Symbol        : {symbol}",
        f"  Side          : {side}",
        f"  Type          : {order_type}",
        f"  Quantity      : {quantity}",
    ]
    if price is not None:
        lines.append(f"  Price         : {price}")
    if stop_price is not None:
        lines.append(f"  Stop Price    : {stop_price}")
    lines.append("─" * 56)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Order placement helpers
# ---------------------------------------------------------------------------

class OrderManager:
    """
    High-level order operations built on top of BinanceFuturesClient.

    This is the layer that CLI commands should call — never the client directly.
    """

    def __init__(self, client: BinanceFuturesClient):
        self.client = client

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Place an order and return the raw Binance response.

        Logs a structured audit trail of the full request/response cycle.

        Raises:
            BinanceAPIError: Propagated from the client layer.
            requests.RequestException: On network failures.
        """
        logger.info(
            "OrderManager.place_order called | symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
            symbol, side, order_type, quantity, price, stop_price,
        )

        response = self.client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            reduce_only=reduce_only,
        )

        logger.info(
            "Order placed successfully | orderId=%s status=%s executedQty=%s avgPrice=%s",
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
            response.get("avgPrice"),
        )

        return response

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ) -> Dict[str, Any]:
        """Convenience method: place a MARKET order."""
        return self.place_order(symbol=symbol, side=side, order_type="MARKET", quantity=quantity)

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> Dict[str, Any]:
        """Convenience method: place a LIMIT order."""
        return self.place_order(symbol=symbol, side=side, order_type="LIMIT", quantity=quantity, price=price)

    def place_stop_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
    ) -> Dict[str, Any]:
        """Convenience method: place a STOP_MARKET order (bonus)."""
        return self.place_order(
            symbol=symbol, side=side, order_type="STOP_MARKET", quantity=quantity, stop_price=stop_price
        )

    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
    ) -> Dict[str, Any]:
        """Convenience method: place a STOP_LIMIT order (bonus)."""
        return self.place_order(
            symbol=symbol, side=side, order_type="STOP_LIMIT",
            quantity=quantity, price=price, stop_price=stop_price,
        )
