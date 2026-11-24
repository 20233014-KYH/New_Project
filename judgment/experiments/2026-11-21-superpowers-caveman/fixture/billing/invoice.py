from dataclasses import dataclass
from datetime import date

from .cycle import cycle_days, next_billing_date
from .discount import apply_discounts


@dataclass
class Invoice:
    customer: str
    period_start: date
    period_end: date
    amount: int


def make_invoice(customer: str, start: date, price: int, coupons: list[float] | None = None) -> Invoice:
    return Invoice(customer, start, next_billing_date(start), apply_discounts(price, coupons or []))


def prorate(start: date, change_day: date, old_price: int, new_price: int) -> int:
    """플랜을 change_day에 바꿨을 때 남은 기간 차액."""
    total = cycle_days(start)
    left = (next_billing_date(start) - change_day).days
    return (new_price - old_price) * left // total
