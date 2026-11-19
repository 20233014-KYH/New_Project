"""할 일 관리 CLI. 사용법: python todo.py add "제목" | list | done <번호> | delete <번호>"""
import sys

from storage import load, save


def add(items, title):
    items.append({"title": title, "done": False})
    return items


def done(items, idx):
    items[idx]["done"] = True
    return items


def delete(items, idx):
    items.pop(idx)
    return items


def render(items):
    lines = []
    for i, it in enumerate(items, 1):
        mark = "x" if it["done"] else " "
        lines.append(f"{i}. [{mark}] {it['title']}")
    return "\n".join(lines) if lines else "(할 일 없음)"


def main(argv):
    items = load()
    if not argv or argv[0] == "list":
        print(render(items))
        return
    cmd = argv[0]
    if cmd == "add":
        save(add(items, " ".join(argv[1:])))
    elif cmd == "done":
        save(done(items, int(argv[1]) - 1))
    elif cmd == "delete":
        save(delete(items, int(argv[1]) - 1))
    else:
        print("알 수 없는 명령:", cmd)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
