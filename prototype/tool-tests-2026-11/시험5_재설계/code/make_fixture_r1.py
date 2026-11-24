#!/usr/bin/env python3
"""R1 과제 코드 만들기: 동아리 관리 앱(파이썬, sqlite). 같은 원인(사용자 입력을 SQL 문자열에 그대로 붙임)의 숨은 변종 8곳 + 생김새가 비슷한 안전한 코드 7곳.
알려 주는 것은 auth/login.py의 find_user 하나뿐. 정답표는 TRUTH/DECOYS (채점에만 씀, 과제 폴더에는 안 넣음).
holdout: 규칙이 '새 코드'에서도 잡는지 보는 따로 둔 파일(과제 폴더에는 안 넣음)."""
import os
import sys
import textwrap

TRUTH = {  # 함수 이름: 파일
    "search_members": "clubapp/members/search.py",
    "update_nickname": "clubapp/members/profile.py",
    "monthly_report": "clubapp/fees/report.py",
    "find_payments": "clubapp/fees/payments.py",
    "event_by_title": "clubapp/events/calendar.py",
    "by_member": "clubapp/events/attendance.py",
    "delete_old": "clubapp/admin/maintenance.py",
    "search_notices": "clubapp/notices/board.py",
}
DECOYS = ["get_profile", "sort_report", "by_event", "export_table", "count_members", "list_by_ids", "record_login"]
HOLD_TRUTH = ["hx_find_room", "hx_rename_room", "hx_room_by_owner"]
HOLD_SAFE = ["hx_room_by_id", "hx_rooms_sorted", "hx_rooms_param"]

FILES = {
"clubapp/__init__.py": "",
"clubapp/config.py": '''
DB_PATH = "club.db"
TABLE_MEMBERS = "members"
ALLOWED_TABLES = {"members", "fees", "events", "notices"}
PAGE_SIZE = 20
''',
"clubapp/db.py": '''
"""DB 연결과 실행 도우미. 모든 쿼리는 run()을 거친다."""
import sqlite3
from .config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run(sql, params=()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall()


def run_write(sql, params=()):
    with get_conn() as conn:
        conn.execute(sql, params)
        conn.commit()
''',
"clubapp/sqlutil.py": '''
"""SQL 조각을 만드는 작은 도우미들."""

_SORTABLE = {"name": "name", "joined": "joined_at", "amount": "amount"}


def eq(field, value):
    """field = value 조건 문자열."""
    return f"{field} = '{value}'"


def like(field, term):
    """부분 일치 조건 문자열."""
    return f"{field} LIKE '%{term}%'"


def in_list(field, values):
    """field IN (?, ?, ...) 와 값 목록을 함께 돌려준다."""
    marks = ",".join("?" for _ in values)
    return f"{field} IN ({marks})", list(values)


def order_by(key):
    """정해 둔 열 이름으로만 정렬한다."""
    col = _SORTABLE.get(key, "name")
    return f"ORDER BY {col}"
''',
"clubapp/auth/__init__.py": "",
"clubapp/auth/login.py": '''
import hashlib
from ..db import run, run_write


def find_user(username):
    # 알려진 문제: 사용자 이름을 그대로 붙인다
    return run(f"SELECT * FROM users WHERE username = '{username}'")


def check_password(username, password):
    digest = hashlib.sha256(password.encode()).hexdigest()
    rows = run("SELECT 1 FROM users WHERE username = ? AND pw_hash = ?", (username, digest))
    return bool(rows)


def record_login(username, ip):
    run_write("INSERT INTO login_log(username, ip) VALUES (?, ?)", (username, ip))
''',
"clubapp/members/__init__.py": "",
"clubapp/members/search.py": '''
from ..db import run
from .. import sqlutil
from ..config import PAGE_SIZE


def search_members(name, page=1):
    cond = sqlutil.like("name", name)
    offset = (int(page) - 1) * PAGE_SIZE
    return run(f"SELECT id, name FROM members WHERE {cond} LIMIT {PAGE_SIZE} OFFSET {offset}")


def list_by_ids(ids):
    cond, params = sqlutil.in_list("id", ids)
    return run(f"SELECT id, name FROM members WHERE {cond}", params)
''',
"clubapp/members/profile.py": '''
from ..db import run, run_write
from ..config import TABLE_MEMBERS


def get_profile(member_id):
    mid = int(member_id)
    return run(f"SELECT * FROM members WHERE id = {mid}")


def update_nickname(member_id, nickname):
    query = "UPDATE members SET nickname = '%s' WHERE id = %d" % (nickname, int(member_id))
    run_write(query)


def count_members():
    return run(f"SELECT COUNT(*) FROM {TABLE_MEMBERS}")[0][0]
''',
"clubapp/fees/__init__.py": "",
"clubapp/fees/report.py": '''
from ..db import run
from .. import sqlutil


def monthly_report(month):
    sql = "SELECT member, SUM(amount) FROM fees WHERE month = '" + month + "' GROUP BY member"
    return run(sql)


def sort_report(sort_key):
    return run("SELECT member, amount FROM fees " + sqlutil.order_by(sort_key))
''',
"clubapp/fees/payments.py": '''
from ..db import run, run_write
from .. import sqlutil


def record_payment(email, amount, month):
    run_write("INSERT INTO fees(email, amount, month) VALUES (?, ?, ?)", (email, int(amount), month))


def find_payments(member_email):
    where = sqlutil.eq("email", member_email)
    return run("SELECT * FROM fees WHERE " + where)
''',
"clubapp/events/__init__.py": "",
"clubapp/events/calendar.py": '''
from ..db import run


def events_between(start, end):
    return run("SELECT * FROM events WHERE day BETWEEN ? AND ?", (start, end))


def event_by_title(title):
    return run("SELECT * FROM events WHERE title = '{}'".format(title))
''',
"clubapp/events/attendance.py": '''
from ..db import run


class AttendanceRepo:
    def _q(self, cond):
        return run(f"SELECT * FROM attendance WHERE {cond}")

    def by_member(self, name):
        return self._q(f"member = '{name}'")

    def by_event(self, event_id):
        return self._q(f"event_id = {int(event_id)}")
''',
"clubapp/admin/__init__.py": "",
"clubapp/admin/export.py": '''
import csv
import io
from ..db import run
from ..config import ALLOWED_TABLES


def export_table(table):
    if table not in ALLOWED_TABLES:
        raise ValueError("허용되지 않은 표")
    rows = run(f"SELECT * FROM {table}")
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    return buf.getvalue()
''',
"clubapp/admin/maintenance.py": '''
import logging
from ..db import run_write

log = logging.getLogger(__name__)


def delete_old(days):
    """관리 화면에서 받은 '며칠'보다 오래된 기록을 지운다."""
    log.info(f"delete logs older than '{days}' days")
    run_write(f"DELETE FROM logs WHERE created < date('now', '-{days} days')")
''',
"clubapp/notices/__init__.py": "",
"clubapp/notices/board.py": '''
from ..db import run, run_write


def post_notice(author, title, body):
    run_write("INSERT INTO notices(author, title, body) VALUES (?, ?, ?)", (author, title, body))


def search_notices(filters):
    """filters 예: {"author": "kim", "category": "모임"} (검색 화면의 입력값)"""
    clauses = []
    for key, value in filters.items():
        clauses.append(f"{key} = '{value}'")
    where = " AND ".join(clauses) or "1=1"
    return run("SELECT * FROM notices WHERE " + where)
''',
"clubapp/utils/__init__.py": "",
"clubapp/utils/text.py": '''
def shorten(s, n=40):
    return s if len(s) <= n else s[: n - 1] + "…"


def greeting(name):
    return f"안녕하세요, '{name}' 님"
''',
"clubapp/utils/dates.py": '''
import datetime


def month_key(d=None):
    d = d or datetime.date.today()
    return f"{d.year}-{d.month:02d}"
''',
"clubapp/api/__init__.py": "",
"clubapp/api/routes.py": '''
"""HTTP 요청 값(req.args / req.json)을 각 기능으로 넘긴다. 모든 인자는 사용자가 보낸 값이다."""
from ..auth import login
from ..members import search, profile
from ..fees import report, payments
from ..events import calendar, attendance
from ..admin import export, maintenance
from ..notices import board

ROUTES = {
    "GET /login/user": lambda req: login.find_user(req.args["username"]),
    "GET /members": lambda req: search.search_members(req.args["q"], req.args.get("page", 1)),
    "GET /members/ids": lambda req: search.list_by_ids(req.args.getlist("id")),
    "GET /profile": lambda req: profile.get_profile(req.args["id"]),
    "POST /profile/nickname": lambda req: profile.update_nickname(req.json["id"], req.json["nickname"]),
    "GET /fees/report": lambda req: report.monthly_report(req.args["month"]),
    "GET /fees/sorted": lambda req: report.sort_report(req.args.get("sort", "name")),
    "GET /fees/mine": lambda req: payments.find_payments(req.args["email"]),
    "GET /events/title": lambda req: calendar.event_by_title(req.args["title"]),
    "GET /attendance/member": lambda req: attendance.AttendanceRepo().by_member(req.args["name"]),
    "GET /attendance/event": lambda req: attendance.AttendanceRepo().by_event(req.args["event"]),
    "GET /admin/export": lambda req: export.export_table(req.args["table"]),
    "POST /admin/cleanup": lambda req: maintenance.delete_old(req.json["days"]),
    "GET /notices": lambda req: board.search_notices(dict(req.args)),
}
''',
"README.md": "# 동아리 관리 앱\n\n회원·회비·행사·공지 관리. `clubapp/api/routes.py`가 요청을 각 기능으로 넘긴다.\n",
}

HOLDOUT = '''
from clubapp.db import run, run_write
from clubapp import sqlutil

_ROOM_SORT = {"name": "name", "size": "capacity"}


def hx_find_room(name):
    return run(f"SELECT * FROM rooms WHERE name = '{name}'")


def hx_rename_room(room_id, new_name):
    run_write("UPDATE rooms SET name = '%s' WHERE id = %d" % (new_name, int(room_id)))


def hx_room_by_owner(owner):
    return run("SELECT * FROM rooms WHERE " + sqlutil.eq("owner", owner))


def hx_room_by_id(room_id):
    return run(f"SELECT * FROM rooms WHERE id = {int(room_id)}")


def hx_rooms_sorted(key):
    return run("SELECT * FROM rooms ORDER BY " + _ROOM_SORT.get(key, "name"))


def hx_rooms_param(owner):
    return run("SELECT * FROM rooms WHERE owner = ?", (owner,))
'''


def write(root):
    for rel, body in FILES.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p) or root, exist_ok=True)
        open(p, "w", encoding="utf-8").write(textwrap.dedent(body).lstrip("\n"))


def write_holdout(root):
    os.makedirs(root, exist_ok=True)
    open(os.path.join(root, "extra.py"), "w", encoding="utf-8").write(HOLDOUT.lstrip("\n"))


if __name__ == "__main__":
    write(sys.argv[1])
