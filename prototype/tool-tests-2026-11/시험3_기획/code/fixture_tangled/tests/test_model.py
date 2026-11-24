from todo import model


def test_add_complete_delete():
    data = {"version": 2, "items": []}
    it = model.add_item(data, "장보기")
    model.complete(data, it["id"])
    assert data["items"][0]["done"]
    model.delete(data, it["id"])
    assert data["items"] == []
