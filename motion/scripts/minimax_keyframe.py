from __future__ import annotations

import argparse
import base64
import json
import os
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-url", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        raise RuntimeError("缺少 MINIMAX_API_KEY")
    payload = {
        "model": "image-01",
        "prompt": args.prompt,
        "aspect_ratio": "1:1",
        "response_format": "base64",
        "n": 1,
        "subject_reference": [{"type": "character", "image_file": args.reference_url}],
    }
    request = urllib.request.Request(
        "https://api.minimaxi.com/v1/image_generation",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MiniMax HTTP {error.code}: {body[:500]}") from error
    encoded = result.get("data", {}).get("image_base64", [])
    if not encoded:
        raise RuntimeError(f"未返回图片: {json.dumps(result, ensure_ascii=False)[:500]}")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode(encoded[0]))
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
