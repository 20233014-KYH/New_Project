from datetime import date

from billing.cycle import cycle_days, next_billing_date
from billing.discount import apply_discounts
from billing.invoice import make_invoice, prorate


def test_month_end_clamp_feb():
    assert next_billing_date(date(2026, 1, 31)) == date(2026, 2, 28)


def test_month_end_clamp_leap():
    assert next_billing_date(date(2028, 1, 30)) == date(2028, 2, 29)


def test_month_end_clamp_apr():
    assert next_billing_date(date(2026, 3, 31)) == date(2026, 4, 30)


def test_year_wrap():
    assert next_billing_date(date(2026, 12, 31)) == date(2027, 1, 31)


def test_cycle_days_month_end():
    assert cycle_days(date(2026, 1, 31)) == 28


def test_discount_floor_each_step():
    assert apply_discounts(103, [0.5, 0.5]) == 25


def test_discount_floor_half():
    assert apply_discounts(5, [0.5]) == 2


def test_discount_two_steps_normal():
    assert apply_discounts(10000, [0.15, 0.1]) == 7650


def test_discount_none():
    assert apply_discounts(4900, []) == 4900


def test_invoice_month_end():
    inv = make_invoice("lee", date(2026, 3, 31), 103, [0.5, 0.5])
    assert inv.period_end == date(2026, 4, 30)
    assert inv.amount == 25


def test_prorate_month_end():
    # 1/31 가입, 2/14에 9900→19900 변경: 남은 14일 / 주기 28일
    assert prorate(date(2026, 1, 31), date(2026, 2, 14), 9900, 19900) == 5000


def test_basic_still_ok():
    assert next_billing_date(date(2026, 3, 15)) == date(2026, 4, 15)
    assert apply_discounts(10000, [0.1]) == 9000
