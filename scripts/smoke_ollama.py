"""Check an Ollama installation and optional model generation."""
from __future__ import annotations

import argparse
import json
import os
import sys

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true", help="Run a small local chat request")
    args = parser.parse_args()

    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "").strip()
    if not model:
        print("OLLAMA_MODEL is empty. Set it to an installed model tag, e.g. qwen3:4b.", file=sys.stderr)
        return 2

    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code >= 400:
            raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text[:300]}")
        data = response.json()
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        print(f"Cannot reach Ollama at {base_url}: {exc}", file=sys.stderr)
        return 2

    available = {
        str(item.get("name", "")).strip()
        for item in data.get("models", [])
        if isinstance(item, dict)
    }
    if model not in available:
        print(f"Model '{model}' is not in Ollama's local tag list.", file=sys.stderr)
        print("Available models:", ", ".join(sorted(available)) or "(none)", file=sys.stderr)
        print(f"Pull it first with: ollama pull {model}", file=sys.stderr)
        return 2

    print(json.dumps({"status": "OLLAMA_READY", "base_url": base_url, "model": model}, indent=2))
    if not args.generate:
        return 0

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": "Answer concisely. Do not provide financial advice."},
                    {"role": "user", "content": "Reply with the words: FinAI local model ready."},
                ],
                "options": {"num_predict": 40},
            },
            timeout=90,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text[:300]}")
        message = response.json().get("message", {}).get("content", "")
        if not isinstance(message, str) or not message.strip():
            raise RuntimeError("Ollama returned no text content.")
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        print(f"Ollama generation smoke test failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"status": "OLLAMA_GENERATION_READY", "response": message.strip()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
