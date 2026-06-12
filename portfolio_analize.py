
import scipy as sp
import yfinance as yf
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 


tickers = ['AAPL','ASML','AMZN','PDD','GOOGL','META','AMGN','REGN','COST','PEP', 'USMV', 'VGSH']


year_base_start = "2024-01-01"
year_base_end = "2024-12-31"

year_test_start = "2025-01-01"
year_test_end = "2025-12-31"


def download(name, year_start, year_end):
    data = yf.download(name, start = year_start, end = year_end, interval = "1d")
    Close = data["Close"]
    return Close


data2024 = download(tickers, year_base_start, year_base_end)[tickers]
data2025 = download(tickers, year_test_start, year_test_end)[tickers]
nasdaq_composite = download("^IXIC", year_base_start, year_base_end).squeeze()
nasdaq_composite_2025 = download("^IXIC", year_test_start, year_test_end).squeeze()
def yield_valuation(data):#считаем дневную доходность через формулу ln(p2/p1)
    daily_yield = np.log(data/data.shift(1)).dropna()
    return daily_yield 

yield_2024 = yield_valuation(data2024) 
yield_2025 = yield_valuation(data2025)
yield_nasdaq = yield_valuation(nasdaq_composite)
yield_nasdaq_2025 = yield_valuation(nasdaq_composite_2025)
def cov_valuation(data):
    cov = np.cov(data.dropna().T)
    return cov 
cov_2024 = cov_valuation(yield_2024) #таблица ковариаций для акций

equal_weight = 1/len(tickers)
lists_weight = np.array([equal_weight for x in tickers]) #создаем список из равных весов для тикеров 

def portfolio_yield(weight, yield_data): #
    portfolio_yield = yield_data * weight
    portfolio_sum = portfolio_yield.sum(axis= 1)
    return portfolio_sum
portfolio_yield_2024 = portfolio_yield(equal_weight, yield_2024)


def average_yield(yield_data):
    avg = yield_data.mean(axis = 0)
    return avg
average_yield_2024 = average_yield(yield_2024) #считаем среднюю дневную доходность
nasdaq_yield_daily = average_yield(yield_nasdaq)
nasdaq_yield_daily_2025 = average_yield(yield_nasdaq_2025)

def annualy_yield(yield_data):
    annual_retention = np.exp(yield_data.sum(axis = 0)) - 1
    return annual_retention 
annual_ret_2024 = annualy_yield(yield_2024) #считаем годовую доходность через сложный процент
nasdaq_annual_yield = annualy_yield(yield_nasdaq)
nasdaq_annual_yield_2025 = annualy_yield(yield_nasdaq_2025)




def daily_std(yield_data):
    daily_std = yield_data.std(axis = 0)
    return daily_std

standart_deviation_2024 = daily_std(yield_2024) #считаем стандартное отклонение 
nasdaq_std = daily_std(yield_nasdaq)
nasdaq_std_2025 = daily_std(yield_nasdaq_2025)

def annual_dev(std):
    annual_dev = std * np.sqrt(252)
    return annual_dev
annual_standart_deviation_2024 = annual_dev(standart_deviation_2024)#252 - количество торговых дней в году
nasdaq_annual_dev = annual_dev(nasdaq_std)
nasdaq_annual_dev_2025 = annual_dev(nasdaq_std_2025)


#создаем таблицу для ковариационной матрицы на отдельном листе 
covariation_matrix_2024 = pd.DataFrame(cov_2024, columns = tickers, index = tickers)



#работаем с безрисковой доходностью
risk_free24 = pd.read_excel("DGS1.xlsx", sheet_name="Daily")
risk_free24["observation_date"] = pd.to_datetime(risk_free24["observation_date"])

risk_free24["DGS1"] = pd.to_numeric(risk_free24["DGS1"], errors="coerce") #игнорирует пустые клетки + проверка на числа  
avg_annual_rate24 = risk_free24["DGS1"].mean() / 100  
avg_daily_rate24 = (1 + avg_annual_rate24) ** (1/252) - 1

risk_free25 = pd.read_excel("DGS2.xlsx", sheet_name="Daily")
risk_free25["observation_date"] = pd.to_datetime(risk_free25["observation_date"])
risk_free25["DGS1"] = pd.to_numeric(risk_free25["DGS1"], errors="coerce") #игнорирует пустые клетки + проверка на числа  
avg_annual_rate25 = risk_free25["DGS1"].mean() / 100  
avg_daily_rate25 = (1 + avg_annual_rate25) ** (1/252) - 1



print(round(avg_daily_rate24*100, 2))
print(round(avg_daily_rate25*100, 2))
print(round(avg_annual_rate24*100, 2))
print(round(avg_annual_rate25*100, 2))
#расчет метрик
def sharp_ratio(annual_yield, std, annual_free_rate):
    sharp = (annual_yield-annual_free_rate)/std
    return sharp

def m2_calc(test_portfolio_yield, annual_dev_portfolio, ndq_annual_dev, ndq_annual_yield, annual_free_rate):
    m2 = (test_portfolio_yield - annual_free_rate) * (ndq_annual_dev/annual_dev_portfolio) - (ndq_annual_dev-annual_free_rate)
    return m2

z_stat = sp.stats.norm.ppf(0.01)

def beta_calc(weights, y_data, y_nasdaq, ndq_std):
    portfolio = portfolio_yield(weights, y_data)
    #поскольку у насдака 250 торговых дней а у портфеля 251 то приходится выкинуть лишние дни когда насдак не торгоавлся 
    align_data = pd.concat([portfolio, y_nasdaq], axis = 1).dropna() 
    portfolio_cov = np.cov(align_data.iloc[:, 0], align_data.iloc[:, 1])
    #для математической точности беты используем дисперсию именно по выровненным датам
    beta = portfolio_cov[0, 1] / portfolio_cov[1, 1]
    return beta

def treynor_calc(test_portfolio_yield, beta, annual_free_rate):
    treynor = (test_portfolio_yield-annual_free_rate)/beta
    return treynor 

def jensen_alpha_calc(test_portfolio_yield, beta, ndq_annual_dev, annual_free_rate): 
    jensen_alpha = test_portfolio_yield - (annual_free_rate + beta * (ndq_annual_dev - annual_free_rate))
    return jensen_alpha


def var_calc(daily_std_portfolio):
    var = z_stat * daily_std_portfolio
    return var

def cvar_calc(weights, y_data, var_threshold):
    portfolio = portfolio_yield(weights, y_data).dropna()
    worst_days = portfolio[portfolio <= var_threshold]
    if len(worst_days) == 0:
        return portfolio.min()
        
    cvar = worst_days.mean()
    return cvar
    
def consr_calc(daily_ret_portfolio, cvar, daily_free_rate):
    consr = (daily_ret_portfolio-daily_free_rate)/(abs(cvar))
    return consr

def skewness_calc(weights, y_data): 
    portfolio = portfolio_yield(weights, y_data).dropna()
    return portfolio.skew()

def kurtosis_calc(weights, y_data): 
    portfolio = portfolio_yield(weights, y_data).dropna()
    return portfolio.kurtosis()

def zmvar_calc(skewness, kurtosis):
    abs_z = abs(z_stat)
    z_mvar = -(abs_z + (1/6)*(abs_z**2 - 1)*skewness + (1/24)*(abs_z**3 - 3*abs_z)*kurtosis + (1/36)*(2*abs_z**3 - 5*abs_z)*(skewness**2))
    return z_mvar


def mvar_calc(zmvar, daily_std_portfolio):
    return zmvar * daily_std_portfolio

def modsr_calc(daily_ret_portfolio, mvar, daily_free_rate):
    modsr = (daily_ret_portfolio - daily_free_rate)/abs(mvar)
    return modsr

def geomean_calc(weights, y_data):
    portfolio = portfolio_yield(weights, y_data).dropna()
    geomean = np.exp(portfolio.mean()) - 1
    return geomean


def calculate_metrics(weights, y_data=yield_2024, y_nasdaq=yield_nasdaq, ndq_std=nasdaq_std, ndq_annual_yield=nasdaq_annual_yield, ndq_annual_dev=nasdaq_annual_dev, rf_annual=avg_annual_rate24, rf_daily=avg_daily_rate24):
    portfolio_yield_array = portfolio_yield(weights, y_data).dropna()
    
    retention_daily = average_yield(portfolio_yield_array)

    retention_annual = np.sum(weights * annualy_yield(y_data))

    standart_deviation_daily = daily_std(portfolio_yield_array)

    standart_deviation_annual = annual_dev(standart_deviation_daily)

    sharp = sharp_ratio(retention_annual, standart_deviation_annual, rf_annual)

    m2 = m2_calc(retention_annual, standart_deviation_annual, ndq_annual_dev, ndq_annual_yield, rf_annual)

    beta = beta_calc(weights, y_data, y_nasdaq, ndq_std)

    treynor = treynor_calc(retention_annual, beta, rf_annual)

    jensen_alpha = jensen_alpha_calc(retention_annual, beta, ndq_annual_dev, rf_annual)

    var = var_calc(standart_deviation_daily)

    cvar = cvar_calc(weights, y_data, var)

    consr = consr_calc(retention_daily, cvar, rf_daily)

    skew = skewness_calc(weights, y_data)

    kurt = kurtosis_calc(weights, y_data)

    zmvar = zmvar_calc(skew, kurt)

    mvar = mvar_calc(zmvar, standart_deviation_daily)

    modsr = modsr_calc(retention_daily, mvar, rf_daily)

    geomean = geomean_calc(weights, y_data)

    metrics = {
        "Ret. daily": retention_daily,
        "Ret. annual": retention_annual,
        "Std. daily": standart_deviation_daily,
        "Std. annual": standart_deviation_annual,
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
    for i in range(len(tickers)):
        metrics[tickers[i]] = weights[i]
        
    return metrics

    
    


#задаем индивидуальные границы для каждого актива в порядке списка tickers
#['aapl' 'asml' 'tsla' 'pdd' 'googl' 'meta' 'amgn' 'regn' 'cost' 'pep' 'usmv' 'vgsh']
bound = (
    (0.02, 0.15), #aapl
    (0.02, 0.08), #asml
    (0.02, 0.08), #tsla
    (0.02, 0.08), #pdd
    (0.02, 0.15), #googl
    (0.02, 0.15), #meta
    (0.02, 0.15), #amgn
    (0.02, 0.15), #regn
    (0.02, 0.15), #cost
    (0.02, 0.15), #pep
    (0.10, 0.25), #usmv
    (0.05, 0.20)  #vgsh
)


targetstd = 0.2
targetret = 0.05
constraint = (
    {"type": "eq", "fun": lambda x: x.sum() - 1.0}, #сумма всех весов равна 1
    {"type": "ineq", "fun": lambda x: x[0:10].sum() - 0.65}, #акции >= 65%
    {"type": "ineq", "fun": lambda x: 0.80 - x[0:10].sum()}, #акции <= 80%
    {"type": "ineq", "fun": lambda x: targetstd - annual_dev(daily_std(portfolio_yield(x, yield_2024).dropna()))}, #ограничение на риск <= 18%
    {"type": "ineq", "fun": lambda x: np.sum(x * annual_ret_2024) - targetret} #ограничение на доходность >= 5%
)
initial_guess = [0.075] * 10 + [0.15, 0.10] #начальные веса (сумма 1 акции 075 etf 025)


def optimize_portfolio(metric, maximize):  #функция для оптимизации портфеля настройка ограничений активов и суммы весов в коде
    def maximum_calc(w): #функция для оптимизации портфеля в зависимости нужно ли максимизировать или минимизировать метрику
        all_metrics = calculate_metrics(w)
        need_value = all_metrics[metric]
        if maximize == False: 
            return need_value
        else:
            return -need_value
    result = sp.optimize.minimize(maximum_calc, initial_guess, method = "SLSQP", bounds = bound, constraints = constraint) #аналог найти решения в экселе для подбора весов с максимизацией конткретного параметра 
    return calculate_metrics(result.x), result.x


#формирование 6 портфелей оптимизированных по разным метрикам
equal_metrics = calculate_metrics(lists_weight)
max_return, w_ret = optimize_portfolio("Ret. annual", True)
min_standart_deviation, w_std = optimize_portfolio("Std. daily", False)
max_sr, w_sr = optimize_portfolio("Sharp", True)
max_modsr, w_modsr = optimize_portfolio("ModSR", True)
max_consr, w_consr = optimize_portfolio("ConSR", True)

#табличка с дневным доходностью каждого вида портфеля
eq_daily = portfolio_yield(lists_weight, yield_2024)
ret_daily = portfolio_yield(w_ret, yield_2024)
std_daily = portfolio_yield(w_std, yield_2024)
sr_daily = portfolio_yield(w_sr, yield_2024)
modsr_daily = portfolio_yield(w_modsr, yield_2024)
consr_daily = portfolio_yield(w_consr, yield_2024)


daily_returns_df = pd.DataFrame({
    "Equal-weighted": eq_daily,
    "Max return": ret_daily,
    "Min StDev": std_daily,
    "Max SR": sr_daily,
    "Max Mod.SR": modsr_daily,
    "Max Con.SR": consr_daily
})


nasdaq_df = pd.DataFrame(yield_nasdaq)
nasdaq_df.loc["Annual return"] = [nasdaq_annual_yield]
nasdaq_df.loc["Average yield"] = [nasdaq_yield_daily]
nasdaq_df.loc["Standart deviation"] = [nasdaq_std]
nasdaq_df.loc["Annual standart deviation"] = [nasdaq_annual_dev]


last_result = pd.DataFrame({  "Equal-weighted": equal_metrics,
    "Max return": max_return,
    "Min StDev": min_standart_deviation,
    "Max SR": max_sr,
    "Max Mod.SR": max_modsr,
    "Max Con.SR": max_consr})


def calc_25(w): #расчет метрик за 2025 год с использованием тех же весов для сравнения с 24 годом
    return calculate_metrics(w, y_data=yield_2025, y_nasdaq=yield_nasdaq_2025, 
                             ndq_std=nasdaq_std_2025, ndq_annual_yield=nasdaq_annual_yield_2025, 
                             ndq_annual_dev=nasdaq_annual_dev_2025,
                             rf_annual=avg_annual_rate25, rf_daily=avg_daily_rate25)

last_result_2025 = pd.DataFrame({  
    "Equal-weighted": calc_25(lists_weight),
    "Max return": calc_25(w_ret),
    "Min StDev": calc_25(w_std),
    "Max SR": calc_25(w_sr),
    "Max Mod.SR": calc_25(w_modsr),
    "Max Con.SR": calc_25(w_consr)
})





def random_portfolios(amount, y_data):  #функция для симуляции случайных портфелей
    risk = []
    y = []
    asset_annual = annualy_yield(y_data)
    for i in range(0, amount):
        w = np.random.random(len(tickers))
        w = w/np.sum(w)
        test_yield = portfolio_yield(w, y_data).dropna()
        avg_test_yield = test_yield.mean(axis = 0)
        test_annual_yield = np.sum(w * asset_annual)
        test_daily_std = daily_std(test_yield)
        test_annual_std = annual_dev(test_daily_std)
        y.append(test_annual_yield)
        risk.append(test_annual_std)
    return risk, y




risk_24, y_24 = random_portfolios(10000, yield_2024) #симуляция 10000 портфелей в 2024 году

#equal_metrics = calculate_metrics(lists_weight)
#max_return w_ret = optimize_portfolio("ret annual" true)
#min_standart_deviation w_std = optimize_portfolio("std daily" false)
#max_sr w_sr = optimize_portfolio("sharp" true)
#max_modsr w_modsr = optimize_portfolio("modsr" true)
#max_consr w_consr = optimize_portfolio("consr" true)

#todo 
portfolio_ret_24_dot = max_sr["Ret. annual"]
portfolio_vol_24_dot = max_sr["Std. annual"]
portfolio_ret_25_dot = calc_25(w_sr)["Ret. annual"]
portfolio_vol_25_dot = calc_25(w_sr)["Std. annual"]


#создаем график облака портфелей и линии эффективности 
plt.figure(figsize = (12, 8)) #создаем полотно для графика
plt.scatter(risk_24, y_24, c = "#14248A", alpha = 0.2, s= 3, label = "Рандомные портфели") #наносим точки на график цвет точек синий прозрачность 02 размер 3
plt.scatter(portfolio_vol_24_dot,portfolio_ret_24_dot, c = "#8a1414", alpha =1, s = 50, label = "Наш портфель") #красный цвет обозначающий портфель 24 года
plt.title("Эффективная граница 2024 года")

#расчет и отрисовка самой дуги эффективности
target_returns = np.linspace(min(y_24), max(y_24), 100) #разрезаем облако на 100 равномерных целей от минимума до максимума по доходности 
frontier_volatility = [] #пустой список куда запишем минимальный риск для каждой из целевых доходностей

for target in target_returns:
    cons = ( #задаем математические ограничения для алгоритма:
        {"type": "eq", "fun": lambda x: np.sum(x * annual_ret_2024) - target}, #условие 2:  годовая доходность подобранного портфеля равнялась таргету
        {"type": "eq", "fun": lambda x: x.sum() - 1.0}, #сумма всех весов равна 1
        {"type": "ineq", "fun": lambda x: x[0:10].sum() - 0.65}, #акции >= 65%
        {"type": "ineq", "fun": lambda x: 0.80 - x[0:10].sum()}, #акции <= 80%
        {"type": "ineq", "fun": lambda x: targetstd - annual_dev(daily_std(portfolio_yield(x, yield_2024).dropna()))} #цель по риску 
    )
    res = sp.optimize.minimize( #просим библиотеку scipy найти минимум функции
        lambda x: annual_dev(daily_std(portfolio_yield(x, yield_2024).dropna())), #минимизируем годовой риск портфеля
        initial_guess, #отправная точка для поиска: равновзвешенный портфель
        method="SLSQP", #метод оптимизации 
        bounds=bound, #задаем индивидуальные границы для каждой акции и etf
        constraints=cons #указываем наши два жестких ограничения: веса = 1 и доходность = target
    )
    frontier_volatility.append(res.fun) #сохраняем найденный минимальный риск (fun при запросе fun(function) мы получаем финальное значение той функции которую просили минимизировать) в наш список
plt.plot(frontier_volatility, target_returns, 'k--', linewidth=2, label="Эффективная граница") #рисуем дугу x = найденный риск y = заданная доходность 'k--' означает черная пунктирная линия



#рисуем и расчитываем координаты линии cal
cal_x = [0, max_sr["Std. annual"]*1.5]
cal_y = [avg_annual_rate24, avg_annual_rate24 + max_sr["Sharp"] * cal_x[1]]
plt.plot(cal_x, cal_y, color='yellow', linestyle='-', linewidth=2, label="CAL") #рисуем линию cal
plt.xlabel("Годовой риск/волатильность")
plt.ylabel("Годовая доходность")
plt.legend()
plt.grid(True) #сетка на графике
plt.savefig("effective_line_2024.png")




#тоже самое для 25 года
risk_25, y_25 = random_portfolios(10000, yield_2025)
plt.figure(figsize = (12, 8))
plt.scatter(risk_25, y_25, c="#14248A", alpha=0.2, s= 3, label = "Рандомные портфели") 
plt.scatter(portfolio_vol_25_dot,portfolio_ret_25_dot, c = "#8a1414", alpha = 1, s = 50, label = "Наш портфель")
plt.scatter(portfolio_vol_24_dot,portfolio_ret_24_dot, c = "#148a32", alpha =1, s = 50, label = "Наш портфель в прошлом году")
plt.title("Эффективная граница 2025 года")
plt.xlabel("Годовой риск/волатильность")
plt.ylabel("Годовая доходность")
plt.legend()
plt.grid(True) 
plt.savefig("effective_line_2025.png")


#добавляем все посчитанные метрики в таблицу
yield_2024.loc["Annual return"] = annual_ret_2024
yield_2024.loc["Average yield"] = average_yield_2024
yield_2024.loc["Standart deviation"] = standart_deviation_2024
yield_2024.loc["Annual standart deviation"] = annual_standart_deviation_2024
yield_2024["portfolio yield"] = portfolio_yield_2024

with pd.ExcelWriter("close prices for 2024 - 2025.xlsx", engine = "xlsxwriter") as writer:
    data2024.to_excel (writer, sheet_name = "close prices for 2024")
    data2025.to_excel(writer, sheet_name="close prices for 2025")
    yield_2024.to_excel(writer, sheet_name="yield 2024") 
    covariation_matrix_2024.to_excel(writer, sheet_name = "cov matrix 2024")
    nasdaq_df.to_excel(writer, sheet_name= "nasdaq composite")
    last_result.to_excel(writer, sheet_name = "last results 2024")
    last_result_2025.to_excel(writer, sheet_name = "last results 2025")
    daily_returns_df.to_excel(writer, sheet_name="Daily Returns 2024")
    workbook = writer.book 
    worksheet = workbook.add_worksheet("Эффективная граница 2024 года")
    worksheet.insert_image("B2", "effective_line_2024.png")
    worksheet = workbook.add_worksheet("Эффективная граница 2025 года")
    worksheet.insert_image("B2", "effective_line_2025.png")

