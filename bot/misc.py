import datetime, holidays, pytz, time
import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf

# checks whether the market is open or closed
tz = pytz.timezone('US/Eastern')
def after_hours(now=None):
	if not now:
		now = datetime.datetime.now(tz)
	open_time = datetime.time(hour=9, minute=30, second=0)
	close_time = datetime.time(hour=16, minute=0, second=0)
	return now.strftime('%Y-%m-%d') in holidays.US() or \
		now.time() < open_time or now.time() > close_time or \
		now.date().weekday() > 4

# grabs and formats stock data from yahoo finance
def get_stock_data(symbol, period="5d", interval="5m"):
	stock_data = yf.download(symbol, period=period, interval=interval)
	return stock_data[["Open"]].dropna().values.flatten()

# helper method for test_bot()
def normalize_data(data):
	data = np.array(data)
	min_val, max_val = min(data), max(data)
	data = (data - min_val) / (max_val - min_val)
	return data
