from datetime import date

from billing.cycle import next_billing_date
from billing.discount import apply_discounts
from billing.invoice import make_invoice


def test_next_billing_normal_day():
    assert next_billing_date(date(2026, 3, 15)) == date(2026, 4, 15)


def test_discount_single():
    assert apply_discounts(10000, [0.1]) == 9000


def test_invoice_basic():
    inv = make_invoice("kim", date(2026, 5, 10), 9900)
    assert inv.period_end == date(2026, 6, 10)
    assert inv.amount == 9900
