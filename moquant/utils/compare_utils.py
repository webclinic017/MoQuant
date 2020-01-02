def maxi(*args):
    result = None
    for arg in args:
        if arg is None:
            continue
        elif result is None:
            result = arg
        else:
            result = max(result, arg)
    return result


def mini(*args):
    result = None
    for arg in args:
        if arg is None:
            continue
        elif result is None:
            result = arg
        else:
            result = min(result, arg)
    return result
