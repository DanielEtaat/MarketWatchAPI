import time
from api import MarketWatchGame
from bot import misc
from bot.strategies import Strategy, PessimisticAverage
from hidden import username, password


class Investor:

    def __init__(self, game, strategy, save=0):
        self.game = game
        self.strategy = strategy
        self.save = save
        self.cash = string_to_float(game.portfolio_summary['cash remaining']) - save

    def invest_stocks(self, symbols, exchanges, buys, shorts, interval="2m", seconds=120):
        num_symbols = len(symbols)
        while not misc.after_hours():
            portfolio = self.game.portfolio_summary
            holdings = self.game.portfolio_holdings
            for i in range(num_symbols):
                self.invest(symbols[i], exchanges[i], portfolio, holdings,
                            interval=interval, 
                            should_buy=buys[i], 
                            should_short=shorts[i], 
                            num_symbols=num_symbols)
            time.sleep(seconds)
        return "MARKET CLOSED"

    def invest(self, symbol, exchange, portfolio, holdings, interval="2m", should_buy=True, should_short=False, num_symbols=1):
        data = misc.get_stock_data(symbol, period="4d", interval=interval)
        shares = 0
        if should_buy: 
            shares += self.game.get_buy_shares(symbol, holdings)
        if should_short: 
            shares -= self.game.get_short_shares(symbol, holdings)
        cash_max = string_to_float(portfolio['cash remaining']) - self.save
        cash = string_to_float(portfolio['net worth']) / num_symbols - abs(shares) * data[-1]
        if cash > cash_max: 
            cash = cash_max
        if cash < 0:
            cash = 0
        buy, cover, short = self.strategy.get_action(data, shares, cash, 0)
        print("{}: buy {}, cover {}, short {}".format(symbol, buy, cover, short))
        if buy > 0 and should_buy: 
            print(self.game.place_order(symbol, exchange, int(buy), order_type="BUY"))
        if buy < 0 and should_buy: 
            print(self.game.place_order(symbol, exchange, int(-buy), order_type="SELL"))
        if cover and should_short: 
            print(self.game.place_order(symbol, exchange, int(cover), order_type="COVER"))
        if short and should_short: 
            print(self.game.place_order(symbol, exchange, int(short), order_type="SHORT"))
        return True

def string_to_float(string):
    string = string.replace("$", "").replace(",", "")
    return float(string)

def thread():

    simp_avg = PessimisticAverage(look_back=15, risk=10e7, power=0, std_fac=3.5)
    wght_avg = PessimisticAverage(look_back=99, risk=20e6, power=1, std_fac=3.5)
    strategy = Strategy([simp_avg, wght_avg])
    
    exchngs = ['XNYS', 'XNAS', 'XNYS', 'XNAS'] # possible: XNYS, XASE, XNAS
    symbols = ['MR', 'MRKR', 'MR', 'MRKR']
    buys = [True, True, False, False]
    shrt = [False, False, True, True]
   
    while not misc.after_hours():
        try:
            game_name = 'algo-trading-1'
            game = MarketWatchGame(username, password, game_name)
            investor = Investor(game, strategy, save=0)
            investor.invest_stocks(symbols, exchngs, buys, shrt, interval="2m", seconds=120)
        except Exception as e:
            print(e)
            time.sleep(60)

if __name__ == "__main__":
    thread()
















