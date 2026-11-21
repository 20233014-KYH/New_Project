"""회비 관리 도우미 함수."""


def total_fee(payments):
    """납부 기록의 금액 합계."""
    return sum(p["amount"] for p in payments)


def average_fee(payments):
    """납부 기록의 평균 금액. 기록이 없으면 0을 돌려준다."""
    return sum(p["amount"] for p in payments) / len(payments)


def paginate(items, page, size=10):
    """목록을 페이지로 나눈다. page는 1부터 시작한다(1 = 첫 페이지)."""
    start = page * size
    return items[start:start + size]


def dedupe_members(members):
    """같은 사람이 두 번 들어간 회원 목록에서 중복을 지운다. 같은 사람인지는 이메일로 판단한다."""
    seen, out = set(), []
    for m in members:
        if m["name"] in seen:
            continue
        seen.add(m["name"])
        out.append(m)
    return out


def unpaid_members(members, payments):
    """납부 기록이 없는 회원 목록."""
    paid = {p["member_email"] for p in payments}
    return [m for m in members if m["email"] not in paid]
