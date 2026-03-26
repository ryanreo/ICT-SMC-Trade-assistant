# ICT-SMC Trade Assistant 🏦

An institutional-grade autonomous trading bot built on **Inner Circle Trader (ICT)** and **Smart Money Concepts (SMC)** methodology. The bot programmatically maps market structure, liquidity pools, and fair value gaps across multiple timeframes, then leverages **Google Gemini AI** as a final confirmation arbiter before executing trades on **MetaTrader 5**.

## Architecture

```
┌─────────────────────────────────────────────┐
│               Main Trading Loop             │
│  (Multi-Timeframe: Daily Bias → M15 Entry)  │
├──────────┬──────────┬───────────────────────┤
│  Core    │    AI    │     Execution         │
│ Engine   │  Layer   │     Layer             │
├──────────┼──────────┼───────────────────────┤
│ Swing    │ Gemini   │ Kill Zone Filter      │
│ Points   │ LLM      │ Risk Manager          │
│ Market   │ Arbiter  │ Order Router (MT5)    │
│ Structure│          │ Discord Notifier      │
│ FVGs     │          │                       │
│ Liquidity│          │                       │
│ Order    │          │                       │
│ Blocks   │          │                       │
└──────────┴──────────┴───────────────────────┘
```

## Features

- **Multi-Timeframe Analysis**: Daily (D1) bias drives macro direction; M15 provides precision entries.
- **ICT/SMC Core Engine**: Programmatic detection of swing points, market structure shifts (BOS/CHoCH), fair value gaps, liquidity pools, and premium/discount zones.
- **AI Confirmation**: Google Gemini evaluates every setup for confluence before execution, including explicit reasoning for rejections.
- **Autonomous Execution**: Trades are routed directly through MetaTrader 5 with ATR-padded stop losses and calculated position sizing.
- **Real-Time Discord Alerts**: Every AI evaluation (approval or rejection with full rationale) is pushed to Discord in real-time.
- **Kill Zone Awareness**: Session-based timing aligned to London, New York, and Asian kill zones.

## Project Structure

```
ICT-SMC-Trade-assistant/
├── main.py                  # Main bot entry point & trading loop
├── ai/
│   ├── llm_client.py        # Gemini AI integration
│   └── prompts.py           # AI system persona & context prompts
├── core/
│   ├── data/
│   │   └── data_ingestion.py  # MT5 data fetcher
│   ├── structure/
│   │   ├── swing_points.py    # Swing high/low detection
│   │   └── market_structure.py # BOS/CHoCH identification
│   └── patterns/
│       ├── fvg.py             # Fair Value Gap detection
│       ├── liquidity.py       # Liquidity pool mapping
│       └── order_blocks.py    # Premium/Discount zones
├── execution/
│   ├── killzones.py           # Session timing filter
│   ├── risk_manager.py        # Position sizing & SL padding
│   ├── router.py              # MT5 order execution
│   └── notifier.py            # Discord webhook notifications
├── backtesting/
│   └── vbt_engine.py          # Vectorbt backtesting engine
├── requirements.txt
└── .env.example
```

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/ryanreo/ICT-SMC-Trade-assistant.git
   cd ICT-SMC-Trade-assistant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys, MT5 credentials, and Discord webhook URL
   ```

5. **Run the bot**
   ```bash
   python main.py
   ```

## Configuration

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key for AI confirmation |
| `MT5_LOGIN` | MetaTrader 5 account number |
| `MT5_PASSWORD` | MetaTrader 5 password |
| `MT5_SERVER` | MetaTrader 5 broker server |
| `DISCORD_WEBHOOK_URL` | Discord channel webhook for live alerts |
| `RISK_PER_TRADE_PERCENT` | Risk per trade as % of account balance |
| `CONFIDENCE_THRESHOLD` | Minimum AI confidence score to execute |

## Disclaimer

This software is for **educational purposes only**. Trading financial instruments carries significant risk. Use at your own discretion.
