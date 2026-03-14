# 🤖 Binance Futures Testnet Trading Bot

A production-grade Python CLI application for placing orders on **Binance USDT-M Futures Testnet**.  
Built with clean separation of concerns, structured logging, and comprehensive input validation.

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API client (signing, retries, error handling)
│   ├── orders.py          # Order placement logic + response formatting
│   ├── validators.py      # Input validation — raises clear errors
│   └── logging_config.py  # Rotating file + console log handlers
├── cli.py                 # CLI entry point (argparse sub-commands)
├── logs/
│   └── trading_bot.log    # Auto-created on first run
├── README.md
└── requirements.txt
```

---

## ⚙️ Setup Steps

### 1. Prerequisites

- Python **3.8+** installed
- VS Code (recommended) with the Python extension

### 2. Get Binance Futures Testnet API Keys

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in (GitHub account works)
3. Click your avatar → **API Key** → **Generate Key**
4. Copy and save your **API Key** and **Secret Key**

### 3. Clone / Download the Project

```bash
# If using git
git clone https://github.com/<your-username>/trading-bot.git
cd trading_bot

# Or just unzip and cd into the folder
```

### 4. Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Set API Credentials

**Option A — Environment variables (recommended):**

```bash
# Windows (Command Prompt)
set BINANCE_API_KEY=your_api_key_here
set BINANCE_API_SECRET=your_api_secret_here

# Windows (PowerShell)
$env:BINANCE_API_KEY="your_api_key_here"
$env:BINANCE_API_SECRET="your_api_secret_here"

# macOS / Linux
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

**Option B — CLI flags (useful for quick testing):**

```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET place --symbol BTCUSDT ...
```

---

## 🚀 How to Run

### Check Connectivity

```bash
python cli.py ping
```

```
🔌  Pinging Binance Futures Testnet …
✅  Connected!  Server time: 1741942860123 ms
```

---

### View Account Balances

```bash
python cli.py account
```

---

### Place a MARKET Order

```bash
# BUY 0.01 BTC at market price
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# SELL 0.01 BTC at market price
python cli.py place --symbol BTCUSDT --side SELL --type MARKET --quantity 0.01
```

**Sample output:**
```
┌──────────────────────────────────────────────────────┐
│              ORDER REQUEST SUMMARY                   │
└──────────────────────────────────────────────────────┘
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Quantity      : 0.01
────────────────────────────────────────────────────────

⏳  Sending order to Binance Futures Testnet …

╔══════════════════════════════════════════════════════╗
║              ORDER RESPONSE SUMMARY                 ║
╚══════════════════════════════════════════════════════╝
  Order ID      : 4165496830
  Status        : FILLED
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Orig Qty      : 0.01
  Executed Qty  : 0.01
  Avg Price      : 83425.60
  Time-in-Force  : GTC
  Update Time    : 1741942861000
════════════════════════════════════════════════════════

✅  Order placed successfully! orderId=4165496830  status=FILLED
```

---

### Place a LIMIT Order

```bash
# Limit SELL at $95,000
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 95000

# Limit BUY at $70,000 (resting order below market)
python cli.py place --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 70000
```

---

### Place a STOP_MARKET Order *(Bonus)*

```bash
# Stop BUY triggered when price hits $80,000
python cli.py place --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.01 --stop-price 80000
```

---

### Place a STOP_LIMIT Order *(Bonus)*

```bash
# Stop-Limit SELL: trigger at $79,000, limit at $78,500
python cli.py place --symbol BTCUSDT --side SELL --type STOP_LIMIT \
  --quantity 0.01 --stop-price 79000 --price 78500
```

---

### Print Raw JSON Response

Add `--json` to any `place` command:

```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --json
```

---

### Change Log Level

```bash
python cli.py --log-level DEBUG place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

---

## 📋 Full CLI Reference

```
usage: trading_bot [-h] [--log-level {DEBUG,INFO,WARNING,ERROR}]
                   [--api-key API_KEY] [--api-secret API_SECRET]
                   {ping,account,place} ...

Subcommands:
  ping      Check connectivity to the testnet
  account   Show account balances
  place     Place a futures order
    --symbol     SYMBOL         Trading pair (e.g. BTCUSDT)        [required]
    --side       {BUY,SELL}     Order side                         [required]
    --type       {MARKET,LIMIT,STOP_MARKET,STOP_LIMIT}             [required]
    --quantity   FLOAT          Amount in base asset               [required]
    --price      FLOAT          Limit price (LIMIT / STOP_LIMIT)   [optional]
    --stop-price FLOAT          Trigger price (STOP_*)             [optional]
    --json                      Also print raw JSON response       [flag]
```

---

## 📊 Logging

All sessions are logged to `logs/trading_bot.log` automatically.

- **File handler**: `INFO` level and above, rotates at 5 MB (keeps 5 backups)
- **Console handler**: `WARNING` and above only (keeps CLI output clean)
- Each log line: `timestamp | level | module | message`

Log file captures:
- Every API request (method, endpoint, params — signature redacted)
- Every API response (status code, body snippet)
- Validation errors
- Network failures and Binance API errors
- Session start / end with exit code

---

## 🏗️ Architecture

| Layer | File | Responsibility |
|-------|------|----------------|
| **CLI** | `cli.py` | Argument parsing, user output, exit codes |
| **Validation** | `bot/validators.py` | Input validation, normalisation |
| **Business Logic** | `bot/orders.py` | Order placement, response formatting |
| **API Client** | `bot/client.py` | HTTP, signing, retries, error mapping |
| **Logging** | `bot/logging_config.py` | Handlers, formatters, rotation |

The layers are strictly one-directional: CLI → Orders → Client.  
Nothing in `client.py` knows about the CLI; nothing in `orders.py` knows about argparse.

---

## 🐛 Error Handling

| Error Type | Behaviour |
|------------|-----------|
| Invalid input (wrong type, missing price) | Validation error before any API call |
| Binance API error (e.g. -1111 precision) | Printed with code + message; logged |
| Network timeout | Retried up to 3× with backoff; then error |
| Missing API keys | Clear startup error, no crash |

---

## 📌 Assumptions

1. **Testnet only** — base URL is hardcoded to `https://testnet.binancefuture.com`. Change `TESTNET_BASE_URL` in `client.py` for mainnet (use at your own risk).
2. **USDT-M Futures only** — spot and COIN-M endpoints are not covered.
3. **Hedge mode not assumed** — `positionSide` defaults to `BOTH` (one-way mode).
4. **Quantity precision** — Binance enforces per-symbol precision rules. If you get `-1111`, reduce decimal places on your quantity.
5. **No `python-binance` dependency** — all requests are made via raw `requests` calls for transparency and control.

---

## 🧪 Running Tests (Optional)

```bash
pip install pytest
pytest tests/ -v
```

*(Test stubs are provided in `tests/` — add mocks for full offline testing.)*

---

## 📦 Dependencies

```
requests>=2.31.0   # HTTP client with connection pooling
urllib3>=2.0.0     # Retry logic
```

No heavyweight frameworks. No `python-binance` required.

---

## 📬 Submission Notes

- Log files from a MARKET order and a LIMIT order are included in `logs/trading_bot.log`
- Bonus: STOP_MARKET and STOP_LIMIT order types are fully supported
- All code is linted to PEP 8 and uses type hints throughout
