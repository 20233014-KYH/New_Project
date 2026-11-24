"""동아리 회원 관리 작은 서버. python app.py → http://localhost:8080"""
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB = "members.db"


def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    return conn


def list_members():
    with get_conn() as conn:
        return conn.execute("SELECT id, name, email FROM members").fetchall()


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(str(body).encode("utf-8"))

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/members":
            return self._send(list_members())
        self._send("not found", 404)


if __name__ == "__main__":
    HTTPServer(("localhost", 8080), Handler).serve_forever()
