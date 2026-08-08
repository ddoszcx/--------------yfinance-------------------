import logging
from typing import Dict, List, Tuple, Union, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy as sp
import scipy.stats
import yfinance as yf

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Конфигурация ---
TICKERS = [
    'AAPL', 'ASML', 'AMZN', 'PDD', 'GOOGL', 'META', 
    'AMGN', 'REGN', 'COST', 'PEP', 'USMV', 'VGSH'
]

YEAR_BASE_START = "2024-01-01"
YEAR_BASE_END = "2024-12-31"

YEAR_TEST_START = "2025-01-01"
YEAR_TEST_END = "2025-12-31"

TARGET_STD = 0.2
TARGET_RET = 0.05

BOUNDS = (
    (0.02, 0.15),  # aapl
    (0.02, 0.08),  # asml
    (0.02, 0.08),  # tsla/amzn
    (0.02, 0.08),  # pdd
    (0.02, 0.15),  # googl
    (0.02, 0.15),  # meta
    (0.02, 0.15),  # amgn
    (0.02, 0.15),  # regn
    (0.02, 0.15),  # cost
    (0.02, 0.15),  # pep
    (0.10, 0.25),  # usmv
    (0.05, 0.20)   # vgsh
)

INITIAL_GUESS = [0.075] * 10 + [0.15, 0.10]
Z_STAT = scipy.stats.norm.ppf(0.01)


def download_data(tickers: List[str], year_start: str, year_end: str) -> pd.DataFrame:
    """Скачивает цены закрытия для списка тикеров."""
    data = yf.download(tickers, start=year_start, end=year_end, interval="1d")
    return data["Close"]


def calculate_daily_yield(data: pd.DataFrame) -> pd.DataFrame:
    """Считает дневную доходность через формулу ln(p2/p1)."""
    return np.log(data / data.shift(1)).dropna()


def calculate_covariance(data: pd.DataFrame) -> np.ndarray:
    """Рассчитывает матрицу ковариаций."""
    return np.cov(data.dropna().T)


def calculate_portfolio_yield(weights: np.ndarray, yield_data: pd.DataFrame) -> pd.Series:
    """Рассчитывает доходность портфеля на основе весов."""
    portfolio_yld = yield_data * weights
    return portfolio_yld.sum(axis=1)


def calculate_average_yield(yield_data: Union[pd.DataFrame, pd.Series]) -> Union[pd.Series, float]:
    """Считает среднюю дневную доходность."""
    return yield_data.mean(axis=0)


def calculate_annual_yield(yield_data: Union[pd.DataFrame, pd.Series]) -> Union[pd.Series, float]:
    """Считает годовую доходность через сложный процент."""
    return np.exp(yield_data.sum(axis=0)) - 1


def calculate_daily_std(yield_data: Union[pd.DataFrame, pd.Series]) -> Union[pd.Series, float]:
    """Считает стандартное отклонение (дневное)."""
    return yield_data.std(axis=0)


def calculate_annual_dev(std: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """Считает годовое стандартное отклонение (252 торговых дня)."""
    return std * np.sqrt(252)


def get_risk_free_rates() -> Tuple[float, float, float, float]:
    """Загружает безрисковые ставки из локальных файлов DGS1.xlsx и DGS2.xlsx."""
    try:
        risk_free24 = pd.read_excel("DGS1.xlsx", sheet_name="Daily")
        risk_free24["DGS1"] = pd.to_numeric(risk_free24["DGS1"], errors="coerce")
        avg_annual_rate24 = risk_free24["DGS1"].mean() / 100
        avg_daily_rate24 = (1 + avg_annual_rate24) ** (1 / 252) - 1

        risk_free25 = pd.read_excel("DGS2.xlsx", sheet_name="Daily")
        risk_free25["DGS1"] = pd.to_numeric(risk_free25["DGS1"], errors="coerce")
        avg_annual_rate25 = risk_free25["DGS1"].mean() / 100
        avg_daily_rate25 = (1 + avg_annual_rate25) ** (1 / 252) - 1
        
        return avg_annual_rate24, avg_daily_rate24, avg_annual_rate25, avg_daily_rate25
    except Exception as e:
        logging.error(f"Error loading risk free rates: {e}. Using defaults.")
        return 0.05, 0.05 / 252, 0.05, 0.05 / 252


def calculate_metrics(
    weights: np.ndarray,
    y_data: pd.DataFrame,
    y_nasdaq: pd.Series,
    ndq_std: float,
    ndq_annual_yield: float,
    ndq_annual_dev: float,
    rf_annual: float,
    rf_daily: float
) -> Dict[str, float]:
    """Вычисляет все основные метрики портфеля для заданных весов."""
    portfolio_yield_array = calculate_portfolio_yield(weights, y_data).dropna()
    
    retention_daily = calculate_average_yield(portfolio_yield_array)
    retention_annual = np.sum(weights * calculate_annual_yield(y_data))
    
    std_daily = calculate_daily_std(portfolio_yield_array)
    std_annual = calculate_annual_dev(std_daily)

    sharp = (retention_annual - rf_annual) / std_annual if std_annual else 0
    m2 = (retention_annual - rf_annual) * (ndq_annual_dev / std_annual) - (ndq_annual_yield - rf_annual) if std_annual else 0

    align_data = pd.concat([portfolio_yield_array, y_nasdaq], axis=1).dropna()
    portfolio_cov = np.cov(align_data.iloc[:, 0], align_data.iloc[:, 1])
    beta = portfolio_cov[0, 1] / portfolio_cov[1, 1] if portfolio_cov[1, 1] else 1

    treynor = (retention_annual - rf_annual) / beta if beta else 0
    jensen_alpha = retention_annual - (rf_annual + beta * (ndq_annual_yield - rf_annual))

    var = Z_STAT * std_daily
    
    worst_days = portfolio_yield_array[portfolio_yield_array <= var]
    cvar = worst_days.mean() if len(worst_days) > 0 else portfolio_yield_array.min()
    
    consr = (retention_daily - rf_daily) / abs(cvar) if cvar else 0

    skew = portfolio_yield_array.skew()
    kurt = portfolio_yield_array.kurtosis()

    zmvar = Z_STAT + (1/6)*(Z_STAT**2 - 1)*skew + (1/24)*(Z_STAT**3 - 3*Z_STAT)*kurt - (1/36)*(2*Z_STAT**3 - 5*Z_STAT)*(skew**2)
    mvar = zmvar * std_daily
    modsr = (retention_daily - rf_daily) / abs(mvar) if mvar else 0

    geomean = np.exp(portfolio_yield_array.mean()) - 1

    metrics = {
        "Ret. daily": retention_daily,
        "Ret. annual": retention_annual,
        "Std. daily": std_daily,
        "Std. annual": std_annual,
        "Sharp": sharp,
        "M2": m2,
        "Beta": beta,
        "Treynor": treynor,
        "Jensen's alpha": jensen_alpha,
        "VaR": var,
        "CVaR": cvar,
        "ConSR": consr,
        "Skewness": skew,
        "Kurtosis": kurt,
        "Z-MVAR": zmvar,
        "MVAR": mvar,
        "ModSR": modsr,
        "Geometric mean daily": geomean
    }
    
    for i, ticker in enumerate(TICKERS):
        metrics[ticker] = weights[i]
        
    return metrics


def optimize_portfolio(
    metric: str, 
    maximize: bool,
    y_data: pd.DataFrame,
    y_nasdaq: pd.Series,
    ndq_std: float,
    ndq_annual_yield: float,
    ndq_annual_dev: float,
    rf_annual: float,
    rf_daily: float,
    annual_ret_data: pd.Series
) -> Tuple[Dict[str, float], np.ndarray]:
    """Оптимизирует портфель по выбранной метрике."""
    
    def objective(w: np.ndarray) -> float:
        mets = calculate_metrics(w, y_data, y_nasdaq, ndq_std, ndq_annual_yield, ndq_annual_dev, rf_annual, rf_daily)
        val = mets[metric]
        return -val if maximize else val

    constraints = (
        {"type": "eq", "fun": lambda x: x.sum() - 1.0},
        {"type": "ineq", "fun": lambda x: x[0:10].sum() - 0.65},
        {"type": "ineq", "fun": lambda x: 0.80 - x[0:10].sum()},
        {"type": "ineq", "fun": lambda x: TARGET_STD - calculate_annual_dev(calculate_daily_std(calculate_portfolio_yield(x, y_data).dropna()))},
        {"type": "ineq", "fun": lambda x: np.sum(x * annual_ret_data) - TARGET_RET}
    )

    result = sp.optimize.minimize(
        objective, 
        INITIAL_GUESS, 
        method="SLSQP", 
        bounds=BOUNDS, 
        constraints=constraints
    )
    
    final_metrics = calculate_metrics(result.x, y_data, y_nasdaq, ndq_std, ndq_annual_yield, ndq_annual_dev, rf_annual, rf_daily)
    return final_metrics, result.x


def generate_random_portfolios(amount: int, y_data: pd.DataFrame, num_assets: int) -> Tuple[List[float], List[float]]:
    """Симулирует случайные портфели."""
    risk, returns = [], []
    asset_annual = calculate_annual_yield(y_data)
    
    for _ in range(amount):
        w = np.random.random(num_assets)
        w /= np.sum(w)
        
        test_yield = calculate_portfolio_yield(w, y_data).dropna()
        test_annual_yield = np.sum(w * asset_annual)
        test_annual_std = calculate_annual_dev(calculate_daily_std(test_yield))
        
        returns.append(test_annual_yield)
        risk.append(test_annual_std)
        
    return risk, returns


def main() -> None:
    """Точка входа."""
    logging.info("Downloading data...")
    data2024 = download_data(TICKERS, YEAR_BASE_START, YEAR_BASE_END)[TICKERS]
    data2025 = download_data(TICKERS, YEAR_TEST_START, YEAR_TEST_END)[TICKERS]
    
    nasdaq_composite = download_data(["^IXIC"], YEAR_BASE_START, YEAR_BASE_END).squeeze()
    nasdaq_composite_2025 = download_data(["^IXIC"], YEAR_TEST_START, YEAR_TEST_END).squeeze()

    yield_2024 = calculate_daily_yield(data2024)
    yield_2025 = calculate_daily_yield(data2025)
    
    yield_nasdaq = calculate_daily_yield(nasdaq_composite)
    yield_nasdaq_2025 = calculate_daily_yield(nasdaq_composite_2025)

    cov_2024 = calculate_covariance(yield_2024)
    covariation_matrix_2024 = pd.DataFrame(cov_2024, columns=TICKERS, index=TICKERS)

    equal_weight = 1 / len(TICKERS)
    lists_weight = np.array([equal_weight] * len(TICKERS))

    avg_annual_rate24, avg_daily_rate24, avg_annual_rate25, avg_daily_rate25 = get_risk_free_rates()
    logging.info(f"RF Rates 24: {avg_annual_rate24:.2%}, 25: {avg_annual_rate25:.2%}")

    ndq_std_24 = calculate_daily_std(yield_nasdaq)
    ndq_ann_yield_24 = calculate_annual_yield(yield_nasdaq)
    ndq_ann_dev_24 = calculate_annual_dev(ndq_std_24)

    ndq_std_25 = calculate_daily_std(yield_nasdaq_2025)
    ndq_ann_yield_25 = calculate_annual_yield(yield_nasdaq_2025)
    ndq_ann_dev_25 = calculate_annual_dev(ndq_std_25)

    annual_ret_2024 = calculate_annual_yield(yield_2024)
    avg_yld_24 = calculate_average_yield(yield_2024)
    std_24 = calculate_daily_std(yield_2024)
    ann_std_24 = calculate_annual_dev(std_24)

    # Функция-обертка для оптимизации
    def opt(metric: str, maximize: bool) -> Tuple[Dict[str, float], np.ndarray]:
        return optimize_portfolio(
            metric, maximize, yield_2024, yield_nasdaq, ndq_std_24, 
            ndq_ann_yield_24, ndq_ann_dev_24, avg_annual_rate24, avg_daily_rate24, annual_ret_2024
        )

    logging.info("Optimizing portfolios...")
    equal_metrics = calculate_metrics(lists_weight, yield_2024, yield_nasdaq, ndq_std_24, ndq_ann_yield_24, ndq_ann_dev_24, avg_annual_rate24, avg_daily_rate24)
    max_return, w_ret = opt("Ret. annual", True)
    min_std, w_std = opt("Std. daily", False)
    max_sr, w_sr = opt("Sharp", True)
    max_modsr, w_modsr = opt("ModSR", True)
    max_consr, w_consr = opt("ConSR", True)
    
    eq_daily = calculate_portfolio_yield(lists_weight, yield_2024)
    ret_daily = calculate_portfolio_yield(w_ret, yield_2024)
    std_daily = calculate_portfolio_yield(w_std, yield_2024)
    sr_daily = calculate_portfolio_yield(w_sr, yield_2024)
    modsr_daily = calculate_portfolio_yield(w_modsr, yield_2024)
    consr_daily = calculate_portfolio_yield(w_consr, yield_2024)

    daily_returns_df = pd.DataFrame({
        "Equal-weighted": eq_daily,
        "Max return": ret_daily,
        "Min StDev": std_daily,
        "Max SR": sr_daily,
        "Max Mod.SR": modsr_daily,
        "Max Con.SR": consr_daily
    })

    # 2025 evaluation
    def calc_25(w: np.ndarray) -> Dict[str, float]:
        return calculate_metrics(
            w, yield_2025, yield_nasdaq_2025, ndq_std_25, 
            ndq_ann_yield_25, ndq_ann_dev_25, avg_annual_rate25, avg_daily_rate25
        )

    last_result_2024 = pd.DataFrame({
        "Equal-weighted": equal_metrics,
        "Max return": max_return,
        "Min StDev": min_std,
        "Max SR": max_sr,
        "Max Mod.SR": max_modsr,
        "Max Con.SR": max_consr
    })

    last_result_2025 = pd.DataFrame({
        "Equal-weighted": calc_25(lists_weight),
        "Max return": calc_25(w_ret),
        "Min StDev": calc_25(w_std),
        "Max SR": calc_25(w_sr),
        "Max Mod.SR": calc_25(w_modsr),
        "Max Con.SR": calc_25(w_consr)
    })
    
    # ---------------- PLOTS AND OPTIMIZATION ----------------
    logging.info("Generating plots...")
    risk_24, y_24 = generate_random_portfolios(10000, yield_2024, len(TICKERS))
    
    portfolio_ret_24_dot = max_sr["Ret. annual"]
    portfolio_vol_24_dot = max_sr["Std. annual"]
    portfolio_ret_25_dot = calc_25(w_sr)["Ret. annual"]
    portfolio_vol_25_dot = calc_25(w_sr)["Std. annual"]

    plt.figure(figsize=(12, 8))
    plt.scatter(risk_24, y_24, c="#14248A", alpha=0.2, s=3, label="Рандомные портфели")
    plt.scatter(portfolio_vol_24_dot, portfolio_ret_24_dot, c="#8a1414", alpha=1, s=50, label="Наш портфель")
    plt.title("Эффективная граница 2024 года")

    target_returns = np.linspace(min(y_24), max(y_24), 100)
    frontier_volatility = []

    for target in target_returns:
        cons = (
            {"type": "eq", "fun": lambda x: np.sum(x * annual_ret_2024) - target},
            {"type": "eq", "fun": lambda x: x.sum() - 1.0},
            {"type": "ineq", "fun": lambda x: x[0:10].sum() - 0.65},
            {"type": "ineq", "fun": lambda x: 0.80 - x[0:10].sum()},
            {"type": "ineq", "fun": lambda x: TARGET_STD - calculate_annual_dev(calculate_daily_std(calculate_portfolio_yield(x, yield_2024).dropna()))}
        )
        res = sp.optimize.minimize(
            lambda x: calculate_annual_dev(calculate_daily_std(calculate_portfolio_yield(x, yield_2024).dropna())),
            INITIAL_GUESS,
            method="SLSQP",
            bounds=BOUNDS,
            constraints=cons
        )
        frontier_volatility.append(res.fun)
        
    plt.plot(frontier_volatility, target_returns, 'k--', linewidth=2, label="Эффективная граница")

    cal_x = [0, max_sr["Std. annual"] * 1.5]
    cal_y = [avg_annual_rate24, avg_annual_rate24 + max_sr["Sharp"] * cal_x[1]]
    plt.plot(cal_x, cal_y, color='yellow', linestyle='-', linewidth=2, label="CAL")
    plt.xlabel("Годовой риск/волатильность")
    plt.ylabel("Годовая доходность")
    plt.legend()
    plt.grid(True)
    plt.savefig("effective_line_2024_refactored.png")

    risk_25, y_25 = generate_random_portfolios(10000, yield_2025, len(TICKERS))
    plt.figure(figsize=(12, 8))
    plt.scatter(risk_25, y_25, c="#14248A", alpha=0.2, s=3, label="Рандомные портфели")
    plt.scatter(portfolio_vol_25_dot, portfolio_ret_25_dot, c="#8a1414", alpha=1, s=50, label="Наш портфель")
    plt.scatter(portfolio_vol_24_dot, portfolio_ret_24_dot, c="#148a32", alpha=1, s=50, label="Наш портфель в прошлом году")
    plt.title("Эффективная граница 2025 года")
    plt.xlabel("Годовой риск/волатильность")
    plt.ylabel("Годовая доходность")
    plt.legend()
    plt.grid(True)
    plt.savefig("effective_line_2025_refactored.png")
    
    yield_2024.loc["Annual return"] = annual_ret_2024
    yield_2024.loc["Average yield"] = avg_yld_24
    yield_2024.loc["Standart deviation"] = std_24
    yield_2024.loc["Annual standart deviation"] = ann_std_24
    yield_2024["portfolio yield"] = calculate_portfolio_yield(lists_weight, yield_2024)

    nasdaq_df = pd.DataFrame(yield_nasdaq)
    nasdaq_df.loc["Annual return"] = [ndq_ann_yield_24]
    nasdaq_df.loc["Average yield"] = [calculate_average_yield(yield_nasdaq)]
    nasdaq_df.loc["Standart deviation"] = [ndq_std_24]
    nasdaq_df.loc["Annual standart deviation"] = [ndq_ann_dev_24]

    logging.info("Saving results...")
    with pd.ExcelWriter("close_prices_2024_2025_refactored.xlsx", engine="xlsxwriter") as writer:
        data2024.to_excel(writer, sheet_name="close prices for 2024")
        data2025.to_excel(writer, sheet_name="close prices for 2025")
        yield_2024.to_excel(writer, sheet_name="yield 2024")
        covariation_matrix_2024.to_excel(writer, sheet_name="cov matrix 2024")
        nasdaq_df.to_excel(writer, sheet_name="nasdaq composite")
        last_result_2024.to_excel(writer, sheet_name="last results 2024")
        last_result_2025.to_excel(writer, sheet_name="last results 2025")
        daily_returns_df.to_excel(writer, sheet_name="Daily Returns 2024")
        
        workbook = writer.book
        worksheet1 = workbook.add_worksheet("Эффективная граница 2024 года")
        worksheet1.insert_image("B2", "effective_line_2024_refactored.png")
        worksheet2 = workbook.add_worksheet("Эффективная граница 2025 года")
        worksheet2.insert_image("B2", "effective_line_2025_refactored.png")

    logging.info("Finished.")


if __name__ == "__main__":
    main()
