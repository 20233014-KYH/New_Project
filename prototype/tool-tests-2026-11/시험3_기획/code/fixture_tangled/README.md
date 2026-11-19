# todo

할 일 관리. 명령줄과 작은 웹 화면 두 가지로 쓸 수 있어요.

```
python -m todo.cli add "장보기"
python -m todo.cli list
python -m todo.web        # http://localhost:8000
```

- 데이터: `todo.json` (형식은 `todo/storage.py` 맨 위 설명)
- 시험: `python -m pytest`
