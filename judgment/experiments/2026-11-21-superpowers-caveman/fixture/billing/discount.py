def apply_discounts(price: int, rates: list[float]) -> int:
    """쿠폰 할인율 목록을 차례로 적용한 최종 금액(원)."""
    total = float(price)
    for r in rates:
        if not 0 <= r < 1:
            raise ValueError(f"할인율이 이상해요: {r}")
        total = total * (1 - r)
    return round(total)
