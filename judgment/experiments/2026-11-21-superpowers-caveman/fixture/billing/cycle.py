import calendar
from datetime import date, timedelta


def add_months(start: date, months: int) -> tuple[int, int]:
    m = start.month - 1 + months
    return start.year + m // 12, m % 12 + 1


def next_billing_date(start: date, months: int = 1) -> date:
    """가입일 기준 months달 뒤 청구일."""
    y, m = add_months(start, months)
    last = calendar.monthrange(y, m)[1]
    if start.day > last:
        # 날짜가 넘치면 넘친 만큼 다음 날로 보낸다
        return date(y, m, last) + timedelta(days=start.day - last)
    return date(y, m, start.day)


def cycle_days(start: date) -> int:
    """이번 청구 주기의 일수(이번 청구일 ~ 다음 청구일)."""
    return (next_billing_date(start) - start).days
