from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


#список тикеров 
tickers = [ 
    "AAPL",
    "MSFT",
    "AMD",
    "ASML",
    "AMZN",
    "TSLA",
    "MELI",
    "PDD",
    "GOOGL",
    "META",
    "NFLX",
    "TMUS",
    "CHTR",
    "AMGN",
    "GILD",
    "REGN",
    "VRTX",
    "COST",
    "PEP",
    "MDLZ",
    "KDP",
    "CCEP"
]

#настройки бэктестинга
BASE_YEAR = 2024
TEST_YEAR = 2025
YEARS = [2022, 2023, 2024, 2025]

OUTPUT_PATH = Path.cwd() / "company info + metrics.xlsx"


def get_col_by_year(table, year):
    if table is None or table.empty:
        return None
    for col in table.columns:
        if getattr(col, "year", None) == year:
            return col
    return None


def get_row_value(table, row_names, col, default=pd.NA):
    if table is None or table.empty or col is None:
        return default
    if isinstance(row_names, str):
        row_names = [row_names]
    for row_name in row_names:
        if row_name in table.index:
            return table.loc[row_name, col]
    return default


def safe_abs(value):
    if pd.isna(value):
        return pd.NA
    return abs(value)


def safe_divide(numerator, denominator):
    if pd.isna(numerator) or pd.isna(denominator):
        return pd.NA
    if denominator == 0:
        return pd.NA
    return numerator / denominator


def safe_divide_series(num_series, den_series):
    #предотвращает ошибку деления на ноль заменяя 0 на nan в серии
    return num_series / den_series.replace(0, np.nan)


def cagr(start_value, end_value, years_count):
    if pd.isna(start_value) or pd.isna(end_value):
        return pd.NA
    if start_value <= 0 or end_value <= 0:
        return pd.NA
    if years_count <= 0:
        return pd.NA
    return (end_value / start_value) ** (1 / years_count) - 1  #расчет cagr по классической формуле и возврат результата


def collect_company_year(ticker_symbol, year, income, balance, cashflow, dividends, hist_prices):
    incomecol = get_col_by_year(income, year)
    balancecol = get_col_by_year(balance, year)
    prevbalancecol = get_col_by_year(balance, year - 1)
    cashflowcol = get_col_by_year(cashflow, year)

    warnings = []

    if incomecol is None: warnings.append("missing income column")
    if balancecol is None: warnings.append("missing balance column")
    if cashflowcol is None: warnings.append("missing cashflow column")
    if prevbalancecol is None: warnings.append("missing prev balance column")


    price = pd.NA
    if hist_prices is not None and not hist_prices.empty:
        year_hist = hist_prices[hist_prices.index.year == year]
        if not year_hist.empty:
            price = year_hist["Close"].iloc[-1]

    #income statement (отчет о прибылях и убытках)
    revenue = get_row_value(income, "Total Revenue", incomecol)
    gross_profit = get_row_value(income, "Gross Profit", incomecol)
    net_income = get_row_value(income, ["Net Income", "Net Income Common Stockholders"], incomecol)
    eps = get_row_value(income, "Diluted EPS", incomecol)
    diluted_shares = get_row_value(income, "Diluted Average Shares", incomecol)
    ebitda = get_row_value(income, "EBITDA", incomecol)
    ebit = get_row_value(income, ["EBIT", "Operating Income"], incomecol)
    interest_expense = safe_abs(get_row_value(income, ["Interest Expense", "Interest Expense Non Operating"], incomecol))  #извлечение и расчет модуля процентных расходов

    pretax_income = get_row_value(income, "Pretax Income", incomecol)
    tax_provision = get_row_value(income, "Tax Provision", incomecol)
    
    tax_rate = pd.NA
    if pd.notna(pretax_income) and pd.notna(tax_provision) and pretax_income > 0:
        tax_rate = tax_provision / pretax_income  #расчет эффективной ставки налога: налоги делим на доналоговую прибыль
    elif pd.notna(pretax_income) and pd.notna(tax_provision) and pretax_income <= 0:
        tax_rate = 0.0

    #balance sheet (балансовый отчет)
    cash = get_row_value(balance, ["Cash And Cash Equivalents", "Cash"], balancecol)
    current_assets = get_row_value(balance, "Current Assets", balancecol)
    total_assets = get_row_value(balance, "Total Assets", balancecol)
    
    prev_total_assets = get_row_value(balance, "Total Assets", prevbalancecol)
    average_total_assets = total_assets if pd.isna(prev_total_assets) else (total_assets + prev_total_assets) / 2
    
    current_liabilities = get_row_value(balance, "Current Liabilities", balancecol)
    inventory = get_row_value(balance, "Inventory", balancecol)

    equity = get_row_value(balance, ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"], balancecol)
    prev_equity = get_row_value(balance, ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"], prevbalancecol)

    average_equity = equity if pd.isna(prev_equity) else (equity + prev_equity) / 2  #расчет среднего капитала за год (или использование текущего если нет прошлого)
    total_debt = get_row_value(balance, "Total Debt", balancecol)

    invested_capital = get_row_value(balance, "Invested Capital", balancecol)
    if pd.isna(invested_capital) and pd.notna(total_debt) and pd.notna(equity) and pd.notna(cash):
        invested_capital = total_debt + equity - cash  #самостоятельный расчет инвестированного капитала (долг + капитал - кэш)

    #cash flow statement (отчет о движении денежных средств)
    operating_cash_flow = get_row_value(cashflow, "Operating Cash Flow", cashflowcol)
    capital_expenditure = get_row_value(cashflow, "Capital Expenditure", cashflowcol)
    fcf = get_row_value(cashflow, "Free Cash Flow", cashflowcol)

    if pd.isna(fcf) and not pd.isna(operating_cash_flow) and not pd.isna(capital_expenditure):
        fcf = operating_cash_flow + capital_expenditure  #расчет fcf вручную (capex часто отрицательный поэтому просто складываем)

    div_paid = safe_abs(get_row_value(cashflow, ["Common Stock Dividend Paid", "Cash Dividends Paid"], cashflowcol))

    #dps (дивиденды на акцию)
    dps = pd.NA
    if dividends is not None and not dividends.empty:
        annual_div = dividends.groupby(dividends.index.year).sum()  #группировка всех дивидендов за год и расчет суммы
        if year in annual_div.index:
            dps = annual_div.loc[year]

    if pd.isna(dps) and not pd.isna(div_paid) and not pd.isna(diluted_shares):
        dps = safe_divide(div_paid, diluted_shares)  #расчет dps делением общей суммы дивидендов на количество акций

    return {
        "Ticker": ticker_symbol,
        "Year": year,
        "Price": price,
        "Revenue": revenue,
        "Gross Profit": gross_profit,
        "Net Income": net_income,
        "EPS": eps,
        "DPS": dps,
        "Diluted Shares": diluted_shares,
        "FCF": fcf,
        "Operating Cash Flow": operating_cash_flow,
        "Capital Expenditure": capital_expenditure,
        "Common Dividends Paid": div_paid,
        "Cash": cash,
        "Current Assets": current_assets,
        "Total Assets": total_assets,
        "Average Total Assets": average_total_assets,
        "Current Liabilities": current_liabilities,
        "Inventory": inventory,
        "Equity": equity,
        "Average Equity": average_equity,
        "Total Debt": total_debt,
        "Invested Capital": invested_capital,
        "EBITDA": ebitda,
        "EBIT": ebit,
        "Interest Expense": interest_expense,
        "Pretax Income": pretax_income,
        "Tax Provision": tax_provision,
        "Tax Rate": tax_rate,
        "Warnings": "; ".join(warnings),
    }


def get_end_of_year_price(ticker, year):
    try:
        #берем данные за декабрь чтобы найти последнюю цену закрытия в году
        hist = ticker.history(start=f"{year}-12-01", end=f"{year+1}-01-01")
        if not hist.empty:
            return hist["Close"].iloc[-1]
    except Exception:
        pass
    return pd.NA


def collect_company_info(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    return {
        "Ticker": ticker_symbol,
        "Name": info.get("shortName", "N/A"),
        "Yahoo Sector": info.get("sector", "N/A"),
        "Yahoo Industry": info.get("industry", "N/A"),
    }


def collect_all_company_info(ticker_group):
    rows = []
    for ticker_symbol in ticker_group:
        print(f"Collecting info: {ticker_symbol}")
        try:
            rows.append(collect_company_info(ticker_symbol))
        except Exception as error:
            rows.append({
                "Ticker": ticker_symbol,
                "Name": "N/A",
                "Yahoo Sector": "N/A",
                "Yahoo Industry": "N/A",
                "Info Error": str(error),
            })
    return pd.DataFrame(rows)


def add_yearly_ratios(df):
    df = df.copy()

    #рентабельность и выплаты
    df["Gross Margin"] = df.apply(lambda row: safe_divide(row["Gross Profit"], row["Revenue"]), axis=1)  #расчет валовой маржи (валовая прибыль / выручка)
    df["Operating Margin"] = df.apply(lambda row: safe_divide(row["EBIT"], row["Revenue"]), axis=1)  #расчет операционной маржи (ebit / выручка)
    df["Net Profit Margin"] = df.apply(lambda row: safe_divide(row["Net Income"], row["Revenue"]), axis=1)  #расчет чистой маржи (чистая прибыль / выручка)
    df["ROE"] = df.apply(lambda row: safe_divide(row["Net Income"], row["Average Equity"]), axis=1)  #расчет рентабельности собственного капитала (roe)
    df["ROA"] = df.apply(lambda row: safe_divide(row["Net Income"], row["Average Total Assets"]), axis=1)  #расчет рентабельности активов (roa)
    
    def calc_nopat(row):
        tr = row.get("Tax Rate", pd.NA)
        if pd.isna(tr): tr = 0.21
        return row["EBIT"] * (1 - tr) if pd.notna(row["EBIT"]) else pd.NA  #расчет nopat = ebit * (1 - tax rate)
        
    df["NOPAT"] = df.apply(calc_nopat, axis=1)
    df["ROIC"] = df.apply(lambda row: safe_divide(row["NOPAT"], row["Invested Capital"]), axis=1)  #расчет рентабельности инвестированного капитала (roic)
    
    df["Payout Ratio based on NI"] = df.apply(lambda row: safe_divide(row["Common Dividends Paid"], row["Net Income"]), axis=1)  #расчет payout ratio по чистой прибыли (дивиденды / чистая прибыль)
    df["Payout Ratio based on FCF"] = df.apply(lambda row: safe_divide(row["Common Dividends Paid"], row["FCF"]), axis=1)  #расчет payout ratio по свободному денежному потоку (дивиденды / fcf)

    #долг и ликвидность
    df["D/E"] = df.apply(lambda row: safe_divide(row["Total Debt"], row["Equity"]), axis=1)  #расчет коэффициента debt/equity (долг / собственный капитал)
    df["Interest Coverage"] = df.apply(lambda row: safe_divide(row["EBIT"], row["Interest Expense"]), axis=1)  #расчет коэффициента покрытия процентов (ebit / проценты к уплате)
    df["OCF / Total Debt"] = df.apply(lambda row: safe_divide(row["Operating Cash Flow"], row["Total Debt"]), axis=1)  #расчет отношения операционного потока к долгу
    
    df["Net Debt"] = df["Total Debt"] - df["Cash"].fillna(0)  #расчет чистого долга (общий долг минус денежные средства)
    df["Net Debt / EBITDA"] = df.apply(lambda row: safe_divide(row["Net Debt"], row["EBITDA"]), axis=1)  #расчет показателя долговой нагрузки net debt / ebitda
    df["Current Ratio"] = df.apply(lambda row: safe_divide(row["Current Assets"], row["Current Liabilities"]), axis=1)  #расчет коэффициента текущей ликвидности (оборотные активы / краткосрочные обязательства)
    
    def safe_quick_ratio(row):
        inv = row["Inventory"] if pd.notna(row["Inventory"]) else 0
        return safe_divide(row["Current Assets"] - inv, row["Current Liabilities"])  #формула: (активы - запасы) / обязательства
        
    df["Quick Ratio"] = df.apply(safe_quick_ratio, axis=1)
    df["Cash Ratio"] = df.apply(lambda row: safe_divide(row["Cash"], row["Current Liabilities"]), axis=1)  #расчет коэффициента абсолютной ликвидности (кэш / обязательства)

    #оценка стоимости (мультипликаторы по годам)
    df["Market Cap"] = df["Price"] * df["Diluted Shares"]  #расчет рыночной капитализации для каждого года
    df["EV"] = df["Market Cap"] + df["Total Debt"].fillna(0) - df["Cash"].fillna(0)  #расчет стоимости предприятия ev
    
    df["P/E"] = df.apply(lambda row: safe_divide(row["Price"], row["EPS"]), axis=1)  #расчет мультипликатора p/e
    df["P/S"] = df.apply(lambda row: safe_divide(row["Market Cap"], row["Revenue"]), axis=1)  #расчет мультипликатора p/s
    df["P/FCF"] = df.apply(lambda row: safe_divide(row["Market Cap"], row["FCF"]), axis=1)  #расчет мультипликатора p/fcf
    df["EV/EBITDA"] = df.apply(lambda row: safe_divide(row["EV"], row["EBITDA"]), axis=1)  #расчет мультипликатора ev/ebitda
    df["Dividend Yield"] = df.apply(lambda row: safe_divide(row["DPS"], row["Price"]), axis=1)  #расчет дивидендной доходности
    df["P/B"] = df.apply(lambda row: safe_divide(row["Market Cap"], row["Equity"]), axis=1)  #расчет мультипликатора p/b

    return df


def collect_historical_data(ticker_group, years):
    rows = []
    for ticker_symbol in ticker_group:
        print(f"Collecting statements: {ticker_symbol}")
        ticker = yf.Ticker(ticker_symbol)

        try:
            income = ticker.income_stmt
            balance = ticker.balance_sheet
            cashflow = ticker.cashflow
            dividends = ticker.dividends
            
            #скачиваем цены за весь период одним запросом
            min_year = min(years)
            max_year = max(years)
            hist_prices = ticker.history(start=f"{min_year}-12-01", end=f"{max_year+1}-01-01")
        except Exception as error:
            for year in years:
                rows.append({"Ticker": ticker_symbol, "Year": year, "Warnings": f"download error: {error}"})
            continue

        for year in years:
            try:
                row = collect_company_year(ticker_symbol, year, income, balance, cashflow, dividends, hist_prices)
            except Exception as error:
                row = {"Ticker": ticker_symbol, "Year": year, "Warnings": f"row error: {error}"}
            rows.append(row)

    historical_data = pd.DataFrame(rows)
    
    #сортируем по тикеру и году чтобы ffill брал значения из прошлого
    historical_data = historical_data.sort_values(by=["Ticker", "Year"])
    
    #определяем колонки с сырыми данными (все кроме служебных)
    raw_cols = [col for col in historical_data.columns if col not in ["Ticker", "Year", "Warnings"]]
    
    #протягиваем (forward fill) пропущенные данные с прошлого года для каждого тикера
    historical_data[raw_cols] = historical_data.groupby("Ticker")[raw_cols].ffill()
    
    historical_data = add_yearly_ratios(historical_data)
    return historical_data


def calculate_company_summary(historical_data):
    summary_rows = []
    
    #базовый период (отрезаем будущее)
    base_data = historical_data[historical_data["Year"] <= BASE_YEAR]

    for ticker_symbol in base_data["Ticker"].unique():
        company_data = base_data[base_data["Ticker"] == ticker_symbol].sort_values("Year").copy()
        if company_data.empty: continue

        start_year = company_data["Year"].iloc[0]
        end_year = company_data["Year"].iloc[-1]
        years_count = end_year - start_year

        summary_row = {
            "Ticker": ticker_symbol,
            "Start Year": start_year,
            f"End Year (Base)": end_year,
            "Revenue CAGR": cagr(company_data["Revenue"].iloc[0], company_data["Revenue"].iloc[-1], years_count),
            "Net Income CAGR": cagr(company_data["Net Income"].iloc[0], company_data["Net Income"].iloc[-1], years_count),
            "EPS CAGR": cagr(company_data["EPS"].iloc[0], company_data["EPS"].iloc[-1], years_count),
            "DPS CAGR": cagr(company_data["DPS"].iloc[0], company_data["DPS"].iloc[-1], years_count),
            "FCF CAGR": cagr(company_data["FCF"].iloc[0], company_data["FCF"].iloc[-1], years_count),
            
            "Average Gross Margin": company_data["Gross Margin"].mean(skipna=True),
            "Average Operating Margin": company_data["Operating Margin"].mean(skipna=True),
            "Average Net Profit Margin": company_data["Net Profit Margin"].mean(skipna=True),
            "Average ROE": company_data["ROE"].mean(skipna=True),
            "Average ROA": company_data["ROA"].mean(skipna=True),
            "Average ROIC": company_data["ROIC"].mean(skipna=True),
            "Average Tax Rate": company_data["Tax Rate"].mean(skipna=True),
            "Average Payout NI": company_data["Payout Ratio based on NI"].mean(skipna=True),
            "Average Payout FCF": company_data["Payout Ratio based on FCF"].mean(skipna=True),
            
            "Average D/E": company_data["D/E"].mean(skipna=True),
            "Average Interest Coverage": company_data["Interest Coverage"].mean(skipna=True),
            "Average OCF / Total Debt": company_data["OCF / Total Debt"].mean(skipna=True),
            "Average Net Debt / EBITDA": company_data["Net Debt / EBITDA"].mean(skipna=True),
            
            "Average Current Ratio": company_data["Current Ratio"].mean(skipna=True),
            "Average Quick Ratio": company_data["Quick Ratio"].mean(skipna=True),
            "Average Cash Ratio": company_data["Cash Ratio"].mean(skipna=True),
            
            #данные последнего базового года (для расчета мультипликаторов)
            "Latest Price": company_data["Price"].iloc[-1],
            "Latest DPS": company_data["DPS"].iloc[-1],
            "Latest EPS": company_data["EPS"].iloc[-1],
            "Latest FCF": company_data["FCF"].iloc[-1],
            "Latest Revenue": company_data["Revenue"].iloc[-1],
            "Latest EBITDA": company_data["EBITDA"].iloc[-1],
            "Latest Total Debt": company_data["Total Debt"].iloc[-1],
            "Latest Cash": company_data["Cash"].iloc[-1],
            "Latest Equity": company_data["Equity"].iloc[-1],
            "Latest Diluted Shares": company_data["Diluted Shares"].iloc[-1],
        }
        summary_rows.append(summary_row)

    return pd.DataFrame(summary_rows)


def extract_test_year_data(historical_data):
    test_data = historical_data[historical_data["Year"] == TEST_YEAR].copy()
    
    #добавим год к названиям колонок для ясности
    rename_map = {}
    for col in test_data.columns:
        if col not in ["Ticker", "Year", "Warnings"]:
            rename_map[col] = f"{col} ({TEST_YEAR})"
            
    test_data = test_data.rename(columns=rename_map)
    return test_data


def add_valuation_multiples(df, year):
    #требует наличия колонок price diluted shares и финансовых показателей
    
    if year == BASE_YEAR:  #если расчет для базового года
        price_col = "Latest Price"
        eps_col = "Latest EPS"
        rev_col = "Latest Revenue"
        fcf_col = "Latest FCF"
        ebitda_col = "Latest EBITDA"
        dps_col = "Latest DPS"
        debt_col = "Latest Total Debt"
        cash_col = "Latest Cash"
        equity_col = "Latest Equity"
        shares_col = "Latest Diluted Shares"
    else:  #расчет для тестового (другого) года
        price_col = f"Price ({TEST_YEAR})"
        eps_col = f"EPS ({TEST_YEAR})"
        rev_col = f"Revenue ({TEST_YEAR})"
        fcf_col = f"FCF ({TEST_YEAR})"
        ebitda_col = f"EBITDA ({TEST_YEAR})"
        dps_col = f"DPS ({TEST_YEAR})"
        debt_col = f"Total Debt ({TEST_YEAR})"
        cash_col = f"Cash ({TEST_YEAR})"
        equity_col = f"Equity ({TEST_YEAR})"
        shares_col = f"Diluted Shares ({TEST_YEAR})"
        
    df[f"Market Cap ({year})"] = df[price_col] * df[shares_col]  #расчет рыночной капитализации (цена акции * количество акций)
    df[f"EV ({year})"] = df[f"Market Cap ({year})"] + df[debt_col].fillna(0) - df[cash_col].fillna(0)  #расчет стоимости предприятия ev (капитализация + долг - кэш)
    
    df[f"P/E ({year})"] = safe_divide_series(df[price_col], df[eps_col])  #расчет мультипликатора p/e (цена / прибыль)
    df[f"P/S ({year})"] = safe_divide_series(df[f"Market Cap ({year})"], df[rev_col])  #расчет мультипликатора p/s (капитализация / выручка)
    df[f"P/FCF ({year})"] = safe_divide_series(df[f"Market Cap ({year})"], df[fcf_col])  #расчет мультипликатора p/fcf (капитализация / fcf)
    df[f"EV/EBITDA ({year})"] = safe_divide_series(df[f"EV ({year})"], df[ebitda_col])  #расчет мультипликатора ev/ebitda
    df[f"Dividend Yield ({year})"] = safe_divide_series(df[dps_col], df[price_col])  #расчет дивидендной доходности (dps / цена)
    df[f"P/B ({year})"] = safe_divide_series(df[f"Market Cap ({year})"], df[equity_col])  #расчет мультипликатора p/b (капитализация / собственный капитал)
    
    if "EPS CAGR" in df.columns:
        df[f"PEG ({year})"] = df.apply(lambda row: safe_divide(row[f"P/E ({year})"], row["EPS CAGR"] * 100) if pd.notna(row.get("EPS CAGR")) and row["EPS CAGR"] > 0 else pd.NA, axis=1)  #расчет peg
    else:
        df[f"PEG ({year})"] = pd.NA
        
    return df


def safe_sheet_name(name):
    bad_chars = ["\\", "/", "*", "[", "]", ":", "?"]
    for char in bad_chars:
        name = name.replace(char, " ")
    return name[:31]


def make_metric_sheet(historical_data, metric):
    return historical_data.pivot_table(
        index="Ticker",
        columns="Year",
        values=metric,
        aggfunc="first",
    ).sort_index()


def export_to_excel(historical_data, company_info, summary_data, test_data):
    metrics = [
        "Price", "Revenue", "Gross Profit", "Net Income", "EPS", "DPS", "FCF",
        "Pretax Income", "Tax Provision", "Tax Rate", "NOPAT", "Invested Capital",
        "Gross Margin", "Operating Margin", "Net Profit Margin", "ROE", "ROA", "ROIC",
        "Payout Ratio based on NI", "Payout Ratio based on FCF",
        "D/E", "Interest Coverage", "OCF / Total Debt", "Net Debt / EBITDA",
        "Current Ratio", "Quick Ratio", "Cash Ratio",
        "Total Assets", "Market Cap", "EV", "P/E", "P/S", "P/FCF", "EV/EBITDA", "Dividend Yield", "P/B"
    ]

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        historical_data.to_excel(writer, sheet_name="Raw Data", index=False)
        company_info.to_excel(writer, sheet_name="Market Info", index=False)
        
        summary_data.to_excel(writer, sheet_name=f"Summary (up to {BASE_YEAR})", index=False)
        test_data.to_excel(writer, sheet_name=f"Test Results ({TEST_YEAR})", index=False)

        for metric in metrics:
            if metric in historical_data.columns:
                metric_sheet = make_metric_sheet(historical_data, metric)
                metric_sheet.to_excel(writer, sheet_name=safe_sheet_name(metric))


def main():
    historical_data = collect_historical_data(tickers, YEARS)
    company_info = collect_all_company_info(tickers)

    #1 сводка для принятия решений (до 2024 года)
    summary_data = calculate_company_summary(historical_data)
    summary_data = summary_data.merge(company_info, on="Ticker", how="left")
    summary_data = add_valuation_multiples(summary_data, BASE_YEAR)

    #2 данные для проверки (2025 год)
    test_data = extract_test_year_data(historical_data)
    test_data = test_data.merge(company_info, on="Ticker", how="left")
    if not test_data.empty:
        test_data = add_valuation_multiples(test_data, TEST_YEAR)  #расчет мультипликаторов для тестового года

    #3 сохранение
    export_to_excel(historical_data, company_info, summary_data, test_data)
    print(f"Done: {OUTPUT_PATH}")


main()
