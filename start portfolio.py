
import scipy as sp
import yfinance as yf
import pandas as pd 
import numpy as np 



tickers = ['AAPL','ASML','TSLA','PDD','GOOGL','META','AMGN','REGN','COST','PEP', "VOO", "IAU"]


year_base_start = "2024-01-01"
year_base_end = "2024-12-31"

year_test_start = "2025-01-01"
year_test_end = "2025-12-31"


def download(name, year_start, year_end):
    data = yf.download(name, start = year_start, end = year_end, interval = "1d")
    Close = data["Close"]
    return Close


data2024 = download(tickers, year_base_start, year_base_end)
data2025 = download(tickers, year_test_start, year_test_end)
nasdaq_composite = download("^IXIC", year_base_start, year_base_end).squeeze()
def yield_valuation(data):#считаем дневную доходность через формулу ln(p2/p1)
    daily_yield = np.log(data/data.shift(1))
    return daily_yield 

yield_2024 = yield_valuation(data2024) 
yield_nasdaq = yield_valuation(nasdaq_composite)
def cov_valuation(data):
    cov = np.cov(data.dropna().T)
    return cov 
cov_2024 = cov_valuation(yield_2024) # таблица ковариаций для акций

equal_weight = 1/len(tickers)
lists_weight = np.array([equal_weight for x in tickers]) # создаем список из равных весов для тикеров 

def portfolio_yield(weight, yield_data):
    portfolio_yield = yield_data * weight
    portfolio_sum = portfolio_yield.sum(axis= 1)#суммируем дневную доходность активов для равновзвешенного портфеля
    return portfolio_sum
portfolio_yield_2024 = portfolio_yield(equal_weight, yield_2024)


def average_yield(yield_data):
    avg = yield_data.mean(axis = 0)
    return avg
average_yield_2024 = average_yield(yield_2024) #считаем среднюю дневную доходность
nasdaq_yield_daily = average_yield(yield_nasdaq)

def annualy_yield(yield_data):
    annual_retention = np.exp(yield_data.sum(axis = 0)) - 1
    return annual_retention 
annual_ret_2024 = annualy_yield(yield_2024) #считаем годовую доходность через формулу e^(сумма дневных доходностей)-1
nasdaq_annual_yield = annualy_yield(yield_nasdaq)




def daily_std(yield_data):
    daily_std = yield_data.std(axis = 0)
    return daily_std

standart_deviation_2024 = daily_std(yield_2024) #считаем стандартное отклонение 
nasdaq_std = daily_std(yield_nasdaq)

def annual_dev(std):
    annual_dev = std * np.sqrt(252)
    return annual_dev
annual_standart_deviation_2024 = annual_dev(standart_deviation_2024)# 252 - количество торговых дней в году
nasdaq_annual_dev = annual_dev(nasdaq_std)


#Создаем таблицу для ковариационной матрицы на отдельном листе 
covariation_matrix_2024 = pd.DataFrame(cov_2024, columns = tickers, index = tickers)



#работаем с безрисковой доходностью
risk_free_2024 = pd.read_excel("treasure bills coupon rate 2024.xlsx")
avg_annual_rate = risk_free_2024["52 WEEKS COUPON EQUIVALENT"].mean()/100/100
avg_daily_rate = (1 + avg_annual_rate)**(1/252) - 1

# расчет метрик
def sharp_ratio(annual_yield, std):
    sharp = (annual_yield-avg_annual_rate)/std
    return sharp

def m2_calc(test_portfolio_yield,  annual_dev_portfolio):
    m2 = (test_portfolio_yield - avg_annual_rate) * (nasdaq_annual_dev/annual_dev_portfolio) - (nasdaq_annual_yield-avg_annual_rate)
    return m2

z_stat = sp.stats.norm.ppf(0.01)

def beta_calc(weights):
    portfolio = portfolio_yield(weights, yield_2024)
    #поскольку у насдака 250 торговых дней а у портфеля 251, то приходится выкинуть лишние дни когда насдак не торгоавлся 
    align_data = pd.concat([portfolio, yield_nasdaq], axis = 1).dropna() 
    portfolio_cov = np.cov(align_data.iloc[:, 0], align_data.iloc[:, 1])
    beta = portfolio_cov[0, 1]/(nasdaq_std**2)
    return beta

def treynor_calc(test_portfolio_yield, beta):
    treynor = (test_portfolio_yield-avg_annual_rate)/beta
    return treynor 

def jensen_alpha_calc(test_portfolio_yield, beta): 
    jensen_alpha = test_portfolio_yield - (avg_annual_rate + beta * (nasdaq_annual_yield - avg_annual_rate))
    return jensen_alpha


def var_calc(daily_std_portfolio):
    var = z_stat * daily_std_portfolio
    return var

def cvar_calc(weights):
    portfolio = portfolio_yield(weights, yield_2024).dropna()
    worst_scen = np.percentile(portfolio, 1)
    worst_days = portfolio[portfolio <= worst_scen]
    cvar = worst_days.mean()
    return cvar
    
def consr_calc(daily_ret_portfolio, cvar):
    consr = (daily_ret_portfolio-avg_daily_rate)/(abs(cvar))
    return consr

def skewness_calc(weights): 
    portfolio = portfolio_yield(weights, yield_2024).dropna()
    return portfolio.skew()

def kurtosis_calc(weights): 
    portfolio = portfolio_yield(weights, yield_2024).dropna()
    return portfolio.kurtosis()

def zmvar_calc(skewness, kurtosis):
    z_mvar = z_stat + (1/6)*(z_stat**2 - 1)*skewness + (1/24)*(z_stat**3 - 3*z_stat)*kurtosis + (1/36)*(2*z_stat**3 - 5*z_stat)*(skewness**2)
    return z_mvar

def mvar_calc(zmvar, daily_std_portfolio):
    return zmvar * daily_std_portfolio

def modsr_calc(daily_ret_portfolio, mvar):
    modsr = (daily_ret_portfolio - avg_daily_rate)/abs(mvar)
    return modsr

def geomean_calc(weights):
    portfolio = portfolio_yield(weights, yield_2024).dropna()
    geomean = np.exp(portfolio.mean()) - 1
    return geomean


def calculate_metrics(weights):
    portfolio_yield_array = portfolio_yield(weights, yield_2024).dropna()
    
    retention_daily = average_yield(portfolio_yield_array)

    retention_annual = annualy_yield(portfolio_yield_array)

    standart_deviation_daily = daily_std(portfolio_yield_array)

    standart_deviation_annual = annual_dev(standart_deviation_daily)

    sharp = sharp_ratio(retention_annual, standart_deviation_annual)

    m2 = m2_calc(retention_annual, standart_deviation_annual)

    beta = beta_calc(weights)

    treynor = treynor_calc(retention_annual, beta)

    jensen_alpha = jensen_alpha_calc(retention_annual, beta)

    var = var_calc(standart_deviation_daily)

    cvar = cvar_calc(weights)

    consr = consr_calc(retention_daily, cvar)

    skew = skewness_calc(weights)

    kurt = kurtosis_calc(weights)

    zmvar = zmvar_calc(skew, kurt)

    mvar = mvar_calc(zmvar, standart_deviation_daily)

    modsr = modsr_calc(retention_daily, mvar)

    geomean = geomean_calc(weights)

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
        "Geometric mean": geomean
    }
    for i in range(len(tickers)):
        metrics[tickers[i]] = weights[i]
        
    return metrics

    
    


bound = tuple((0.05, 0.25) for asset in tickers) 
constraint = {"type": "eq", "fun": lambda x: x.sum()-1}

initial_guess = list(lists_weight)


def optimize_portfolio(metric, maximize):
    def maximum_calc(w): 
        all_metrics = calculate_metrics(w)
        need_value = all_metrics[metric]
        if maximize == False: 
            return need_value
        else:
            return -need_value
    result = sp.optimize.minimize(maximum_calc, initial_guess, method = "SLSQP", bounds = bound, constraints = [constraint])
    return calculate_metrics(result.x), result.x

equal_metrics = calculate_metrics(lists_weight)
max_return, w_ret = optimize_portfolio("Ret. annual", True)
min_standart_deviation, w_std = optimize_portfolio("Std. daily", False)
max_sr, w_sr = optimize_portfolio("Sharp", True)
max_modsr, w_modsr = optimize_portfolio("ModSR", True)
max_consr, w_consr = optimize_portfolio("ConSR", True)

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



# добавляем все посчитанные метрики в таблицу
yield_2024.loc["Annual return"] = annual_ret_2024
yield_2024.loc["Average yield"] = average_yield_2024
yield_2024.loc["Standart deviation"] = standart_deviation_2024
yield_2024.loc["Annual standart deviation"] = annual_standart_deviation_2024
yield_2024["portfolio yield"] = portfolio_yield_2024

with pd.ExcelWriter("close prices for 2024 - 2025.xlsx") as writer:
    data2024.to_excel (writer, sheet_name = "close prices for 2024")
    data2025.to_excel(writer, sheet_name="close prices for 2025")
    yield_2024.to_excel(writer, sheet_name="yield 2024") 
    covariation_matrix_2024.to_excel(writer, sheet_name = "cov matrix 2024")
    nasdaq_df.to_excel(writer, sheet_name= "nasdaq composite")
    last_result.to_excel(writer, sheet_name = "last results")
    daily_returns_df.to_excel(writer, sheet_name="Daily Returns")





