# NSE Analytics

A full-stack platform for real-time Nairobi Securities Exchange (NSE) stock analysis, ML-powered price forecasting, and portfolio management.

![Stack](https://img.shields.io/badge/Backend-Django-green) ![Stack](https://img.shields.io/badge/Frontend-React-blue) ![Stack](https://img.shields.io/badge/ML-scikit--learn-orange) ![Stack](https://img.shields.io/badge/Deploy-Docker-blue)

> **Disclaimer:** This project is for educational and research purposes only. Nothing in this application constitutes financial advice. Do not make investment decisions based on this tool. Past performance of any stock or model does not guarantee future results.

---

## Features

- **Real-time market data** — Live NSE stock prices via RapidAPI + custom scrapers
- **ML price forecasting** — Random Forest & Linear Regression models predicting stock movement
- **Technical analysis** — RSI, MACD, Bollinger Bands, momentum scoring
- **Portfolio management** — Track holdings, P&L, weighted average cost
- **Telegram bot** — Market alerts, portfolio updates, and predictions on demand
- **Backtesting engine** — Validate trading strategies on historical data
- **Dividend calendar** — Track dividend schedules and yield analysis
- **Dockerized** — Full 3-service setup (API + MySQL + Telegram bot)

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React Frontend │────▶│  Django REST API  │────▶│    MySQL DB      │
│  (Chart.js/Plotly│     │  (Port 8000)      │     │  (Port 3316)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
             ┌──────▼──────┐      ┌────────▼────────┐
             │  RapidAPI   │      │  Telegram Bot   │
             │  NSE Data   │      │  (Alerts/Cmds)  │
             └─────────────┘      └─────────────────┘
                    │
             ┌──────▼──────┐
             │  ML Engine  │
             │ RandomForest│
             │ LinearRegr. │
             └─────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5, Django REST Framework |
| Frontend | React 18, Chart.js, Plotly.js, React Router |
| Database | MySQL 8 (production), SQLite (development) |
| ML | scikit-learn, pandas, numpy, scipy |
| Automation | Telegram Bot API, RapidAPI |
| DevOps | Docker, docker-compose |

---

## Getting Started

### Prerequisites
- Docker & docker-compose
- Python 3.11+
- Node.js 18+

### 1. Clone the repo
```bash
git clone https://github.com/Nmwaura132/nse-analytics.git
cd nse-analytics
```

### 2. Set up environment variables
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
RAPIDAPI_KEY=your_rapidapi_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
MYSQL_ROOT_PASSWORD=your_db_password
MYSQL_DATABASE=nse_db
MYSQL_USER=nse_user
MYSQL_PASSWORD=your_password
```

### 3. Run with Docker
```bash
docker-compose up --build
```

Services start at:
- **API:** http://localhost:8000
- **Frontend:** http://localhost:5173 (dev) or served via Django in production
- **MySQL:** localhost:3316

### 4. Run without Docker (development)

**Backend:**
```bash
pip install poetry
poetry install
cd nse_backend
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## ML Models

| Model | Purpose | Algorithm |
|-------|---------|-----------|
| Price Forecaster | Predict next-day closing price | Random Forest (100 trees, OOB-validated) |
| Trend Analyser | Long-term price trend & slope | Linear Regression on ordinal dates |
| Stock Scorer | Rank stocks by momentum/value | Custom weighted scoring (RSI + MACD + BB) |
| Portfolio Optimizer | Max-Sharpe asset allocation | Markowitz MPT · Ledoit-Wolf covariance shrinkage |
| Strategy Backtester | Validate MACD/RSI strategies on history | Walk-forward equity simulation |

---

## Model Performance (Out-of-Sample)

Walk-forward expanding-window validation · 5 folds · features computed with 1-day shift to prevent look-ahead leakage.

| Metric | Random Forest | Persistence Baseline |
|--------|--------------|----------------------|
| RMSE | reported per ticker | tomorrow = today |
| MAE | reported per ticker | — |
| Directional Accuracy | reported per ticker | ~50% (random) |
| Beats Baseline | ✓ on real data | — |

Use the `/predict TICKER` Telegram command to see live per-ticker validation metrics, or call `MLPredictor().walk_forward_validate(df)` directly.

**MACD Strategy Backtest (example — SCOM)**

| Metric | Strategy | Buy & Hold |
|--------|----------|------------|
| Return | varies | varies |
| Max Drawdown | reported | reported |
| Sharpe Ratio | reported | — |
| Win Rate | reported | — |

Commission: 0.1% per trade (NSE standard). Run `Backtester().run_backtest(df, 'MACD')` for full results.

> ⚠️ For educational and research purposes only. Not financial advice.

---

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/market` | Current market summary |
| `/predict TICKER` | ML price prediction for a stock |
| `/portfolio` | Your portfolio P&L |
| `/top` | Top gainers and losers |
| `/analysis TICKER` | Full technical analysis |

---

## Project Structure

```
nse-analytics/
├── nse_backend/          # Django REST API
│   ├── api/              # Models, views, serializers
│   └── config/           # Django settings, URLs
├── frontend/             # React SPA
│   └── src/
│       ├── pages/        # Dashboard, Portfolio, DataScience
│       └── components/   # Navbar, StockModal, Charts
├── data/                 # Historical stock data (60+ stocks)
├── nse_bot.py            # Telegram bot
├── ml_predictor.py       # ML forecasting engine
├── comprehensive_analyzer.py  # Stock scoring
├── portfolio_manager.py  # Portfolio operations
├── backtester.py         # Strategy backtesting
├── docker-compose.yml
└── pyproject.toml
```

---

## Environment Variables Reference

| Variable | Description |
|----------|-------------|
| `RAPIDAPI_KEY` | RapidAPI key for NSE stock data |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `MYSQL_ROOT_PASSWORD` | MySQL root password |
| `MYSQL_DATABASE` | Database name |
| `MYSQL_USER` | Database user |
| `MYSQL_PASSWORD` | Database password |

---

## Author

**Nelson Mwaura** — [linkedin.com/in/nelson-peter](https://www.linkedin.com/in/nelson-peter) · [portfolio-e16.pages.dev](https://portfolio-e16.pages.dev)
