"""MiniMax 官方视频生成适配器（首尾帧模式）。

使用环境变量 MINIMAX_API_KEY；不要把密钥写入参数、文件或日志。
MiniMax 官方接口要求首尾帧使用可访问的图片 URL。
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

API_ROOT = "https://api.minimaxi.com/v1"


def request_json(method: str, url: str, payload: dict | None = None) -> dict:
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        raise RuntimeError("缺少 MINIMAX_API_KEY 环境变量")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MiniMax HTTP {error.code}: {body[:500]}") from error


def main() -> int:
    parser = argparse.ArgumentParser(description="调用 MiniMax 官方首尾帧视频接口")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--first-frame-url", required=True)
    parser.add_argument("--last-frame-url")
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="MiniMax-Hailuo-02")
    parser.add_argument("--duration", type=int, default=6)
    parser.add_argument("--resolution", default="1080P")
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    payload = {
        "prompt": args.prompt,
        "first_frame_image": args.first_frame_url,
        "model": args.model,
        "duration": args.duration,
        "resolution": args.resolution,
    }
    if args.last_frame_url:
        payload["last_frame_image"] = args.last_frame_url
    created = request_json("POST", f"{API_ROOT}/video_generation", payload)
    task_id = created.get("task_id")
    if not task_id:
        raise RuntimeError(f"MiniMax 未返回 task_id: {json.dumps(created, ensure_ascii=False)}")
    print(f"任务已提交: {task_id}")

    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        query = urllib.parse.urlencode({"task_id": task_id})
        status = request_json("GET", f"{API_ROOT}/query/video_generation?{query}")
        state = status.get("status")
        print(f"状态: {state}")
        if state == "Success":
            file_id = status.get("file_id")
            if not file_id:
                raise RuntimeError("任务成功但未返回 file_id")
            file_info = request_json("GET", f"{API_ROOT}/files/retrieve?file_id={urllib.parse.quote(str(file_id))}")
            download_url = file_info.get("file", {}).get("download_url") or file_info.get("download_url")
            if not download_url:
                raise RuntimeError(f"未找到视频下载地址: {json.dumps(file_info, ensure_ascii=False)}")
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(download_url, output)
            print(f"视频已保存: {output}")
            return 0
        if state == "Fail":
            raise RuntimeError(f"MiniMax 任务失败: {json.dumps(status, ensure_ascii=False)}")
        time.sleep(args.poll_seconds)
    raise TimeoutError("MiniMax 视频任务轮询超时")


if __name__ == "__main__":
    raise SystemExit(main())
