from report import sales_report, refund_report

ROWS = [
    {"type": "sale", "name": "book", "amount": 12.5},
    {"type": "refund", "name": "pen", "amount": 3},
    {"type": "sale", "name": "bag", "amount": 20},
]


def test_sales():
    assert sales_report(ROWS) == "SALES\n-----\nbook: 12.50\nbag: 20.00\nTOTAL: 32.50"


def test_refunds():
    assert refund_report(ROWS) == "REFUNDS\n-------\npen: 3.00\nTOTAL: 3.00"


def test_empty():
    assert sales_report([]) == "SALES\n-----\nTOTAL: 0.00"
