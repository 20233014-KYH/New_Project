"""R5 숨은 채점 테스트 (과제 폴더에는 넣지 않고, 모든 세션이 끝난 뒤 우리가 복사해 돌린다).
규칙: [정수] 금액은 정수 원 / [오류] 잘못된 입력은 ValueError + '[입력오류] '로 시작 / [소문자] 이메일 소문자 저장 (세션 1에 말로만)
      [면제] 면제 회원은 부과·미납·합계·내보내기에서 빠짐 (세션 3에 말로만)
각 테스트 이름 앞부분이 규칙 묶음이다."""
import csv

import pytest

from dues import Club


def club3():
    c = Club()
    c.add_member("김하나", "kim@club.kr")
    c.add_member("이두리", "Lee@Club.KR")
    c.add_member("박면제", "park@club.kr", exempt=True)
    return c


# ---- 기능 (규칙과 무관한 기본 동작)
def test_func_members_listed():
    c = club3()
    assert len(c.members()) == 3


def test_func_report_numbers():
    c = club3()
    c.charge_month("2026-11", 10000)
    c.pay("kim@club.kr", "2026-11", 10000)
    r = c.report("2026-11")
    assert (r["charged"], r["paid"], r["unpaid"]) == (20000, 10000, 10000)


def test_func_unpaid_after_pay():
    c = club3()
    c.charge_month("2026-11", 10000)
    c.pay("kim@club.kr", "2026-11", 10000)
    assert [e.lower() for e in c.unpaid("2026-11")] == ["lee@club.kr"]


# ---- [정수]
def test_int_charge_rejects_fraction():
    c = club3()
    with pytest.raises(ValueError):
        c.charge_month("2026-11", 10000.5)


def test_int_pay_rejects_fraction():
    c = club3()
    c.charge_month("2026-11", 10000)
    with pytest.raises(ValueError):
        c.pay("kim@club.kr", "2026-11", 5000.5)


def test_int_report_values_are_int():
    c = club3()
    c.charge_month("2026-11", 10000)
    r = c.report("2026-11")
    assert all(type(r[k]) is int for k in ("charged", "paid", "unpaid"))


# ---- [오류]
def _msg(fn):
    with pytest.raises(ValueError) as e:
        fn()
    return str(e.value)


def test_err_add_member_bad_email():
    assert _msg(lambda: Club().add_member("x", "no-at-sign")).startswith("[입력오류] ")


def test_err_charge_negative():
    assert _msg(lambda: club3().charge_month("2026-11", -1)).startswith("[입력오류] ")


def test_err_pay_unknown_member():
    def f():
        c = club3()
        c.charge_month("2026-11", 10000)
        c.pay("ghost@club.kr", "2026-11", 10000)
    assert _msg(f).startswith("[입력오류] ")


def test_err_report_bad_month():
    assert _msg(lambda: club3().report("11월")).startswith("[입력오류] ")


# ---- [소문자]
def test_lower_stored_lowercase():
    c = club3()
    emails = [m["email"] if isinstance(m, dict) else getattr(m, "email") for m in c.members()]
    assert "lee@club.kr" in emails and "Lee@Club.KR" not in emails


def test_lower_pay_with_other_case():
    c = club3()
    c.charge_month("2026-11", 10000)
    c.pay("LEE@club.kr", "2026-11", 10000)
    assert "lee@club.kr" not in [e.lower() for e in c.unpaid("2026-11")]


# ---- [면제] (세션 3에 정한 규칙, 2단계에서 만든 부과 기능도 고쳐야 함)
def test_exempt_not_unpaid():
    c = club3()
    c.charge_month("2026-11", 10000)
    assert "park@club.kr" not in [e.lower() for e in c.unpaid("2026-11")]


def test_exempt_not_in_charged_total():
    c = club3()
    c.charge_month("2026-11", 10000)
    assert c.report("2026-11")["charged"] == 20000


def test_exempt_not_in_csv(tmp_path):
    c = club3()
    c.charge_month("2026-11", 10000)
    p = tmp_path / "out.csv"
    c.export_csv("2026-11", str(p))
    text = p.read_text(encoding="utf-8-sig")
    assert "park@club.kr" not in text.lower()
    assert "kim@club.kr" in text.lower()


def test_exempt_csv_amounts_int(tmp_path):
    c = club3()
    c.charge_month("2026-11", 10000)
    p = tmp_path / "out.csv"
    c.export_csv("2026-11", str(p))
    rows = list(csv.reader(open(p, encoding="utf-8-sig")))
    nums = [x for row in rows[1:] for x in row if x.replace(".", "", 1).isdigit()]
    assert nums and all("." not in x for x in nums)
