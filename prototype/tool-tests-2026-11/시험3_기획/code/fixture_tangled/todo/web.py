"""작은 웹 화면: python -m todo.web  →  http://localhost:8000 (목록), /api/items (JSON), POST /api/items (추가)"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from todo import model, storage


def row_html(it):
    # cli.format_item과 같은 정보를 HTML로 보여 준다
    mark = "✔" if it["done"] else ""
    return f"<tr><td>{mark}</td><td>{it['id']}</td><td>{it['title']}</td><td>{it['created']}</td></tr>"


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self):
        data = storage.load()
        if self.path == "/api/items":
            self._send(200, json.dumps(data["items"], ensure_ascii=False), "application/json")
        else:
            rows = "".join(row_html(it) for it in data["items"])
            self._send(200, f"<table>{rows}</table>", "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/items":
            return self._send(404, "not found", "text/plain")
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        data = storage.load()
        item = model.add_item(data, body["title"])
        storage.save(data)
        self._send(201, json.dumps(item, ensure_ascii=False), "application/json")


if __name__ == "__main__":
    HTTPServer(("localhost", 8000), Handler).serve_forever()
