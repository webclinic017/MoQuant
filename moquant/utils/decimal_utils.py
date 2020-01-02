from decimal import Decimal


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


def div(a, b):
    if a is None or b is None or b == 0:
        return 0
    return a / b


def yoy(current, last_year):
    if current is None or last_year is None or last_year == 0:
        return None
    else:
        return (current - last_year) / abs(last_year)
