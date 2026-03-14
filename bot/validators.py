"""
Input validation for trading bot CLI parameters.
All validation raises ValueError with clear, human-readable messages.
"""

from __future__ import annotations

from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

# Binance minimum notional / qty sanity guards (soft limits for UX only)
MIN_QUANTITY = 0.001
MAX_QUANTITY = 1_000_000.0
MIN_PRICE = 0.01
MAX_PRICE = 10_000_000.0


def validate_symbol(symbol: str) -> str:
    """Normalise and validate a trading symbol (e.g. BTCUSDT)."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if not symbol.isalnum():
        raise ValueError(f"Symbol '{symbol}' contains invalid characters. Use alphanumeric only (e.g. BTCUSDT).")
    if len(symbol) < 5 or len(symbol) > 12:
        raise ValueError(f"Symbol '{symbol}' length seems wrong. Expected something like BTCUSDT.")
    return symbol


def validate_side(side: str) -> str:
    """Validate order side: BUY or SELL."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Choose from: {', '.join(sorted(VALID_SIDES))}.")
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Choose from: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: float) -> float:
    """Validate order quantity (must be a positive number)."""
    if quantity <= 0:
        raise ValueError(f"Quantity must be greater than 0. Got: {quantity}.")
    if quantity < MIN_QUANTITY:
        raise ValueError(f"Quantity {quantity} is below the minimum allowed ({MIN_QUANTITY}).")
    if quantity > MAX_QUANTITY:
        raise ValueError(f"Quantity {quantity} exceeds the maximum allowed ({MAX_QUANTITY}).")
    return quantity


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate price field.
    - Required for LIMIT and STOP_LIMIT orders.
    - Must be None / omitted for MARKET and STOP_MARKET orders.
    """
    if order_type in {"LIMIT", "STOP_LIMIT"}:
        if price is None:
            raise ValueError(f"Price is required for {order_type} orders.")
        if price <= 0:
            raise ValueError(f"Price must be greater than 0. Got: {price}.")
        if price < MIN_PRICE:
            raise ValueError(f"Price {price} is below the minimum allowed ({MIN_PRICE}).")
        if price > MAX_PRICE:
            raise ValueError(f"Price {price} exceeds the maximum allowed ({MAX_PRICE}).")
    else:
        if price is not None:
            raise ValueError(f"Price should not be provided for {order_type} orders (it is ignored).")
    return price


def validate_stop_price(stop_price: Optional[float], order_type: str) -> Optional[float]:
    """Validate stop price for STOP_MARKET and STOP_LIMIT orders."""
    if order_type in {"STOP_MARKET", "STOP_LIMIT"}:
        if stop_price is None:
            raise ValueError(f"--stop-price is required for {order_type} orders.")
        if stop_price <= 0:
            raise ValueError(f"Stop price must be greater than 0. Got: {stop_price}.")
    return stop_price


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> dict:
    """
    Run all validations and return a clean, normalised params dict.
    Raises ValueError on the first failure found.
    """
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type.upper()),
        "stop_price": validate_stop_price(stop_price, order_type.upper()),
    }
