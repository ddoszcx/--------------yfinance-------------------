import datetime as dt
import logging
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yfinance as yf

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Конфигурация ---
TICKERS = [
    'AAPL', 'ASML', 'AMZN', 'PDD', 'GOOGL', 'META', 
    'AMGN', 'REGN', 'COST', 'PEP', 'USMV', 'VGSH'
]

# Поскольку PDD самая молодая компания (IPO в эту дату)
BEG_TIME = dt.datetime(2018, 7, 26)
END_TIME = dt.datetime(2025, 12, 31)

# Веса для портфеля
PORTFOLIO_WEIGHTS = np.array([
    0.149999999999990, 0.0200000000000244, 0.08, 0.0200000000000108,
    0.0700000000000372, 0.15, 0.0200000000000039, 0.0200000000000113,
    0.149999999999983, 0.020000000000000, 0.249999999999948, 0.05
])


def fetch_data(tickers: List[str], start: dt.datetime, end: dt.datetime) -> pd.DataFrame:
    """Загружает данные цен закрытия."""
    data = yf.download(tickers, start=start, end=end, interval="1d")
    return data["Close"][tickers]


def daily_portfolio_yield(weights: np.ndarray, yield_data: pd.DataFrame) -> pd.Series:
    """Считает дневную доходность портфеля."""
    return (weights * yield_data).sum(axis=1)


def calculate_jump_diffusion_params(nav_returns: pd.Series, years: float) -> Tuple[float, float, float, float, float]:
    """
    Разделяет дни на обычные и 'скачки', возвращает параметры распределения:
    (дрейф, волатильность, средняя глубина скачка, разброс скачков, частота скачков).
    """
    mad = 1.4826 * (np.abs(nav_returns - nav_returns.median())).median()
    median_ret = nav_returns.median()
    
    normal_days = nav_returns[(nav_returns - median_ret) >= -3 * mad]
    jump_days = nav_returns[(nav_returns - median_ret) < -3 * mad]

    mu = np.mean(normal_days)
    sigma = np.std(normal_days)
    
    mu_j = np.mean(jump_days)
    sigma_j = np.std(jump_days)
    
    lambda_j = len(jump_days) / years
    return mu, sigma, mu_j, sigma_j, lambda_j


def simulation(
    mu: float, 
    sigma: float, 
    mu_j: float, 
    sigma_j: float, 
    lambda_j: float, 
    n_days: int = 252 * 5, 
    n_sims: int = 10000
) -> np.ndarray:
    """
    Симуляция траекторий методом Монте-Карло с jump-diffusion.
    Возвращает кумулятивную доходность портфеля по дням.
    """
    np.random.seed(42)  # Фиксируем seed для воспроизводимости
    matrix = np.random.normal(loc=mu, scale=sigma, size=(n_sims, n_days))
    matrix2 = np.random.binomial(n=1, p=lambda_j / 252, size=(n_sims, n_days))
    matrix3 = np.random.normal(loc=mu_j, scale=sigma_j, size=(n_sims, n_days))
    
    total_returns = matrix + (matrix3 * matrix2)
    total_path = np.exp(np.cumsum(total_returns, axis=1))
    return total_path


def main() -> None:
    """Точка входа."""
    logging.info("Starting Monte Carlo simulation script...")
    
    y_data = fetch_data(TICKERS, BEG_TIME, END_TIME)
    data_daily_yield = np.log(y_data / y_data.shift(1)).dropna()

    w_eq = np.ones(len(TICKERS)) / len(TICKERS)
    years = (END_TIME - BEG_TIME).days / 365.25

    # Параметры для нашего портфеля
    nav_returns = daily_portfolio_yield(PORTFOLIO_WEIGHTS, data_daily_yield)
    mu, sigma, mu_j, sigma_j, lambda_j = calculate_jump_diffusion_params(nav_returns, years)

    logging.info(f"Дрейф (очищенный): {mu*100:.2f}%")
    logging.info(f"Волатильность (очищенная): {sigma*100:.2f}%")
    logging.info(f"Средняя глубина скачков: {mu_j*100:.2f}%")
    logging.info(f"Частота скачков: {lambda_j:.2f}")

    # Параметры для равновзвешенного портфеля
    nav_returns_eq = daily_portfolio_yield(w_eq, data_daily_yield)
    mu_eq, sigma_eq, mu_j_eq, sigma_j_eq, lambda_j_eq = calculate_jump_diffusion_params(nav_returns_eq, years)

    # Симуляция сценариев (стресс-тесты)
    lamdas = np.array([1, 3, 5, 7, 10])
    mu_stress = np.array([-0.01, -0.035, -0.05, -0.10, -0.15])
    mu_base = 0.16 / 252

    res = []
    for x in lamdas:
        for y in mu_stress:
            path = simulation(mu_base, sigma, y, sigma_j, x) 
            result = path[:, -1] - 1 
            var_95 = np.percentile(result, 5)
            cvar_95 = result[result <= var_95].mean() 
            
            path_eq = simulation(mu_base, sigma_eq, y, sigma_j_eq, x) 
            result_eq = path_eq[:, -1] - 1 
            var_95_eq = np.percentile(result_eq, 5) 
            cvar_95_eq = result_eq[result_eq <= var_95_eq].mean() 
            
            diff = cvar_95 - cvar_95_eq
            res.append({'Частота': x, 'Сила удара': y, 'CVaR': cvar_95, 'CVaR_eq': cvar_95_eq, 'Разница': diff})

    df_res = pd.DataFrame(res).round({'Частота': 2})

    # Симуляция с историческими параметрами и график
    con = simulation(mu, sigma, mu_j, sigma_j, lambda_j)
    p10 = np.percentile(con, 10, axis=0)
    p50 = np.percentile(con, 50, axis=0)
    p90 = np.percentile(con, 90, axis=0)
    con_reduced = con[::100, :]

    plt.figure(figsize=(10, 6))
    plt.plot(con_reduced.T, alpha=0.05, color="gray")
    plt.plot(p10, color='red', linewidth=3, linestyle="--", label='10-й перц.')
    plt.plot(p50, color='yellow', linewidth=3, linestyle="--", label='50-й перц.')
    plt.plot(p90, color='green', linewidth=3, linestyle="--", label='90-й перц.')
    plt.title("Конус Монте-Карло (Jump-Diffusion)")
    plt.xlabel("Дни")
    plt.ylabel("Множитель капитала (1=100%)")
    plt.legend()
    plt.savefig("monte_carlo_cone.png")
    
    # Тепловая карта CVaR
    heatmap = df_res.pivot(index='Сила удара', columns='Частота', values='CVaR')
    plt.figure(figsize=(10, 6))
    heatmap.index = [f"{x:.2%}" for x in heatmap.index]
    sns.heatmap(heatmap, annot=True, fmt=".2%", cmap="RdYlGn", center=-0.20)
    plt.title("Обратный стресс-тест: CVaR для портфеля")
    plt.savefig("heatmap_cvar.png")

    # Тепловая карта разницы с равновзвешенным
    heatmap_diff = df_res.pivot(index='Сила удара', columns='Частота', values='Разница')
    plt.figure(figsize=(10, 6))
    heatmap_diff.index = [f"{x:.2%}" for x in heatmap_diff.index]
    sns.heatmap(heatmap_diff, annot=True, fmt=".2%", cmap="RdYlGn", center=0)
    plt.title("Сравнение с равновзвешенным (Наш CVaR - CVaR равновзвешенного)\n< 0 значит провалили порог")
    plt.savefig("heatmap_diff.png")

    logging.info("Graphs saved. Simulation complete.")


if __name__ == "__main__":
    main()
