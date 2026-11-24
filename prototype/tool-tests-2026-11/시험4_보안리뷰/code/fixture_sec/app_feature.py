"""동아리 회원 관리 작은 서버. python app.py → http://localhost:8080"""
import os
import sqlite3
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB = "members.db"
UPLOADS = "uploads"


def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    return conn


def list_members():
    with get_conn() as conn:
        return conn.execute("SELECT id, name, email FROM members").fetchall()


def find_member(name):
    with get_conn() as conn:
        query = "SELECT id, name, email FROM members WHERE name = '" + name + "'"
        return conn.execute(query).fetchall()


def search_by_email(email):
    with get_conn() as conn:
        return conn.execute("SELECT id, name, email FROM members WHERE email = ?", (email,)).fetchall()


def export_report(filename):
    subprocess.run("zip report.zip " + filename, shell=True, check=False)
    return "report.zip"


def read_attachment(path):
    with open(os.path.join(UPLOADS, path), encoding="utf-8") as f:
        return f.read()


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(str(body).encode("utf-8"))

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path == "/members":
            return self._send(list_members())
        if url.path == "/members/find":
            return self._send(find_member(q.get("name", "")))
        if url.path == "/members/search":
            return self._send(search_by_email(q.get("email", "")))
        if url.path == "/report":
            return self._send(export_report(q.get("file", "members.csv")))
        if url.path == "/attachment":
            return self._send(read_attachment(q.get("path", "")))
        self._send("not found", 404)


if __name__ == "__main__":
    HTTPServer(("localhost", 8080), Handler).serve_forever()
