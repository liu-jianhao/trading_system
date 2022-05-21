from jqdatasdk import *
import matplotlib.pyplot as plt
import numpy as np
from jqdatasdk.technical_analysis import MA

# 账号是申请时所填写的手机号；密码为聚宽官网登录密码
auth('xxx', 'xxx')


class AStockTrading(object):
    def __init__(self, strategy_name):
        self._strategy_name = strategy_name

        self.st = '600238.XSHG'

        self.current_stock = {}
        self.history_stock = {}
        self.order_number = 0

        # 本金
        self.principal = 100000

    def get_ma_price(self, check_date, timeperiod):
        return MA(self.st, check_date=check_date, timeperiod=timeperiod)[self.st]

    def buy(self, datetime, price, volume):
        self.order_number += 1
        key = "order" + str(self.order_number)
        self.current_stock[key] = {
            "open_datetime": datetime,
            "open_price": price,
            "volume": volume
        }

    def sell(self, datetime, key, price):
        self.current_stock[key]['close_price'] = price
        self.current_stock[key]['close_datetime'] = datetime
        self.current_stock[key]['pnl'] = \
            (price - self.current_stock[key]['open_price']) \
            * self.current_stock[key]['volume']

        self.history_stock[key] = self.current_stock.pop(key)

    def strategy(self, datetime, price, ma20_price):
        if 0 == len(self.current_stock):
            if (price - ma20_price) / price < -0.02:
                volume = int(self.principal / price / 100) * 100
                self.buy(datetime, price, volume)
        elif 1 == len(self.current_stock):
            if price > ma20_price * 1.02:
                key = list(self.current_stock.keys())[0]
                if datetime.date() != self.current_stock[key]['open_datetime'].date():
                    self.sell(datetime, key, price - 0.01)
                    print('open date is %s, close date is: %s.'
                          % (self.history_stock[key]['open_datetime'].date(), datetime.date()))
        else:
            print('sell order aborted due to T+0 limit')

    def run_backtesting(self):
        df = get_price(self.st, start_date='2021-01-01', end_date='2021-12-31',
                       frequency='1d', fields=None, skip_paused=False, fq='pre', panel=True)

        cur_date = None

        # index -> datetime ; row -> open,close,high,low,volume,money
        for index, row in df.iterrows():
            ma20_price = 0
            if cur_date is None or cur_date != index:
                cur_date = index
                ma20_price = self.get_ma_price(index.date(), 20)

            self.strategy(index, row['close'], ma20_price)


if __name__ == '__main__':
    ast = AStockTrading('ma')
    ast.run_backtesting()

    profit_orders = 0
    loss_orders = 0
    orders = ast.history_stock
    x_date = []
    y_price = []

    for key in orders.keys():
        if orders[key]['pnl'] >= 0:
            profit_orders += 1
        else:
            loss_orders += 1
        x_date.append(orders[key]['close_datetime'].date())
        y_price.append(orders[key]['pnl'])

    win_rate = profit_orders / len(orders)
    loss_rate = loss_orders / len(orders)

    x = np.array(x_date)
    y = np.array(y_price)

    fig, ax = plt.subplots()
    ax.plot_date(x, y, "#FF8800", alpha=0.7)

    fig.autofmt_xdate()
    plt.savefig('./pnl.png')
    plt.show()
