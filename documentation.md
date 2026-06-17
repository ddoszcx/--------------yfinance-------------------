# Documentation for the Financial Metrics Calculation Script

This document describes the data sources and calculation formulas for all financial metrics used in the script. All raw data is loaded using the `yfinance` library, which retrieves information from the Yahoo Finance portal.

## 1. Data Sources (yfinance API)

The script uses the following methods of the `yf.Ticker` object:
* **`ticker.income_stmt`** — Income Statement.
* **`ticker.balance_sheet`** — Balance Sheet.
* **`ticker.cashflow`** — Cash Flow Statement.
* **`ticker.dividends`** — Historical dividend payout data.
* **`ticker.history`** — Historical stock quotes (used to get the year-end price).
* **`ticker.info`** — General company information (sector, industry, shares outstanding).

---

## 2. Metrics Extracted Directly from Reports

### Income Statement
* **Revenue** — from the `Total Revenue` line.
* **Gross Profit** — from the `Gross Profit` line.
* **Net Income** — from the `Net Income` or `Net Income Common Stockholders` lines.
* **EPS (Earnings Per Share)** — from the `Diluted EPS` line.
* **Diluted Shares** — from the `Diluted Average Shares` line.
* **EBITDA** — from the `EBITDA` line.
* **EBIT (Operating Income)** — from the `EBIT` or `Operating Income` lines.
* **Interest Expense** — the absolute value from the `Interest Expense` or `Interest Expense Non Operating` lines.
* **Pretax Income** — from the `Pretax Income` line.
* **Tax Provision** — from the `Tax Provision` line.

### Balance Sheet
* **Cash** — from the `Cash And Cash Equivalents` or `Cash` lines.
* **Current Assets** — from the `Current Assets` line.
* **Total Assets** — from the `Total Assets` line.
* **Current Liabilities** — from the `Current Liabilities` line.
* **Inventory** — from the `Inventory` line.
* **Equity** — from the `Stockholders Equity`, `Common Stock Equity`, or `Total Equity Gross Minority Interest` lines.
* **Total Debt** — from the `Total Debt` line.

### Cash Flow Statement
* **Operating Cash Flow** — from the `Operating Cash Flow` line.
* **Capital Expenditure (CapEx)** — from the `Capital Expenditure` line.
* **Common Dividends Paid** — the absolute value from the `Common Stock Dividend Paid` or `Cash Dividends Paid` lines.

---

## 3. Metrics Calculated Based on Extracted Data

### Basic Metrics and Intermediate Calculations
* **Tax Rate (Effective Tax Rate):** `Tax Provision / Pretax Income` (if Pretax Income > 0; if <= 0, the rate is assumed to be 0%).
* **Average Equity:** `(Current Year Equity + Previous Year Equity) / 2`.
* **Invested Capital:** Extracted directly (`Invested Capital`); if missing, calculated as `Total Debt + Equity - Cash`.
* **FCF (Free Cash Flow):** Extracted directly (`Free Cash Flow`); if missing, calculated as `Operating Cash Flow + Capital Expenditure` (CapEx is usually negative in reports).
* **DPS (Dividends Per Share):** The sum of dividends paid for the year from `ticker.dividends`. If no data is available, calculated as `Common Dividends Paid / Diluted Shares`.
* **NOPAT (Net Operating Profit After Tax):** `EBIT * (1 - Tax Rate)`. If `Tax Rate` is unknown, a default rate of `21%` is used.
* **Net Debt:** `Total Debt - Cash`.

### Profitability and Margins
* **Gross Margin:** `Gross Profit / Revenue`.
* **Operating Margin:** `EBIT / Revenue`.
* **Net Profit Margin:** `Net Income / Revenue`.
* **ROE (Return on Equity):** `Net Income / Average Equity`.
* **ROIC (Return on Invested Capital):** `NOPAT / Invested Capital`.

### Payout Policies
* **Payout Ratio based on NI:** `Common Dividends Paid / Net Income`.
* **Payout Ratio based on FCF:** `Common Dividends Paid / FCF`.

### Debt Load and Coverage
* **D/E (Debt-to-Equity):** `Total Debt / Equity`.
* **Interest Coverage:** `EBIT / Interest Expense`.
* **OCF / Total Debt:** `Operating Cash Flow / Total Debt`.
* **Net Debt / EBITDA:** `Net Debt / EBITDA`.

### Liquidity
* **Current Ratio:** `Current Assets / Current Liabilities`.
* **Quick Ratio:** `(Current Assets - Inventory) / Current Liabilities`.
* **Cash Ratio:** `Cash / Current Liabilities`.

### Growth Metrics (CAGR)
The formula for calculating CAGR: `(Ending Value / Beginning Value) ^ (1 / Number of Years) - 1`.
Applied to: **Revenue, Net Income, EPS, DPS, FCF**.

### Valuation Multiples
Calculations use the year-end stock price (`Price`), `Shares Outstanding`, and balance sheet `Equity`.
* **Market Cap:** `Price * Shares Outstanding`.
* **EV (Enterprise Value):** `Market Cap + Total Debt - Cash`.
* **P/E (Price-to-Earnings):** `Price / EPS`.
* **P/S (Price-to-Sales):** `Market Cap / Revenue`.
* **P/FCF (Price-to-Free Cash Flow):** `Market Cap / FCF`.
* **EV/EBITDA:** `EV / EBITDA`.
* **Dividend Yield:** `DPS / Price`.
* **P/B (Price-to-Book):** `Market Cap / Equity`.
* **PEG (P/E to Growth):** `P/E / (EPS CAGR * 100)`.

---

## 4. Handling Missing Data

When automatically gathering data from Yahoo Finance, some metrics may be missing (due to differences in reporting standards, business models, or parser issues). The script applies the following rules to ensure the financial accuracy of calculations:

### 4.1. Forward Fill
Before calculating derived metrics, the script checks basic financial figures (revenue, assets, cash, etc.) year by year. If a metric is missing for the current year but existed in the previous year, the script automatically **copies the value from the prior year**. If there is no data at all for the entire period, the cell remains empty.

### 4.2. Safe Division and Justified Missing Data
Most derived ratios (P/E, margins, ROE, interest coverage, etc.) are calculated using a special safe division function.
* **Rule:** If at least one of the required inputs is missing (`NaN`), the calculation is aborted, and the function returns an empty cell.
* **Reason:** If a company (e.g., ASML) is missing `Operating Cash Flow` due to IFRS standards, equating it to zero would severely distort the `OCF / Total Debt` ratio. Therefore, the script leaves such calculations blank.

### 4.3. Justified Forcing to Zero
There are 3 strict exceptions in the code where a missing value is forcibly replaced with zero (`0`). This is done only when "emptiness" in the report physically means the absence of that asset or liability:
1.  **Inventory:** If there is no inventory (like IT companies META or NFLX), it is set to zero. This allows for the correct calculation of the *Quick Ratio*.
2.  **Total Debt:** If a company has no loans, debt is set to zero. This allows for the calculation of *EV (Enterprise Value)*.
3.  **Cash:** If cash is not separated out, it is set to zero for the calculation of *Net Debt*.

### 4.4. Fallbacks (Alternative Formulas)
If Yahoo Finance does not provide a ready-made metric, the script attempts to calculate it manually:
* **FCF (Free Cash Flow):** If the specific line is missing, it's calculated as `Operating Cash Flow + Capital Expenditure`.
* **Invested Capital:** Calculated as `Total Debt + Equity - Cash`.
* **Average Equity:** Used for ROE. If previous year equity is missing, the script skips averaging and simply uses the current year's equity.
* **Tax Rate:** If the company incurred a pretax loss, the effective rate is set to `0`. If tax data is completely missing, a standard corporate rate of `21%` is applied to calculate NOPAT.
* **DPS (Dividends Per Share):** If a ready-made dividend history isn't available, it is calculated as total `Common Dividends Paid` divided by diluted shares.

### 4.5. PEG Multiple
The PEG (P/E to Growth) ratio requires a stable growth rate. Since year-over-year EPS growth is too volatile, the script calculates PEG **only on the Summary tab** using the averaged long-term `EPS CAGR`, rather than calculating it historically for each individual year.
