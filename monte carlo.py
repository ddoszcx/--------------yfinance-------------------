import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt


tickers = [ "AAPL", "MSFT", "NVDA", "AMD", "ASML",  # Тикеры технологического сектора и смежных
    "AMZN", "TSLA", "BKNG", "MELI", "PDD",  # Тикеры потребительского сектора и онлайн-торговли
    "GOOGL", "META", "NFLX", "TMUS", "CHTR",  # Тикеры телекомов и медиа
    "AMGN", "GILD", "REGN", "VRTX", "ISRG",  # Тикеры здравоохранения и биотехнологий
    "COST", "PEP", "MDLZ", "KDP", "CCEP"] 
weights = np.array([0.04, 0.04, 0.04, 0.04, 0.04,
                    0.04, 0.04, 0.04, 0.04, 0.04,
                    0.04, 0.04, 0.04, 0.04, 0.04,
                    0.04, 0.04, 0.04, 0.04, 0.04,
                    0.04, 0.04, 0.04, 0.04, 0.04,
                    ]) 

initial_portfolio = 10000

train_start = '2024-01-01'
train_end = '2024-12-31'   
test_start = '2025-01-01'
test_end = '2025-12-31'    

time_horizon = 365
n_simulations = 100000       


# 2. ЗАГРУЗКА ДАННЫХ И РАСЧЕТ ПАРАМЕТРОВ (ПО 2024 ГОДУ)

print("Загрузка данных за 2024 год...")
data_2024 = yf.download(tickers, start=train_start, end=train_end)['Close']

# Если yfinance вернул Series (в случае 1 тикера), превращаем в DataFrame
if isinstance(data_2024, pd.Series):
    data_2024 = data_2024.to_frame(name=tickers[0])

# Очистка данных: удаляем тикеры, по которым данные не скачались вообще
valid_columns = data_2024.dropna(axis=1, how='all').columns.tolist()
invalid_tickers = [t for t in tickers if t not in valid_columns]

if invalid_tickers:
    print(f"ВНИМАНИЕ: Нет данных по тикерам {invalid_tickers}. Они исключены из портфеля.")

# Оставляем только валидные данные и заполняем пропуски внутри дней (например, праздники)
data_2024 = data_2024[valid_columns].ffill().bfill()

# Синхронизируем списки тикеров и весов
valid_indices = [tickers.index(t) for t in valid_columns]
tickers = [tickers[i] for i in valid_indices]
weights = weights[valid_indices]
# Нормируем веса до 1 (100%), так как часть активов могла отпасть
if weights.sum() > 0:
    weights = weights / weights.sum()

print(f"Актуальные тикеры: {tickers}")
print(f"Актуальные веса: {np.round(weights, 4)}")

# Расчет логарифмических доходностей
returns_2024 = np.log(data_2024 / data_2024.shift(1)).dropna(how='any')

if returns_2024.empty:
    raise ValueError("Ошибка: После очистки данных не осталось ни одной строки с доходностями за 2024 год.")

mean_returns = returns_2024.mean() 
cov_matrix = returns_2024.cov()

# Добавляем регуляризацию (малое число на диагонали), чтобы избежать ошибки LinAlgError
epsilon = 1e-8
cov_matrix_reg = cov_matrix + np.eye(cov_matrix.shape[0]) * epsilon
try:
    chol_matrix = np.linalg.cholesky(cov_matrix_reg)
except np.linalg.LinAlgError:
    raise ValueError("Невозможно вычислить разложение Холецкого даже с регуляризацией.")


# 3. ЗАГРУЗКА ФАКТИЧЕСКИХ ДАННЫХ ЗА 2025 ГОД (ДЛЯ СРАВНЕНИЯ)

print("\nЗагрузка фактических данных за 2025 год...")
data_2025 = yf.download(tickers, start=test_start, end=test_end)['Close']

if isinstance(data_2025, pd.Series):
    data_2025 = data_2025.to_frame(name=tickers[0])

# Выравниваем колонки, заполняем пропуски
data_2025 = data_2025[tickers].ffill().bfill()
returns_2025 = data_2025.pct_change().dropna(how='any')

if not returns_2025.empty:
    actual_portfolio_returns = (returns_2025 * weights).sum(axis=1)
    actual_portfolio_value = initial_portfolio * (1 + actual_portfolio_returns).cumprod()
else:
    actual_portfolio_value = pd.Series(dtype=float)


# 4. СИМУЛЯЦИЯ МОНТЕ-КАРЛО (ПРОГНОЗ НА 2025 ГОД)

print(f"\nЗапуск {n_simulations} симуляций...")
portfolio_sims = np.zeros((time_horizon, n_simulations))
portfolio_sims[0] = initial_portfolio

for t in range(1, time_horizon):
    random_gauss = np.random.normal(size=(len(tickers), n_simulations))
    correlated_random = np.dot(chol_matrix, random_gauss)
    
    asset_returns = np.exp(mean_returns.values[:, None] + correlated_random)
    portfolio_return_today = np.dot(weights, asset_returns)
    
    portfolio_sims[t] = portfolio_sims[t-1] * portfolio_return_today







# 5. ВИЗУАЛИЗАЦИЯ И ВЫВОДЫ

p10 = np.percentile(portfolio_sims, 10, axis=1)
p50 = np.percentile(portfolio_sims, 50, axis=1)
p90 = np.percentile(portfolio_sims, 90, axis=1)

plt.figure(figsize=(12, 7))

plt.plot(portfolio_sims[:, :100], color='gray', alpha=0.05)
plt.plot(p90, color='green', linestyle='--', linewidth=2, label='Оптимистичный (90-й перцентиль)')
plt.plot(p50, color='blue', linestyle='--', linewidth=2, label='Медианный (50-й перцентиль)')
plt.plot(p10, color='red', linestyle='--', linewidth=2, label='Пессимистичный (10-й перцентиль)')

actual_length = min(len(actual_portfolio_value), time_horizon)
if actual_length > 0:
    plt.plot(range(actual_length), actual_portfolio_value.values[:actual_length], 
             color='black', linewidth=3, label='ФАКТ 2025: Реальное поведение')

plt.title('Монте-Карло: Прогноз на базе 2024 г. vs Реальность 2025 г.', fontsize=14, fontweight='bold')
plt.xlabel('Торговые дни 2025 года', fontsize=12)
plt.ylabel('Стоимость портфеля', fontsize=12)
plt.legend(loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()





# Текстовый вывод для отчета
print("\n=== ИТОГИ НА КОНЕЦ 2025 ГОДА ===")
print(f"Стартовый капитал: ${initial_portfolio:,.2f}")
print(f"Пессимистичный прогноз (10-й перцентиль): ${p10[-1]:,.2f}")
print(f"Медианный прогноз (50-й перцентиль): ${p50[-1]:,.2f}")
print(f"Оптимистичный прогноз (90-й перцентиль): ${p90[-1]:,.2f}")

if not actual_portfolio_value.empty:
    print(f"ФАКТИЧЕСКИЙ результат портфеля: ${actual_portfolio_value.iloc[-1]:,.2f}")
else:
    print("ФАКТИЧЕСКИЙ результат портфеля: нет данных (слишком рано или сбой загрузки)")