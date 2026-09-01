#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_env.py — 一键初始化本 skill 的运行环境
==============================================
1. 定位可用的 Python 解释器（优先当前正在运行的 python）
2. 安装依赖：faster-whisper、yt-dlp
3. （可选）预下载 whisper 模型，避免首次转写时长时间等待

用法：
  python setup_env.py                 # 只装依赖
  python setup_env.py --model small   # 装依赖并预下载 small 模型
  python setup_env.py --hf-mirror https://hf-mirror.com   # 国内镜像
"""

import argparse
import subprocess
import sys


def run(cmd):
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd).returncode


def main():
    p = argparse.ArgumentParser(description="初始化视频文案提取 skill 的依赖环境")
    p.add_argument("--model", default=None, help="预下载的 whisper 模型档位（可选）")
    p.add_argument("--hf-mirror", default=None, help="Hugging Face 镜像，如 https://hf-mirror.com")
    args = p.parse_args()

    py = sys.executable
    print(f"使用 Python：{py}\n")

    # 1) 安装依赖
    rc = run([py, "-m", "pip", "install", "-U", "faster-whisper", "yt-dlp"])
    if rc != 0:
        sys.exit("[错误] 依赖安装失败，请检查网络后重试。")

    # 2) 预下载模型
    if args.model:
        import os
        os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
        if args.hf_mirror:
            os.environ.setdefault("HF_ENDPOINT", args.hf_mirror)
        print(f"\n预下载模型 '{args.model}' ...（首次较慢，取决于网络）")
        try:
            from faster_whisper import WhisperModel
            WhisperModel(args.model)
            print("✅ 模型已就绪。")
        except Exception as e:
            print(f"[警告] 模型预下载失败：{e}")
            print("  可稍后转写时自动下载，或加 --hf-mirror 指定镜像。")

    print("\n✅ 环境初始化完成。可运行：")
    print("   python scripts/transcribe.py <视频或音频文件>")


if __name__ == "__main__":
    main()
