"""할 일 목록을 todo.json 파일에 저장한다. 형식: [{"title": str, "done": bool}, ...]"""
import json
import os

PATH = os.environ.get("TODO_FILE", "todo.json")


def load():
    if not os.path.exists(PATH):
        return []
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)


def save(items):
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
