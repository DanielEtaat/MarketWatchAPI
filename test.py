from bot import misc
from bot.strategies import Strategy, PessimisticAverage
import matplotlib.pyplot as plt
import numpy as np

class InvestorSim:

    def __init__(self, cash, strategy, commission=10):
        self.cash = cash
        self.strategy = strategy
        self.commission = commission
        self.reserve = 0

    def simulate_actions(self, symbol, period="2d", interval="2m", sample_size=20):
        data = misc.get_stock_data(symbol, period=period, interval=interval)
        tracking = {'prices': [], 'buys': [], 'sell': []}
        shares = 0
        for i in range(sample_size, len(data)):
            batch = data[i-sample_size:i]
            buy, cover, short = self.strategy.get_action(batch, shares, self.cash, self.reserve)
            action = buy + cover - short
            tracking['prices'].append(batch[-1])
            tracking['buys'].append(int(action>0))
            tracking['sell'].append(int(action<0))
        return tracking

    def simulate(self, symbol, period="2d", interval="2m", sample_size=20, nobuy=False, noshort=True):
        data = misc.get_stock_data(symbol, period=period, interval=interval)
        tracking = {'networth': [], 'shares': [], 'prices': []}
        shares = 0
        for i in range(sample_size, len(data)):
            batch = data[i-sample_size:i]
            short_reserve = min([0, shares]) * -data[-1]
            buy, cover, short = self.strategy.get_action(batch, shares, self.cash, short_reserve)
            if nobuy: buy = 0
            if noshort: short = 0
            shares = self.update(batch, shares, buy, cover, short)
            tracking['networth'].append(self.cash+self.reserve+shares*batch[-1])
            tracking['shares'].append(shares)
            tracking['prices'].append(batch[-1])
        print("{0} CHANGE: {1}%".format(symbol, 100*(data[-1]-data[sample_size-1])/data[sample_size-1]))
        return tracking

    def update(self, data, shares, buy, cover, short):
        if cover:
            shares += cover
            self.reserve -= cover * data[-1]
            profit = (self.reserve - abs(shares*data[-1])) * cover / abs(shares - cover)
            self.reserve -= profit
            self.cash += profit
            self.cash -= self.commission
        if short:
            self.reserve += short * data[-1]
            self.cash -= self.commission
        if buy:
            self.cash -= buy * data[-1]
            self.cash -= self.commission
        return shares + buy - short

    def reset(self, cash):
        self.cash = cash
        self.reserve = 0

def plot_sim(tracking):
    space = 2
    plt.plot(misc.normalize_data(tracking['networth'])+2*space)
    plt.plot(misc.normalize_data(tracking['shares'])+space)
    plt.plot(misc.normalize_data(tracking['prices']))
    plt.show()

def plot_actions(tracking):
    tracking['prices'] = np.array(tracking['prices'])
    tracking['buys'] = np.array(tracking['buys']) * tracking['prices']
    tracking['sell'] = np.array(tracking['sell']) * tracking['prices']
    tracking['buys'] = np.where(tracking['buys']==0, None, tracking['buys'])
    tracking['sell'] = np.where(tracking['sell']==0, None, tracking['sell'])
    plt.plot(tracking['prices'])
    plt.plot(tracking['sell'], 'ro', markersize=4)
    plt.plot(tracking['buys'], 'go', markersize=4)
    plt.show()

def simulate_stocks(stocks, strategy, cash, period="2y", interval="1d", test_buy=True, test_short=True):
    netprofit = 0
    investor = InvestorSim(cash, strategy, commission=0)
    for stock in stocks:
        if test_buy:
            investor.reset(cash)
            tracking = investor.simulate(stock, period=period, interval=interval, sample_size=99, nobuy=False, noshort=True)
            profit = 100*(tracking['networth'][-1]-tracking['networth'][0])/tracking['networth'][0]
            netprofit += cash * profit / 100
            print("BOT PROFIT: {0}%".format(profit))
            plot_sim(tracking)
        if test_short:
            investor.reset(cash)
            tracking_short = investor.simulate(stock, period=period, interval=interval, sample_size=99, nobuy=True, noshort=False)
            profit = 100*(tracking_short['networth'][-1]-tracking_short['networth'][0])/tracking_short['networth'][0]
            netprofit += cash * profit / 100
            print("SHORT BOT PROFIT: {0}%".format(profit))
            plot_sim(tracking_short)
        investor.reset(cash)
        plot_actions(investor.simulate_actions(stock, period=period, interval=interval, sample_size=99))
    print(netprofit)

# main program
if __name__ == "__main__":

    simp_avg = PessimisticAverage(look_back=15, risk=10e7, power=0, std_fac=3.5)
    wght_avg = PessimisticAverage(look_back=99, risk=20e6, power=1, std_fac=3.5)
    strategy = Strategy([simp_avg, wght_avg])

    stocks = ['AAPL', 'TSLA']
    cash = 100000 / (len(stocks) * 2)

    simulate_stocks(stocks, strategy, cash, period="2y", interval="1d", test_buy=True, test_short=True)
