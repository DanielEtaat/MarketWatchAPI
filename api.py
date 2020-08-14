import requests
import shlex
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


class MarketWatchGame:

	def __init__(self, username, password, game):
		self.username = username
		self.password = password
		self.game = game
		self.token = get_token(username, password)

	@property
	def portfolio(self):
		session = requests.Session()
		headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36'}
		portfolio_url = 'https://www.marketwatch.com/game/{}/portfolio'.format(self.game)
		portfolio = session.get(portfolio_url, cookies=self.token, headers=headers)
		return portfolio

	@property
	def portfolio_summary(self):
		port_list = BeautifulSoup(self.portfolio.text, features='lxml').find_all('li', attrs={'class': 'kv__item'})
		port_summ = {}
		for p in port_list:
			key = p.find('span', attrs={'class': 'text'}).text.lower()
			port_summ[key] = p.find('span', attrs={'class': 'kv__primary'}).text.lower()
		return port_summ

	@property
	def portfolio_holdings(self):
		holdings_data = []
		portfolio_text = self.portfolio.text
		have_holdings = BeautifulSoup(portfolio_text, features="lxml").find_all("h5", attrs={'class': 'primary'}, text="You currently have no holdings")
		if len(have_holdings) > 0:
			return holdings_data
		holdings_data.append(['symbol', 'shares', 'type'])
		holdings_table = BeautifulSoup(portfolio_text, features='lxml').find('table', attrs={'class', 'holdings'}).find_all('td', attrs={'class': 'align--left'})
		for stock in holdings_table:
			stock_name = stock.find('a').text.strip()
			shares = int(stock.find('small').text.split(" ")[0].replace(",", ""))
			order = stock.find('span', attrs={"class": "m-show"}).text[2:]
			holdings_data.append([stock_name, shares, order])
		return holdings_data

	def get_shares(self, symbol, p):
		shares = 0
		if len(p) < 2:
			return shares
		try:
			index_symbol = p[0].index('symbol')
			index_shares = p[0].index('shares')
			index_type = p[0].index('type')
		except:
			return shares
		for row in p[1:]:
			if row[index_symbol] == symbol:
				if row[index_type] == "Buy":
					shares += int(row[index_shares])
				elif row[index_type] == "Short":
					shares -= int(row[index_shares])
		return int(shares)

	def get_buy_shares(self, symbol, p):
		shares = 0
		if len(p) < 2:
			return shares
		try:
			index_symbol = p[0].index('symbol')
			index_shares = p[0].index('shares')
			index_type = p[0].index('type')
		except:
			return shares
		for row in p[1:]:
			if row[index_symbol] == symbol:
				if row[index_type] == "Buy":
					shares += int(row[index_shares])
		return int(shares)

	def get_short_shares(self, symbol, p):
		shares = 0
		if len(p) < 2:
			return shares
		try:
			index_symbol = p[0].index('symbol')
			index_shares = p[0].index('shares')
			index_type = p[0].index('type')
		except:
			return shares
		for row in p[1:]:
			if row[index_symbol] == symbol:
				if row[index_type] == "Short":
					shares += int(row[index_shares])
		return int(shares)

	def place_order(self, symbol, exchange, shares, order_type="BUY", session=requests.Session()):
		order_type = order_type.capitalize()
		order_url = 'https://www.marketwatch.com/game/{}/trade/submitorder'.format(self.game)
		order_data = {
			'Fuid': 'STOCK-{}-{}'.format(exchange, symbol),
			'Shares': str(shares),
			'Type': order_type
		}
		order_data = '[' + str(order_data) + ']'
		headers = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json', 'charset': 'UTF-8'}
		resp = session.post(order_url, data=order_data, headers=headers, cookies=self.token).json()
		return resp

def get_token(username, password, session=requests.Session()):
	headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36'}
	sign_page = session.get('http://www.marketwatch.com/user/login/status', headers=headers)
	params = parse_qs(urlparse(sign_page.url).query)
	form_data = {
		'username': username,
		'password': password,
		'state': params['state'],
		'client_id': params['client'],
		'clientID': params['client'],
		'protocol': params['protocol'],
		'scope': params['scope'],
		'response_type': params['response_type'],
		'type': params['response_type'],
		'redirect_uri': params['redirect_uri'],
		'redirectURI': params['redirect_uri'],
		'nonce': params['nonce'],
		'ui_locales': params['ui_locales'],
		'ns': params['ns'],
		'savelogin': params['savelogin'],
		'connection': 'DJldap',
		'tenant': 'sso',
		'sso': 'tru',
		'_intstate': 'deprecated',
		'_csrf': session.cookies['_csrf'],
	}
	hidden_form = session.post('https://sso.accounts.dowjones.com/usernamepassword/login', data=form_data, headers=headers)
	hidden_form = BeautifulSoup(hidden_form.content, features='lxml')
	hidden_form_parsed = hidden_form.find_all('input', attrs={'type': 'hidden'})
	hidden_form_data = {}
	for inp in hidden_form_parsed:
		hidden_form_data[inp['name']] = inp['value']
	session.post('https://sso.accounts.dowjones.com/login/callback', data=hidden_form_data, headers=headers)
	if session.get('http://www.marketwatch.com/user/login/status', headers=headers).url == 'https://www.marketwatch.com/my':
		print('Login Succesful.')
	else:
		print('Login Failure.')
	return session.cookies



