#!/usr/bin/env python3
"""
Binance Futures Testnet Trading Bot — CLI Entry Point

Usage examples:
  # Market BUY
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

  # Limit SELL
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 95000

  # Stop-Market BUY (bonus)
  python cli.py place --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.01 --stop-price 80000

  # Stop-Limit SELL (bonus)
  python cli.py place --symbol ETHUSDT --side SELL --type STOP_LIMIT --quantity 0.1 --price 3000 --stop-price 3100

  # Account info
  python cli.py account

  # Check connectivity
  python cli.py ping
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from bot.client import BinanceFuturesClient, BinanceAPIError
from bot.logging_config import setup_logging, get_logger
from bot.orders import OrderManager, format_order_request, format_order_response
from bot.validators import validate_all


# ── helpers ────────────────────────────────────────────────────────────────

def _print_success(message: str) -> None:
    print(f"\n✅  {message}")

def _print_error(message: str) -> None:
    print(f"\n❌  {message}", file=sys.stderr)

def _print_section(title: str, content: str) -> None:
    print(content)


# ── sub-command handlers ────────────────────────────────────────────────────

def cmd_ping(client: BinanceFuturesClient, _args: argparse.Namespace) -> int:
    """Check connectivity to the Binance Futures Testnet."""
    print("\n🔌  Pinging Binance Futures Testnet …")
    try:
        result = client.get_server_time()
        print(f"✅  Connected!  Server time: {result.get('serverTime')} ms")
        return 0
    except Exception as exc:
        _print_error(f"Ping failed: {exc}")
        return 1


def cmd_account(client: BinanceFuturesClient, _args: argparse.Namespace) -> int:
    """Display account balance information."""
    print("\n📊  Fetching account information …\n")
    logger = get_logger("cli")
    try:
        account = client.get_account()
        assets = [a for a in account.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
        if not assets:
            print("  No assets with non-zero balance found.")
        else:
            print(f"  {'Asset':<10} {'Wallet Balance':>18} {'Available Margin':>18}")
            print("  " + "─" * 50)
            for asset in assets:
                print(
                    f"  {asset['asset']:<10} "
                    f"{float(asset['walletBalance']):>18.4f} "
                    f"{float(asset.get('availableBalance', 0)):>18.4f}"
                )
        logger.info("Account info fetched successfully. Assets: %s", [a["asset"] for a in assets])
        return 0
    except BinanceAPIError as exc:
        _print_error(f"Binance API error: {exc}")
        logger.error("Account fetch failed: %s", exc)
        return 1
    except Exception as exc:
        _print_error(f"Unexpected error: {exc}")
        logger.exception("Account fetch unexpected error")
        return 1


def cmd_place(client: BinanceFuturesClient, args: argparse.Namespace) -> int:
    """Validate inputs, place an order, and display the result."""
    logger = get_logger("cli")

    # ── 1. Validate all user inputs ────────────────────────────────────────
    try:
        params = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValueError as exc:
        _print_error(f"Validation error: {exc}")
        logger.error("Input validation failed: %s", exc)
        return 1

    # ── 2. Print request summary ────────────────────────────────────────────
    print(
        format_order_request(
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
            stop_price=params["stop_price"],
        )
    )

    print("\n⏳  Sending order to Binance Futures Testnet …")

    # ── 3. Place order ──────────────────────────────────────────────────────
    manager = OrderManager(client)
    try:
        response = manager.place_order(
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
            stop_price=params["stop_price"],
        )
    except BinanceAPIError as exc:
        _print_error(f"Binance API error {exc.code}: {exc.message}")
        logger.error("Order failed — BinanceAPIError: %s", exc)
        return 1
    except Exception as exc:
        _print_error(f"Unexpected error while placing order: {exc}")
        logger.exception("Order placement unexpected error")
        return 1

    # ── 4. Print response summary ───────────────────────────────────────────
    print(format_order_response(response))
    _print_success(
        f"Order placed successfully! "
        f"orderId={response.get('orderId')}  status={response.get('status')}"
    )

    if args.json:
        print("\n── Raw JSON Response ──")
        print(json.dumps(response, indent=2))

    return 0


# ── argument parser ─────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level for the file handler (default: INFO).",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Binance API key (overrides BINANCE_API_KEY env var).",
    )
    parser.add_argument(
        "--api-secret",
        default=None,
        help="Binance API secret (overrides BINANCE_API_SECRET env var).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── ping ──────────────────────────────────────────────────────────────
    subparsers.add_parser("ping", help="Check connectivity to the testnet.")

    # ── account ───────────────────────────────────────────────────────────
    subparsers.add_parser("account", help="Show account balances.")

    # ── place ─────────────────────────────────────────────────────────────
    place_parser = subparsers.add_parser("place", help="Place a futures order.")
    place_parser.add_argument("--symbol",     required=True, help="Trading pair, e.g. BTCUSDT.")
    place_parser.add_argument("--side",       required=True, choices=["BUY", "SELL"],
                              help="Order side.")
    place_parser.add_argument("--type",       required=True,
                              choices=["MARKET", "LIMIT", "STOP_MARKET", "STOP_LIMIT"],
                              help="Order type.")
    place_parser.add_argument("--quantity",   required=True, type=float,
                              help="Quantity in base asset (e.g. 0.01 BTC).")
    place_parser.add_argument("--price",      type=float, default=None,
                              help="Limit price — required for LIMIT / STOP_LIMIT.")
    place_parser.add_argument("--stop-price", type=float, default=None,
                              dest="stop_price",
                              help="Stop/trigger price — required for STOP_MARKET / STOP_LIMIT.")
    place_parser.add_argument("--json",       action="store_true",
                              help="Also print the raw JSON response.")

    return parser


# ── main ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Set up logging before anything else
    setup_logging(log_level=args.log_level)
    logger = get_logger("cli")
    logger.info("=== Trading Bot Session Started === command=%s", args.command)

    # Build client (raises ValueError if keys are missing)
    try:
        client = BinanceFuturesClient(
            api_key=args.api_key,
            api_secret=args.api_secret,
        )
    except ValueError as exc:
        _print_error(str(exc))
        logger.error("Client initialisation failed: %s", exc)
        return 1

    # Dispatch to sub-command
    dispatch = {
        "ping":    cmd_ping,
        "account": cmd_account,
        "place":   cmd_place,
    }
    exit_code = dispatch[args.command](client, args)
    logger.info("=== Session Ended === exit_code=%s", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
