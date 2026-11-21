from todo.storage import migrate


def test_migrate_v1_list():
    data = migrate([{"title": "장보기", "done": False}])
    assert data["version"] == 2
    assert data["items"][0]["id"]
    assert data["items"][0]["created"]


def test_v2_unchanged():
    d = {"version": 2, "items": [{"id": "a1", "title": "x", "done": True, "created": "2026-01-01"}]}
    assert migrate(d) == d
