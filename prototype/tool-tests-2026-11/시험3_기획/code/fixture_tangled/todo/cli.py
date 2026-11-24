"""명령줄: python -m todo.cli add "제목" | list | done <id> | delete <id>"""
import argparse

from todo import model, storage


def format_item(it):
    mark = "x" if it["done"] else " "
    return f"[{mark}] {it['id']}  {it['title']}  (등록 {it['created']})"


def main(argv=None):
    p = argparse.ArgumentParser(prog="todo")
    sub = p.add_subparsers(dest="cmd")
    a = sub.add_parser("add")
    a.add_argument("title", nargs="+")
    sub.add_parser("list")
    d = sub.add_parser("done")
    d.add_argument("id")
    r = sub.add_parser("delete")
    r.add_argument("id")
    args = p.parse_args(argv)

    data = storage.load()
    if args.cmd == "add":
        model.add_item(data, " ".join(args.title))
    elif args.cmd == "done":
        model.complete(data, args.id)
    elif args.cmd == "delete":
        model.delete(data, args.id)
    else:
        for it in data["items"]:
            print(format_item(it))
        return
    storage.save(data)


if __name__ == "__main__":
    main()
