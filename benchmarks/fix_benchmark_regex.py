from pathlib import Path

p = Path("benchmarks/rllm_finqa_controlled_benchmark.py")
s = p.read_text(encoding="utf-8")

old = r'''    numeric_candidates = re.findall(
        r"(?<![\\d.])\\d+(?:\\.\\d+)?",
        response_normalized,
    )
'''

new = r'''    numeric_candidates = re.findall(
        r"(?<![\d.])\d+(?:\.\d+)?",
        response_normalized,
    )
'''

if old not in s:
    raise RuntimeError("Broken regex block not found")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("FIXED: numeric semantic evaluator regex")
