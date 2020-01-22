def get_index_by_end_date(arr, current_date: str, from_index: int = 0) -> int:
    i = from_index
    while i + 1 < len(arr):
        if arr[i + 1].end_date > current_date:
            break
        else:
            i += 1
    return i


def same_period(arr, i: int, period: str) -> bool:
    return 0 <= i < len(arr) and arr[i].end_date == period
