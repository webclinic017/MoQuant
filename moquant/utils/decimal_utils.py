import math
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
        return Decimal(err_default) if err_default is not None else None
    if not isinstance(a, Decimal):
        a = Decimal(a)
    if not isinstance(b, Decimal):
        b = Decimal(b)
    return a * b


def div(a, b, err_default=0):
    if a is None or b is None or b == 0:
        return Decimal(err_default) if err_default is not None else None
    if not isinstance(a, Decimal):
        a = Decimal(a)
    if not isinstance(b, Decimal):
        b = Decimal(b)
    return a / b


def yoy(current, last_year, err_default=None):
    if current is None or last_year is None or last_year == 0:
        return Decimal(err_default) if err_default is not None else None
    else:
        return (current - last_year) / abs(last_year)


def valid_score(score, s=0, e=100):
    return mini(maxi(score, s), e)


def avg_in_exists(*args):
    total = Decimal(0)
    count = Decimal(0)
    for num in args:
        if num is None:
            continue
        if isinstance(num, Decimal):
            total += num
        else:
            total += Decimal(num)
        count += 1
    return div(total, count)


def cut_format(num: Decimal):
    if num is None:
        return '0'
    elif not isinstance(num, Decimal):
        num = Decimal(num)
    if num >= 100:
        return num.quantize(Decimal('0.0'))
    else:
        return num.quantize(Decimal('0.00'))


def unit_format(num):
    if num is None:
        return '0'
    elif not isinstance(num, Decimal):
        num = Decimal(num)
    abs_val = num.copy_abs()
    if abs_val >= pow(10, 8):
        return '%s亿' % cut_format(div(num, pow(10, 8)))
    elif abs_val >= pow(10, 4):
        return '%s万' % cut_format(div(num, pow(10, 4)))
    else:
        return '%s' % cut_format(num)


def percent_format(num):
    if num is None:
        num = 0
    if not isinstance(num, Decimal):
        num = Decimal(num)
    return '%s%%' % cut_format(num * 100)


def noneToZero(num):
    if num is None or math.isnan(num):
        return 0
    else:
        return num