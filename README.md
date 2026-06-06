# Quantitative Portfolio Optimization, Fundamental Analysis & Monte Carlo Forecasting

## 📌 Project Overview
This repository contains a comprehensive, Python-driven financial engineering project designed to automate fundamental stock analysis, optimize investment portfolios using advanced risk-adjusted metrics, and forecast future portfolio performance. Utilizing empirical market data (2024 base year vs. 2025 test year), the project integrates quantitative methods, mathematical optimization, and stochastic modeling to build and evaluate robust investment strategies.

## ⚙️ Core Architecture & Scripts

The project is divided into three primary modules:

### 1. Automated Fundamental & Valuation Analysis (`collect info.py`)
A robust data pipeline that fetches historical market data, income statements, balance sheets, and cash flow statements via `yfinance`. 
* **Financial Modeling:** Automatically calculates NOPAT, Free Cash Flow (FCF), and Invested Capital.
* **Profitability & Liquidity:** Computes ROE, ROA, ROIC, Gross/Operating/Net Margins, Current/Quick/Cash Ratios.
* **Debt & Valuation Multiples:** Calculates D/E, Interest Coverage, Net Debt / EBITDA, P/E, P/S, P/FCF, EV/EBITDA, P/B, and PEG ratios.
* **Output:** Generates a comprehensive Excel workbook consolidating raw data, multi-year CAGRs, and comparative valuation metrics.

### 2. Advanced Portfolio Optimization (`start portfolio.py`)
Utilizes `scipy.optimize` (SLSQP method) to determine optimal asset allocation boundaries for a selected universe of equities and benchmark ETFs (e.g., NASDAQ, VOO, IAU).
* **Risk-Adjusted Performance:** Calculates standard and advanced metrics including Sharpe Ratio, Treynor Measure, Jensen's Alpha, and the M² Coefficient.
* **Tail Risk Assessment:** Computes Skewness, Kurtosis, Value at Risk (VaR), Conditional VaR (CVaR), and Modified VaR (MVAR/Z-MVAR).
* **Optimization Strategies:** Solves for 5 distinct portfolio structures under strict weight constraints:
  1. Maximum Annual Return
  2. Minimum Daily Standard Deviation
  3. Maximum Sharpe Ratio
  4. Maximum Conditional Sharpe Ratio (ConSR)
  5. Maximum Modified Sharpe Ratio (ModSR)

### 3. Stochastic Forecasting (`monte carlo.py`)
Predicts future portfolio behavior based on historical volatility and inter-asset correlations.
* **Correlated Random Walks:** Uses Cholesky decomposition of the covariance matrix to simulate correlated asset returns, avoiding naive independent asset assumptions.
* **High-Volume Simulation:** Executes 100,000 Monte Carlo simulations over a 365-day trading horizon.
* **Backtesting & Visualization:** Plots the 10th (Pessimistic), 50th (Median), and 90th (Optimistic) percentiles of the simulated portfolio paths against the **actual** historical performance of the portfolio in the test year.

## 🛠️ Tech Stack & Libraries

* **Language:** Python
* **Data Manipulation & Analysis:** `pandas`, `numpy`
* **Mathematical Optimization & Statistics:** `scipy` (`scipy.optimize`, `scipy.stats`)
* **Financial Data Parsing:** `yfinance`
* **Visualization:** `matplotlib`
* **Reporting:** MS Excel (`openpyxl`, `xlsxwriter` via pandas)

## 📊 Results & Output
* **Optimized Allocations:** Successfully bounded asset weights to maximize specific risk-adjusted returns (e.g., punishing downside tail risk via CVaR optimization).
* **Predictive Accuracy:** The Monte Carlo simulations provided a statistically sound confidence interval, verified against actual out-of-sample data from the following fiscal year.
* **Automated Reporting:** Outputs deeply structured `.xlsx` files containing covariance matrices, daily/annual returns, fundamental breakdowns, and optimization test results for easy sharing and presentation.
