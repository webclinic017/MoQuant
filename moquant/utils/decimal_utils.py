from decimal import Decimal

from moquant.utils.compare_utils import mini, maxi


def add(*args):
    result = Decimal(0)
    for num in args:
        if num is None:
            continue
        if isinstance(num, Decimal):
            result += num
        else:
            result += Decimal(num)
    return result


def sub(a, *args):
    result = add(a)
    for num in args:
        if num is None:
            continue
        if isinstance(num, Decimal):
            result -= num
        else:
            result -= Decimal(num)
    return result


def mul(a, b, err_default=0):
    if a is None or b is None:
        return err_default
    if not isinstance(a, Decimal):
        a = Decimal(a)
    if not isinstance(b, Decimal):
        b = Decimal(b)
    return a * b


def div(a, b, err_default=0):
    if a is None or b is None or b == 0:
        return Decimal(err_default)
    if not isinstance(a, Decimal):
        a = Decimal(a)
    if not isinstance(b, Decimal):
        b = Decimal(b)
    return a / b


def yoy(current, last_year):
    if current is None or last_year is None or last_year == 0:
        return None
    else:
        return (current - last_year) / abs(last_year)


def valid_score(score, s=0, e=100):
    return mini(maxi(score, s), e)
