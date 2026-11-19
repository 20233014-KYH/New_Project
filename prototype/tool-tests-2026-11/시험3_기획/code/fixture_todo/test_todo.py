from todo import add, delete, done, render


def test_add_and_render():
    items = add([], "장보기")
    assert render(items) == "1. [ ] 장보기"


def test_done():
    items = done(add([], "장보기"), 0)
    assert render(items) == "1. [x] 장보기"


def test_delete():
    items = delete(add(add([], "a"), "b"), 0)
    assert render(items) == "1. [ ] b"


def test_empty():
    assert render([]) == "(할 일 없음)"
