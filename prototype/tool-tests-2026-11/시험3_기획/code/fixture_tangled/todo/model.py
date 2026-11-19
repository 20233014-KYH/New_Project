import uuid
from datetime import date


def add_item(data, title):
    item = {"id": uuid.uuid4().hex[:6], "title": title, "done": False, "created": date.today().isoformat()}
    data["items"].append(item)
    return item


def find(data, item_id):
    for it in data["items"]:
        if it["id"] == item_id:
            return it
    raise KeyError(item_id)


def complete(data, item_id):
    find(data, item_id)["done"] = True


def delete(data, item_id):
    data["items"] = [it for it in data["items"] if it["id"] != item_id]
