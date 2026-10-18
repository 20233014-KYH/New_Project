import json, os
D = os.path.dirname(os.path.abspath(__file__))
tr = os.path.join(D, "transcript.jsonl")
with open(tr, "w", encoding="utf-8") as f:
    f.write(json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}}) + "\n")
desk = os.path.dirname(D)
data = {
    "hook_event_name": "Status", "session_id": "test-sl-0001", "transcript_path": tr, "cwd": desk,
    "model": {"id": "claude-sonnet-5-5", "display_name": "Sonnet 5.5"},
    "workspace": {"current_dir": desk, "project_dir": desk}, "version": "2.1.191",
    "output_style": {"name": "default"},
    "cost": {"total_cost_usd": 0.01, "total_duration_ms": 10000, "total_api_duration_ms": 5000,
             "total_lines_added": 3, "total_lines_removed": 1},
    "context_window": {"total_input_tokens": 24000, "total_output_tokens": 500, "context_window_size": 200000,
                       "used_percentage": 12, "remaining_percentage": 88,
                       "current_usage": {"input_tokens": 24000, "output_tokens": 500,
                                         "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}},
}
with open(os.path.join(D, "stdin.json"), "w", encoding="utf-8") as f:
    json.dump(data, f)
print("ok")
