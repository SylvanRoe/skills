#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rewrite.py — 文案二次创作（通用、可脱离 WorkBuddy 运行）
========================================================
把 transcribe.py 产出的文案（.txt 或 .json）改写成指定平台的风格脚本。

设计目标：让「任意 AI / 任意环境」都能用。
  - 纯 Python 标准库，无强制第三方依赖；
  - 支持多 LLM 后端（DeepSeek / OpenAI / 本地 OpenAI 兼容服务 / 无后端）；
  - 无 API key 时（--backend none）只输出「组装好的提示词」，可直接粘给任何模型或人工执行；
  - 提示词库集中在 references/prompts.json，便于增删平台与风格。

支持平台（--platform）：
  xiaohongshu  小红书图文笔记
  douyin       抖音短视频脚本
  bilibili     哔哩哔哩视频稿
  youtube      YouTube 视频方案（含英文 SEO）

改写强度（--style）：light(轻度) / medium(中度，默认) / heavy(重度)

用法示例：
  # 1) 无密钥：只产出提示词（交给任意模型/人工）
  python rewrite.py 文案.txt --platform xiaohongshu --style medium

  # 2) 用 DeepSeek 直接生成
  python rewrite.py 文案.txt --platform douyin --style heavy \
      --backend deepseek --api-key sk-xxxx

  # 3) 用本地 Ollama（OpenAI 兼容）
  python rewrite.py 文案.json --platform bilibili --backend local

  # 4) 结构化笔记 / 思维导图
  python rewrite.py 文案.txt --mode notes
  python rewrite.py 文案.txt --mode mindmap
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# 各后端的默认 base_url 与模型（可用 --base-url / --model 覆盖）
BACKENDS = {
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat",
                 "env_key": "DEEPSEEK_API_KEY"},
    "openai":   {"base_url": "https://api.openai.com/v1", "model": "gpt-4o",
                 "env_key": "OPENAI_API_KEY"},
    "local":    {"base_url": "http://localhost:11434/v1", "model": "llama3",
                 "env_key": None},  # 本地服务通常无需 key
}

PLATFORMS = ["xiaohongshu", "douyin", "bilibili", "youtube"]
STYLES = ["light", "medium", "heavy"]


def load_prompts(prompts_path: Path) -> dict:
    if not prompts_path.exists():
        sys.exit(f"[错误] 找不到提示词库：{prompts_path}\n请确认 references/prompts.json 与本脚本同级。")
    with open(prompts_path, encoding="utf-8") as f:
        return json.load(f)


def read_transcript(path: Path) -> str:
    """读取转写结果：.json 抽取分段文本，.txt 直接读。"""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
            segs = data.get("segments") or []
            parts = [s.get("text", "").strip() for s in segs if isinstance(s, dict)]
            joined = "\n".join(p for p in parts if p)
            if joined:
                return joined
            # 退化：直接用顶层 text 字段（若有）
            if isinstance(data.get("text"), str):
                return data["text"]
        except json.JSONDecodeError:
            pass
        # JSON 解析失败则退回原始文本
        return text
    return text


def build_messages(prompts: dict, mode: str, platform: str, style: str,
                   transcript: str, custom: str):
    if mode in ("notes", "mindmap"):
        block = prompts[mode]
    else:
        if platform not in prompts["platforms"]:
            sys.exit(f"[错误] 未知平台 '{platform}'，可选：{', '.join(PLATFORMS)}")
        if style not in prompts["platforms"][platform]:
            sys.exit(f"[错误] 未知强度 '{style}'，可选：{', '.join(STYLES)}")
        block = prompts["platforms"][platform][style]

    system = block.get("system", "")
    user = block.get("user", "").replace("{{文案}}", transcript)
    user = user.replace("{{自定义指令}}", custom or "")
    # 清掉残留的空占位行
    user = user.replace("\n\n\n", "\n\n").strip()
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def call_llm(messages: list, backend: str, api_key: str, model: str,
             base_url: str, timeout: int = 180) -> str:
    cfg = BACKENDS.get(backend, {})
    base_url = base_url or cfg.get("base_url")
    model = model or cfg.get("model")
    if not base_url or not model:
        sys.exit(f"[错误] 后端 '{backend}' 缺少 base_url 或 model，请用 --base-url / --model 指定。")

    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.8,
    }).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:1000]
        sys.exit(f"[错误] LLM 接口返回 {e.code}：{detail}")
    except urllib.error.URLError as e:
        sys.exit(f"[错误] 无法连接 LLM 接口（{url}）：{e.reason}")


def resolve_api_key(backend: str, cli_key: str) -> str:
    if cli_key:
        return cli_key
    env_name = BACKENDS.get(backend, {}).get("env_key")
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    # 通用兜底
    return os.environ.get("LLM_API_KEY", "")


def main():
    here = Path(__file__).resolve().parent
    prompts_path = here.parent / "references" / "prompts.json"

    p = argparse.ArgumentParser(
        description="视频/音频文案二次创作（多平台、多后端、可脱离 WorkBuddy 使用）",
    )
    p.add_argument("transcript", help="转写结果文件：.txt 或 .json（来自 transcribe.py）")
    p.add_argument("--mode", choices=["rewrite", "notes", "mindmap"], default="rewrite",
                   help="rewrite=平台二创；notes=结构化笔记；mindmap=思维导图（默认 rewrite）")
    p.add_argument("--platform", default="xiaohongshu",
                   help=f"二创平台，可选：{', '.join(PLATFORMS)}（仅 --mode rewrite 生效）")
    p.add_argument("--style", choices=STYLES, default="medium",
                   help="改写强度 light/medium/heavy（默认 medium）")
    p.add_argument("--backend", default="none",
                   choices=["none", "deepseek", "openai", "local"],
                   help="LLM 后端；none=只输出提示词不调用模型（默认 none）")
    p.add_argument("--api-key", default=None, help="API key（也可用环境变量）")
    p.add_argument("--model", default=None, help="模型名（覆盖后端默认）")
    p.add_argument("--base-url", default=None, help="OpenAI 兼容接口的 base_url")
    p.add_argument("--custom", default="", help="追加给模型的自定义指令")
    p.add_argument("--output", "-o", default=None, help="输出文件路径（默认同目录自动命名）")
    p.add_argument("--list-platforms", action="store_true", help="列出支持的平台并退出")
    args = p.parse_args()

    if args.list_platforms:
        prompts = load_prompts(prompts_path)
        print("支持平台：")
        for k, v in prompts["platforms"].items():
            print(f"  {k:14s} {v.get('name', '')}")
        return

    prompts = load_prompts(prompts_path)
    transcript_path = Path(args.transcript)
    if not transcript_path.exists():
        sys.exit(f"[错误] 找不到转写文件：{transcript_path}")
    transcript = read_transcript(transcript_path)

    messages = build_messages(
        prompts, args.mode, args.platform, args.style, transcript, args.custom
    )

    # 命名：<stem>.<平台或mode>_<style>.md
    if args.mode == "rewrite":
        tag = f"{args.platform}_{args.style}"
    else:
        tag = args.mode
    stem = transcript_path.stem
    out_path = Path(args.output) if args.output else transcript_path.parent / f"{stem}.{tag}.md"

    if args.backend == "none":
        # 无密钥：输出组装好的提示词，可交给任意模型/人工
        prompt_doc = (
            "# 二创提示词（由 rewrite.py 生成，可直接粘给任意大模型或人工执行）\n\n"
            f"> 模式：{args.mode} ｜ 平台：{args.platform} ｜ 强度：{args.style}\n\n"
            "## System\n\n" + messages[0]["content"] + "\n\n"
            "## User\n\n" + messages[1]["content"] + "\n"
        )
        out_path.write_text(prompt_doc, encoding="utf-8")
        print(f"✅ 已生成提示词文件（未调用模型）：{out_path}")
        print("   将该文件内容粘给任意大模型，或手动执行即可完成二创。")
        print("   也可加 --backend deepseek/openai/local 直接让本脚本调用模型生成结果。")
        return

    api_key = resolve_api_key(args.backend, args.api_key)
    if not api_key and args.backend != "local":
        sys.exit(f"[错误] 后端 '{args.backend}' 需要 API key：用 --api-key 或设置环境变量 "
                 f"{BACKENDS.get(args.backend, {}).get('env_key', 'LLM_API_KEY')}。")

    print(f"[1/2] 调用 {args.backend} 生成二创（平台={args.platform}, 强度={args.style}）...")
    result = call_llm(messages, args.backend, api_key, args.model or "",
                      args.base_url or "", timeout=180)
    out_path.write_text(result, encoding="utf-8")
    print(f"[2/2] 二创完成，已写出：{out_path}")


if __name__ == "__main__":
    main()
