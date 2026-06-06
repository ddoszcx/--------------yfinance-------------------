# Investment Portfolio Optimization and Financial Analysis

## 📌 Project Overview
[cite_start]This repository contains a comprehensive investment portfolio optimization and financial analysis project completed as part of the "Financial Management" curriculum[cite: 1]. [cite_start]The primary objective of the project is to develop, optimize, and evaluate an investment portfolio using empirical historical data from the 2024 and 2025 fiscal years[cite: 1]. [cite_start]The project demonstrates a rigorous approach to asset selection, fundamental analysis, risk management, and quantitative portfolio optimization techniques[cite: 1].

## ⚙️ Key Features & Methodology

* [cite_start]**Market Selection & Asset Screening:** Evaluation and selection of a global stock exchange (e.g., NYSE, NASDAQ, LSE, MOEX)[cite: 1]. [cite_start]An initial universe of 15–25 companies across 4–5 sectors was screened down to a final optimized selection consisting of at least 8 stocks and 2 stabilizing assets[cite: 1].
* [cite_start]**Fundamental Analysis:** In-depth evaluation of corporate financial health over a two-year period (2024–2025) using key financial ratios and valuation multiples[cite: 1]:
  * [cite_start]**Profitability Metrics:** Return on Equity (ROE), Return on Invested Capital (ROIC), and Profit Margin[cite: 1].
  * [cite_start]**Valuation Multiples:** P/E, P/B, PEG, and P/S ratios[cite: 1].
  * [cite_start]**Leverage & Earnings:** EV/EBITDA and Net Debt / EBITDA[cite: 1].
* [cite_start]**Quantitative Portfolio Optimization:** Construction of the **Efficient Frontier** based on historical daily closing prices[cite: 1]. [cite_start]Portfolio asset weights were optimized under specific constraints (upper/lower weight bounds, minimal return thresholds, and maximum risk limits) across 5 distinct strategic criteria[cite: 1]:
  1. [cite_start]Maximum Return [cite: 1]
  2. [cite_start]Minimum Risk (Minimum Variance Portfolio) [cite: 1]
  3. [cite_start]Maximum Sharpe Ratio [cite: 1]
  4. [cite_start]Maximum Conditional Sharpe Ratio [cite: 1]
  5. [cite_start]Maximum Modified Sharpe Ratio [cite: 1]
* [cite_start]**Performance Backtesting & Evaluation:** Comparative analysis of an equally-weighted portfolio against the 5 optimized portfolio models across both 2024 and 2025 historical data[cite: 1]. [cite_start]The performance was benchmarked using key risk-adjusted metrics[cite: 1]:
  * [cite_start]Total Risk & Annualized Return [cite: 1]
  * [cite_start]Sharpe Ratio [cite: 1]
  * [cite_start]M² Coefficient (Modigliani-Modigliani) [cite: 1]
  * [cite_start]Treynor Measure [cite: 1]
  * [cite_start]Jensen's Alpha [cite: 1]
  * [cite_start]Conditional & Modified Sharpe Ratios [cite: 1]

## 🛠️ Tech Stack & Tools

* [cite_start]**Python (Jupyter Notebook):** Used for automating historical data collection, calculating asset growth rates, generating covariance matrices, and portfolio backtesting algorithms (`.py` / `.ipynb` scripts)[cite: 1].
* **Libraries:** `pandas`, `numpy`, `matplotlib` / `seaborn` (for matrix operations, financial data structuring, and plotting the Efficient Frontier).
* [cite_start]**MS Excel:** Comprehensive financial modeling, verification of optimization models, and dynamic asset tracking[cite: 1].

## 📂 Repository Structure
* [cite_start]`/data` — Historical daily closing prices and stock exchange data[cite: 1].
* [cite_start]`/scripts` — Python scripts and Jupyter Notebooks for data parsing, calculations, and optimization[cite: 1].
* [cite_start]`/models` — MS Excel workbook (`.xlsx`) featuring formulas, growth rates, covariance matrices, solver configurations, and charts[cite: 1].
* [cite_start]`/reports` — Comprehensive analytical report (`.docx`) and presentation (`.pptx`) detailing the strategic rationale, findings, and conclusions[cite: 1].
