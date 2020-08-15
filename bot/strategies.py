import numpy as np


class Strategy:

	def __init__(self, strategies):
		self.strategies = strategies

	def strategy(self, data):
		action = 0
		for strat in self.strategies:
			action += strat.get_action(data)
		return action

	def get_action(self, data, shares, cash, short_reserve):
		action = self.strategy(data)
		if action > 0:
			cover_action = 0
			if action * data[-1] > cash:
			    action = cash // data[-1]
			if shares < 0:
			    cover_action = min([action, abs(shares)])
			    action -= cover_action
			return int(action), int(cover_action), 0
		if action < 0:
			cash -= short_reserve
			short_action = 0
			action = abs(action)
			if action > shares:
			    short_action = action - max([shares, 0])
			    action -= short_action
			if (short_action - action) * data[-1] > cash:
			    short_action = (cash + action * data[-1]) // data[-1]
			return -int(action), 0, int(short_action)
		return 0, 0, 0

class OptimisticAverage: # assumes market will continue in the same direction

	def __init__(self, risk=10e6):
		self.risk = risk

	def get_action(self, data):
		risk = self.risk / data[-1]
		return risk * (data[-1] - data[-2]) / data[-2]

class PessimisticAverage: # assumes market is about to change direction

	def __init__(self, look_back=10, risk=10e6, power=2, std_fac=2):
		self.look_back = look_back
		self.risk = risk
		self.power = power
		self.std_fac = std_fac

	def get_action(self, data):
		risk = self.risk / data[-1]
		if len(data) > self.look_back:
			data = data[-self.look_back:]
		std = np.std(data) * self.std_fac
		num = den = 0
		for i in range(len(data)):
			num += (i ** self.power) * data[i]
			den += (i ** self.power)
		avg = (num / den)
		if data[-1] > avg + std or data[-1] < avg - std:
			action = risk * (avg - data[-1]) / avg
		else:
			action = 0
		return action

