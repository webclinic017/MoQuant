from moquant.utils.datetime import format_delta


def get_index_by_ann_date(arr, current_date: str) -> int:
    ann_date_to_find = format_delta(current_date, 1)
    i = -1
    while i + 1 < len(arr):
        if arr[i + 1].ann_date > ann_date_to_find:
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
