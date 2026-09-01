#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_media.py — 多平台视频/音频链接下载（可选，配合 transcribe.py 使用）
==========================================================================
基于 yt-dlp，支持抖音、B站、快手、小红书、微博、YouTube 等主流平台，
也支持直接下载 MP4/MP3/M4A 等音视频直链。下载后可交给 transcribe.py 转写。

依赖：yt-dlp（`pip install yt-dlp`），推荐同时装 ffmpeg（用于合并流）。

用法示例：
  python fetch_media.py "https://v.douyin.com/xxxx" -o ./downloads
  python fetch_media.py "https://www.bilibili.com/video/BVxxxx" --audio-only
  python fetch_media.py "https://example.com/audio.mp3"

常用参数：
  -o/--output-dir   输出目录（默认 ./downloads）
  --audio-only      只下载音频（转写用，更快）
  --cookies         从浏览器读取 cookie 绕过登录限制（格式：--cookies chrome）
"""

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="多平台视频/音频下载（基于 yt-dlp）")
    p.add_argument("url", help="视频/音频链接")
    p.add_argument("-o", "--output-dir", default="./downloads", help="输出目录")
    p.add_argument("--audio-only", action="store_true", help="只下载音频（转写用）")
    p.add_argument("--cookies", default=None, help="浏览器来源读取 cookie（如 chrome/firefox/edge）")
    p.add_argument("--format", default=None, help="自定义 yt-dlp 格式选择器（高级）")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 输出模板：视频用标题，音频直接 m4a
    if args.audio_only:
        tmpl = str(out_dir / "%(title).80s.%(ext)s")
        fmt = args.format or "bestaudio/best"
        post = ["-x", "--audio-format", "m4a"]
    else:
        tmpl = str(out_dir / "%(title).80s.%(ext)s")
        fmt = args.format or "bestvideo+bestaudio/best"
        post = ["--merge-output-format", "mp4"]

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", fmt,
        "-o", tmpl,
        "--no-playlist",
        "--restrict-filenames",
    ]
    if args.cookies:
        cmd += ["--cookies-from-browser", args.cookies]
    cmd += post
    cmd += [args.url]

    print("▶ 开始下载...", flush=True)
    proc = subprocess.run(cmd)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
