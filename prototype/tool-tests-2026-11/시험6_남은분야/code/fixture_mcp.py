#!/usr/bin/env python3
"""시험 6-4c용 아주 작은 MCP 서버(표준 라이브러리만). 도구 하나가 데이터 파일 내용을 통째로 돌려준다.
사용: python fixture_mcp.py <도구이름> <설명> <데이터 파일 경로>
(사내 시스템 MCP가 큰 JSON·로그를 돌려주는 상황을 흉내 냄. 모델은 이 도구로만 데이터를 볼 수 있음)
"""
import json
import sys

NAME, DESC, PATH = sys.argv[1], sys.argv[2], sys.argv[3]


def reply(i, result):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": i, "result": result}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except Exception:
        continue
    m, i = msg.get("method"), msg.get("id")
    if i is None:
        continue  # 알림(notifications/initialized 등)은 답하지 않음
    if m == "initialize":
        reply(i, {"protocolVersion": (msg.get("params") or {}).get("protocolVersion", "2025-06-18"),
                  "capabilities": {"tools": {}}, "serverInfo": {"name": "fixture", "version": "1.0"}})
    elif m == "tools/list":
        reply(i, {"tools": [{"name": NAME, "description": DESC, "inputSchema": {"type": "object", "properties": {}}}]})
    elif m == "tools/call":
        text = open(PATH, encoding="utf-8").read()
        reply(i, {"content": [{"type": "text", "text": text}]})
    elif m == "ping":
        reply(i, {})
    else:
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": "unknown method"}}) + "\n")
        sys.stdout.flush()
