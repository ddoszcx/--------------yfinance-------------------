import numpy as np 
import pandas as pd 
import yfinance as yf 
import datetime as dt 
import seaborn as sns
import matplotlib.pyplot as plt



tickers = ['AAPL','ASML','AMZN','PDD','GOOGL','META','AMGN','REGN','COST','PEP', 'USMV', 'VGSH']



beg_time = dt.datetime(2018, 7, 26) #поскольку PDD здесь самая молодая компания(в эту дату у них было IPO)
end_time = dt.datetime(2025, 12, 31)


y_data = yf.download(tickers, beg_time, end_time, interval = "1d")
y_data = y_data["Close"][tickers]


data_daily_yield = np.log(y_data/y_data.shift(1)).dropna() #дневная доходность 

w = np.array([0.149999999999990,
0.0200000000000244,
0.08,
0.0200000000000108,
0.0700000000000372,
0.15,
0.0200000000000039,
0.0200000000000113,
0.149999999999983,
0.020000000000000,
0.249999999999948,
0.05])
w_eq = np.ones(len(tickers)) / len(tickers) #равновзвешенный портфель


def daily_portfolio_yield(weights, yield_data): #доходность портфеля 
    return (weights * yield_data).sum(axis = 1)

nav_returns = daily_portfolio_yield(w, data_daily_yield) #дневная доходность портфеля


mad = 1.4826* (np.abs(nav_returns-nav_returns.median())).median() #абсолюнтое медианное отклонение 14826 это 75 перцентиль

median_ret = nav_returns.median()
#шумовые дни (все что не является крахом правый хвост остается)
normal_days = nav_returns[(nav_returns - median_ret) >= -3*mad]
#дни со скачками только жесткие просадки левый хвост
jump_days = nav_returns[(nav_returns - median_ret) < -3*mad]

mu = np.mean(normal_days) #дрейф

sigma = np.std(normal_days)#волатильность

mu_j = np.mean(jump_days)#средняя глубина 

sigma_j = np.std(jump_days)#разброс скачков 
years = (end_time - beg_time).days / 365.25 # учитываем высокосный год
lambda_j = len(jump_days) / years #историческая частота скачков 

print(f"очищенный дневной дрейф = {round(mu*100, 2)}% ")
print(f"очищенная средняя дневная волантильность = {round(sigma*100, 2)}% ")
print(f"средняя глубина скачков в периоды кризисов= {round(mu_j*100, 2)}%")
print(f"частота скачков в периоды кризисов = {round(lambda_j, 2)}")


#считаем параметры для равновзвешенного портфеля
nav_returns_eq = daily_portfolio_yield(w_eq, data_daily_yield)
mad_eq = 1.4826 * (np.abs(nav_returns_eq - nav_returns_eq.median())).median()
median_ret_eq = nav_returns_eq.median()
normal_days_eq = nav_returns_eq[(nav_returns_eq - median_ret_eq) >= -3*mad_eq]
jump_days_eq = nav_returns_eq[(nav_returns_eq - median_ret_eq) < -3*mad_eq]

mu_eq = np.mean(normal_days_eq)
sigma_eq = np.std(normal_days_eq)
mu_j_eq = np.mean(jump_days_eq)
sigma_j_eq = np.std(jump_days_eq)
lambda_j_eq = len(jump_days_eq) / years


def simulation(mu, sigma, mu_j, sigma_j, lambda_j, n_days=252*5, n_sims=10000): #10000 симуляций на 5 лет
    np.random.seed(42) # фиксируем генератор случайных чисел для однородности для отчета
    matrix = np.random.normal(loc=mu, scale=sigma, size=(n_sims, n_days)) #генерация рыночного шума
    matrix2 = np.random.binomial(n = 1, p = lambda_j/252, size = (n_sims, n_days))#генерируем скачки 

    matrix3 = np.random.normal(loc = mu_j, scale = sigma_j, size = (n_sims, n_days))#матрица силы удара
    total_returns = matrix + (matrix3*matrix2)
    total_path= np.exp(np.cumsum(total_returns, axis = 1)) #кумулятивная доходность портфеля с каждым днем
    return total_path




lamdas = np.array([1, 3, 5, 7, 10]) #частота шоков в год
mu_stress = np.array([-0.01, -0.035, -0.05, -0.10, -0.15]) #средняя глубина скачка (от -1% до -15%)


mu_base = 0.16 / 252 # уровень роста  индекса насдак в тех отрасли переведенная в дневную размерность
res = []
#сумуляция сценариев
for x in lamdas:
    for y in mu_stress:
        #ля нашего портфеля
        path = simulation(mu_base, sigma, y, sigma_j, x) 
        result = path[:, -1]-1 
        var_95 = np.percentile(result, 5)
        cvar_95 = result[result<=var_95].mean() 
        
        #для равновесного портфеля
        path_eq = simulation(mu_base, sigma_eq, y, sigma_j_eq, x) 
        result_eq = path_eq[:, -1]-1 
        var_95_eq = np.percentile(result_eq, 5) 
        cvar_95_eq = result_eq[result_eq<=var_95_eq].mean() 
        
        #расчет разницы между стратегиями: если отрицательная значит наш портфель просел сильнее равновзвешенного
        diff = cvar_95 - cvar_95_eq
        
        res.append({'Частота': x, 'Сила удара': y, 'CVaR': cvar_95, 'CVaR_eq': cvar_95_eq, 'Разница': diff})



df_res = pd.DataFrame(res).round({'Частота': 2})



#делаем симуляцию монте карло с историческими параметрами сцкнарий 1 
con = simulation(mu, sigma, mu_j, sigma_j,lambda_j)
p10 = np.percentile(con, 10, axis = 0)
p50 = np.percentile(con, 50, axis = 0)
p90 = np.percentile(con, 90, axis = 0)
con_reduced = con[::100, :]
plt.figure(figsize = (10, 6))
plt.plot(con_reduced.T, alpha = 0.05, color = "gray")
plt.plot(p10, color = 'red', linewidth= 3, linestyle = "--", label='10-й перц.')
plt.plot(p50, color = 'yellow', linewidth = 3, linestyle = "--", label = '50-й перц.')
plt.plot(p90, color = 'green', linewidth = 3, linestyle = "--", label = '90-й перц.')
plt.title("Конус Монте-Карло(Jump-Diffusion)")
plt.xlabel("Дни")
plt.ylabel("множитель капитала (1=100%)")
plt.legend()
plt.show()

heatmap = df_res.pivot(index = 'Сила удара', columns = 'Частота', values = 'CVaR')#делаем сводную таблицу для построения тепловой карты
plt.figure(figsize = (10, 6)) #задаем размер полотна
heatmap.index = [f"{x:.2%}" for x in heatmap.index]
sns.heatmap(heatmap, annot=True, fmt=".2%", cmap="RdYlGn", center=-0.20)
plt.title("Обратный стресс тест: CVaR для портфеля")
plt.show()

heatmap_diff = df_res.pivot(index = 'Сила удара', columns = 'Частота', values = 'Разница')
plt.figure(figsize = (10, 6))
heatmap_diff.index = [f"{x:.2%}" for x in heatmap_diff.index]
#красный цвет - наш портфель хуже (разница < 0) зеленый - лучше (разница > 0)
sns.heatmap(heatmap_diff, annot=True, fmt=".2%", cmap="RdYlGn", center=0)
plt.title("Сравнение с равновзвешенным портфелем: (Наш CVaR - CVaR равновзвешенного)\n< 0 значит наш портфель провалил порог толерантности")
plt.show()



        



        






























