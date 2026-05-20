"""
弗洛伊德恋母情结分析网站 — 后端
启动: python main.py
"""

import time
import os
import sys
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory

# ============================================================
# 配置 — 通过环境变量设置，启动时务必提供 API_KEY
# ============================================================
API_KEY = os.environ.get("API_KEY", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-flash")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.deepseek.com/anthropic")
# ============================================================

SYSTEM_PROMPT = (
    "你是弗洛伊德，针对我输入的文字，无论我说的是什么，"
    "你必须围绕我说的话进行简短的逻辑链分析（一定不能多于150个字）必须，分析的起始必须是我说的话里的一些词，"
    "经过两三段逻辑链的分析，最后必须推出'你有恋母情结'的结论，也就是最后一句话必须是'你有恋母情结'这几个字。"
    "现在请你做出分析。"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# ----- 速率限制 -----
RATE_LIMIT_MAX = 10   # 每分钟最多请求数
RATE_LIMIT_WINDOW = 60
_rate_store = defaultdict(list)  # {ip: [timestamp, ...]}


def _clean_old(now: float) -> None:
    """清理所有 IP 的过期记录，每次有请求到来时顺便做。"""
    for ip in list(_rate_store.keys()):
        _rate_store[ip] = [t for t in _rate_store[ip] if now - t < RATE_LIMIT_WINDOW]
        if not _rate_store[ip]:
            del _rate_store[ip]


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    _clean_old(now)
    if len(_rate_store[ip]) >= RATE_LIMIT_MAX:
        return True
    _rate_store[ip].append(now)
    return False


# ----- 路由 -----

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename: str):
    return send_from_directory(BASE_DIR, filename)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    # 速率检查
    ip = request.remote_addr or "unknown"
    if is_rate_limited(ip):
        return jsonify({"error": "请求过于频繁，请稍后再试。"}), 429

    body = request.get_json(silent=True)
    if not body or not body.get("text", "").strip():
        return jsonify({"error": "请提供 text 字段。"}), 400

    user_text = body["text"].strip()

    # 检查配置
    if not API_KEY or not MODEL_NAME:
        return jsonify({"response": "我现在要休息了"})

    import requests as req
    import traceback

    try:
        print(f"[INFO] 开始调用 API, user_text 长度: {len(user_text)}")
        resp = req.post(
            f"{API_BASE_URL}/messages",
            headers={
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "max_tokens": 1024,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {"role": "user", "content": user_text},
                ],
                "temperature": 0.9,
            },
            timeout=60,
        )
        print(f"[INFO] API 响应状态码: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()

        # Anthropic 响应格式: content 是数组, 取 type="text" 的那条
        ai_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                ai_text = block.get("text", "")
                break

        if not ai_text:
            print("[WARN] API 返回了空内容")
            ai_text = "我现在要休息了"

        print(f"[INFO] 成功获取 AI 回复, 长度: {len(ai_text)}")
        return jsonify({"response": ai_text})
    except Exception as e:
        traceback.print_exc()
        print(f"[ERROR] API 调用失败: {e}", file=sys.stderr)
        return jsonify({"response": "我现在要休息了"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
