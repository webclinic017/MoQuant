from decimal import Decimal


class SimDividend(object):
    ts_code: str
    dividend_num: Decimal
    dividend_cash: Decimal
    pay_date: str
    div_listdate: str

    def __init__(self, ts_code, dividend_num, dividend_cash, pay_date, div_listdate):
        self.ts_code = ts_code
        self.dividend_num = dividend_num
        self.dividend_cash = dividend_cash
        self.pay_date = pay_date
        self.div_listdate = div_listdate

    def finish(self, dt: str) -> bool:
        if self.pay_date is not None and self.pay_date > dt:
            return False
        if self.div_listdate is not None and self.div_listdate > dt:
            return False
        return True
