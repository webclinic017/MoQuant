def get_index_by_end_date(arr, current_date: str, from_index: int = -1) -> int:
    i = from_index
    while i + 1 < len(arr):
        if arr[i + 1].end_date > current_date:
            break
        else:
            i += 1
    return i


def get_next_index(arr, date_field: str, pos: str) -> int:
    if pos == len(arr):
        return None
    result = pos + 1
    while result < len(arr) and getattr(arr[result], date_field) < getattr(arr[pos], date_field):
        result += 1
    if result >= len(arr):
        return None
    else:
        return result


def can_use_next_date(arr: list, date_field: str, next_pos: int, current_date: str) -> bool:
    if next_pos is None:
        return False
    else:
        return getattr(arr[next_pos], date_field) <= current_date


def cal_season_value(current, last, period):
    month = int(period[4:6])
    if month == 3:
        return current
    elif current is not None and last is not None:
        return current - last
    return None