# CognitoTrader: An AI-Hybrid Algorithmic Trading Platform

CognitoTrader is a sophisticated, multi-agent algorithmic trading platform built from the ground up in Python. It is designed to analyze the Indian stock market, generate high-probability trading signals using a hybrid of quantitative, AI-driven, and machine learning techniques, and execute trades in a simulated environment. The platform features a modular architecture that supports multiple, distinct trading agents, each with its own unique strategy.

---

## Core Features

* **Multi-Agent Architecture:** The platform is designed to run multiple, independent trading agents simultaneously, each targeting a different market or strategy.
* **Hybrid Intelligence:** Fuses traditional quantitative signals (technical indicators) with qualitative analysis from a Large Language Model (Google Gemini) and predictive insights from a custom-trained Machine Learning model.
* **Live Data Integration:** Connects to live market data feeds via the Fyers API for real-time analysis and trade simulation.
* **Robust Engineering:** Features a structured logging system for performance auditing, automated data pipeline sanitization, and a resilient main loop with error handling.
* **Data-Driven Strategy Development:** Includes a full suite of tools for backtesting, data harvesting, feature engineering, and ML model optimization to allow for rigorous, data-driven strategy refinement.

---

## The Agents

The platform currently supports three distinct, fully developed trading agents.

### 1. The Options Agent (Protocol: "Weighted Confluence Breakout")

This is a highly selective, low-frequency agent designed to trade NIFTY 50 index options. Its core principle is **confluence**, requiring multiple, independent signals to align before authorizing a trade.

* **Strategy:** A trade is only executed if the following conditions are met:
    1.  **NIFTY Regime:** The 45-minute trend of the NIFTY 50 index is aligned.
    2.  **Sector Regime:** The 45-minute trend of the NIFTY BANK index (the most heavily weighted sector) is also aligned.
    3.  **Breakout Trigger:** A 5-minute price breakout in the direction of the trend occurs.
    4.  **Weighted Sentiment:** A custom-built sentiment engine, which analyzes news for the top 10 NIFTY 50 constituents and weights their sentiment scores by their index weightage, provides a confirming signal.
    5.  **ML Prediction:** A custom-trained machine learning model predicts a favorable outcome over the next 30 minutes.
* **Data Sources:** Fyers API (market data), YFinance (company-specific news), Google Gemini (sentiment analysis).

### 2. The Equity Agent (Protocol: "Equity Surge")

This is a medium-frequency, intraday momentum agent that scans the NIFTY 200 universe to find stocks experiencing a price and volume surge.

* **Strategy:**
    1.  **Quantitative Scan:** Every 15 minutes, the agent scans all 200 stocks for those with price change > 1.5% and volume > 500,000.
    2.  **Sector Filter:** It then confirms that the parent sector of each surging stock is also in a confirmed uptrend.
    3.  **Sentiment Filter:** Finally, it uses the LLM to analyze news sentiment for the specific stocks that passed both previous filters before executing a trade.
* **Data Sources:** Fyers API (market data), YFinance (company-specific news), Google Gemini (sentiment analysis).

### 3. The HFT Agent (Protocol: "Order Flow Imbalance")

This is a high-frequency scalping agent designed to trade a single, highly liquid stock by analyzing its real-time order book.

* **Strategy:** The agent connects to a tick-by-tick Level 2 data feed and continuously calculates the imbalance between buy and sell orders in the top 10 levels of the order book. It enters a trade when the imbalance ratio exceeds a predefined threshold (e.g., 30%) and exits when the imbalance neutralizes.
* **Data Sources:** Fyers API (Level 2 Tick-by-Tick WebSocket).

---

## Machine Learning Pipeline

The platform includes a complete end-to-end pipeline for developing and deploying the predictive ML model used by the options agent.

1.  **Data Harvesting:** A chunked downloader script fetches **5 years** of 5-minute NIFTY 50 candle data (>96,000 data points) from the Fyers API.
2.  **Feature Engineering:** A dedicated script processes the raw data, calculating **21 distinct features** (RSI, MACD, multiple EMAs, Bollinger Bands, ATR, etc.) and creating a target label to predict the price direction 30 minutes into the future.
3.  **Model Training & Optimization:** The system uses a GPU-accelerated **LightGBM Classifier**. An optimization script (`model_optimizer.py`) uses `RandomizedSearchCV` to test dozens of hyperparameter combinations to find the optimal model configuration. The baseline model achieved a **51% accuracy** on over 19,000 unseen test samples.

---

## Tech Stack

* **Core Language:** Python
* **Data Manipulation:** Pandas, NumPy
* **Machine Learning:** Scikit-learn, LightGBM, Joblib
* **Technical Analysis:** Pandas-TA
* **APIs & Data Sources:** Fyers API, Google Gemini API, YFinance, Requests
* **Web Scraping:** BeautifulSoup4
* **Version Control:** Git

---

## Setup & Usage

1.  **Clone the repository:**
    ```bash
    git clone [your-repo-url]
    cd ProjectCognito
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    python -m pip install -r requirements.txt
    ```
4.  **Configure API Keys:**
    * Create a `.env` file in the root directory.
    * Add your API keys: `FYERS_APP_ID`, `FYERS_SECRET_KEY`, `GOOGLE_API_KEY`, `NEWS_API_KEY`.
5.  **Run an Agent:**
    * To run the options agent: `python main.py`
    * To run the equity agent: `python equity_main.py`

---

## Disclaimer

This project is for educational and research purposes only. The strategies and agents are not guaranteed to be profitable and are run in a simulated paper trading environment. Trading financial markets involves significant risk. Do not use this code for live trading without a thorough understanding of the risks involved.
