"""할 일 저장. 파일 형식(버전 2): {"version": 2, "items": [{"id": str, "title": str, "done": bool, "created": "YYYY-MM-DD"}]}

버전 1은 항목 리스트만 저장했다. 읽을 때 migrate()로 버전 2로 바꾼다.
"""
import json
import os
import uuid
from datetime import date

PATH = os.environ.get("TODO_FILE", "todo.json")
VERSION = 2


def migrate(data):
    if isinstance(data, list):  # 버전 1
        data = {"version": 1, "items": data}
    if data.get("version") == 1:
        for it in data["items"]:
            it.setdefault("id", uuid.uuid4().hex[:6])
            it.setdefault("created", date.today().isoformat())
        data["version"] = 2
    return data


def load():
    if not os.path.exists(PATH):
        return {"version": VERSION, "items": []}
    with open(PATH, encoding="utf-8") as f:
        return migrate(json.load(f))


def save(data):
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
