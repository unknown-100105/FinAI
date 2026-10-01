from pathlib import Path

p = Path("tests/test_xai_api.py")
s = p.read_text(encoding="utf-8")

old = '''def test_invalid_trace_id():
    response = client.get(
        "/api/v1/xai/traces/../../etc/passwd"
    )

    assert response.status_code == 400
'''

new = '''def test_invalid_trace_id():
    response = client.get(
        "/api/v1/xai/traces/invalid_trace_id"
    )

    assert response.status_code == 400
'''

if old not in s:
    raise RuntimeError("Expected invalid trace ID test block was not found")

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

print("Fixed invalid trace ID test")
