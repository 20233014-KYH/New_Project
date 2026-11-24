"""회비 관리 도우미 함수."""


def total_fee(payments):
    """납부 기록의 금액 합계."""
    return sum(p["amount"] for p in payments)
