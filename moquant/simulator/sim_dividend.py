from decimal import Decimal


class SimDividend(object):
    ts_code: str
    dividend_num: Decimal
    dividend_cash: Decimal
    pay_date: str
    div_listdate: str

    def __init__(self, ts_code, num, dividend_num, dividend_cash, pay_date, div_listdate):
        self.ts_code = ts_code
        self.num = num
        self.dividend_num = dividend_num
        self.dividend_cash = dividend_cash
        self.pay_date = pay_date
        self.div_listdate = div_listdate
