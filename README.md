# 📈 Formation, Optimization, and Stress-Testing of an Investment Portfolio (NASDAQ)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-%230C55A5.svg?style=for-the-badge&logo=scipy&logoColor=white)

An academic project completed as part of the "Financial Management" course at HSE University (Graduate School of Business).

This project focuses on the quantitative analysis of the stock market: from the fundamental screening of US tech sector stocks (NASDAQ) to constructing the Markowitz efficient frontier and performing advanced stress-testing of tail risks using Monte Carlo simulations (Jump-Diffusion model).

## 🎯 Goals and Objectives

The main goal is to algorithmically construct an investment portfolio, optimize its structure, and stress-test its resilience ("to the breaking point") under macroeconomic shocks and market uncertainty.

**Key stages:**

1. **Fundamental Screening:** Selecting the 10 most fundamentally sound and efficient companies out of 22 candidates based on valuation multiples (P/E, EV/EBITDA, P/S) and profitability metrics (ROE, ROIC, Net Margin) across 5 sectors.
2. **Algorithmic Optimization:** Calculating covariance matrices and finding optimal weights (Max Sharpe, Min Volatility) using 2024 data.
3. **Forward Testing (Out-of-sample):** Testing the "trained" weights on the turbulent data of 2025 and comparing them with a naive equal-weight strategy (1/N).
4. **Stress-Testing (Monte Carlo):** Simulating 10,000 scenarios 5 years forward using Merton's Jump-Diffusion model to estimate risk (CVaR) during market crashes up to -15%.

## 🛠️ Tech Stack

* **Language:** `Python 3`
* **Data Collection:** `yfinance`
* **Math & Optimization:** `numpy`, `pandas`, `scipy.optimize`
* **Visualization:** `matplotlib`, `seaborn`

## 🧠 Key Findings (Insights)

During the research, a portfolio optimization paradox was discovered and mathematically proven:

* In the conditions of the "noisy" but growing market of 2025, the optimized portfolio (Max SR) underperformed the naive 1/N allocation in terms of returns. The optimization appeared to be "overfitted."
* However, **the Monte Carlo simulation of tail risks proved the exact opposite**: Markowitz's algorithm built an ultra-protective "armor." When severe crises and market crashes (drops from -5% to -15%) occurred, the optimized portfolio demonstrated unmatched resilience, outperforming the equally weighted strategy in absolutely all 25 crisis scenarios.

## 📂 Project Structure

* `код/collect info.py` — script for automated historical quotes collection via the Yahoo Finance API and initial data cleaning.
* `код/portfolio_analize.py` — the core of the project: calculating returns, covariances, plotting the Markowitz efficient frontier, calculating the Sharpe ratio, and other key metrics.
* `код/monte сarlo.py` — implementation of Merton's model (Jump-Diffusion). Generating random noise matrices and Poisson "jumps", plotting the probability cone, and calculating the CVaR (Conditional Value-at-Risk) metric.
* `фин мен.md` — full text of the research report with conclusions and economic rationale.

*(Note: File paths are kept as in the original repository)*

## 👥 Project Team (HSE University)

* V. V. Andreev
* A. A. Butenko
* M. G. Valieva
* D. N. Grigoryan
* Dao Phi Hung (responsible for codebase and conducting additional analysis)

*(Students of the "Marketing and Market Analytics" educational program) 2026*
