"""시험 채점용 아주 작은 MCP 클라이언트(stdio). dbhub 같은 서버를 띄워 tools/list·tools/call을 부른다."""
import json
import subprocess


class Client:
    def __init__(self, cmd, cwd=None, env=None):
        self.p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, encoding="utf-8", errors="replace")
        self.i = 0
        self.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "grader", "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.p.stdin.flush()

    def call(self, method, params=None):
        self.i += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.i, "method": method, "params": params or {}}) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("서버가 끝남: " + self.p.stderr.read()[-500:])
            try:
                msg = json.loads(line)
            except Exception:
                continue
            if msg.get("id") == self.i:
                return msg

    def close(self):
        try:
            self.p.kill()
        except Exception:
            pass
