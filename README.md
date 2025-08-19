AI-Hybrid Quantitative Trading Platform 
Tech Stack: Python | Scikit-learn | Pandas | NumPy | Google Gemini API | Fyers API | YFinance | Git

Developed a comprehensive, autonomous trading and analysis platform from the ground up, featuring two distinct agents for trading NIFTY 50 options and a universe of 200 Indian equities. The system leverages a hybrid approach, combining quantitative analysis, machine learning predictions, and real-time AI-driven sentiment analysis to identify and execute high-probability intraday trades in a simulated environment.

Engineered a complete Machine Learning pipeline, processing 5 years of 5-minute historical data (>96,000 data points) to train a Gradient Boosting model that achieved a 51% predictive accuracy on over 19,000 unseen test samples.

Developed and backtested multiple quantitative strategies in TradingView; the optimized "Confluence Breakout" protocol achieved a 1.25 Profit Factor and a 37.5% win rate across nearly 1,000 simulated trades.

Integrated the Google Gemini Large Language Model (LLM) to perform real-time sentiment analysis on high-impact financial news, serving as a qualitative filter to confirm or veto quantitative trading signals.

Architected two distinct, fully autonomous trading agents (Options & Equity) with complete trade lifecycle management, including dynamic instrument selection, risk calculation (1% rule), and automated End-of-Day (EOD) exits.

Built a robust, multi-module software suite featuring automated data harvesting from 3 external APIs (Fyers, YFinance, Google AI), dependency management, and a structured logging system for performance auditing and debugging.
