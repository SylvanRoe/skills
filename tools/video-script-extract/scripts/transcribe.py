#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transcribe.py — 视频/音频文案提取（转写）核心脚本
====================================================
把任意视频或音频文件转写为文本，输出三种成果：
  1. <名字>.txt   纯文案（逐段换行，便于阅读与复制）
  2. <名字>.srt   带时间戳字幕（可直接导入剪辑软件 / 用作外挂字幕）
  3. <名字>.json  完整分段（含起止时间、语言、置信度，供后续结构化处理）

依赖：
  - ffmpeg（需在 PATH 中，Windows 下若未装可 `winget install Gyan.FFmpeg`）
  - faster-whisper（`pip install faster-whisper`）
首次运行会自动从 Hugging Face 下载模型；国内网络可加 --hf-mirror 走镜像。

用法示例：
  python transcribe.py 视频.mp4
  python transcribe.py 音频.m4a --model small --language zh --output-dir ./out
  python transcribe.py 视频.mp4 --model large-v3 --hf-mirror https://hf-mirror.com
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(
        description="视频/音频转写：提取音频并用 faster-whisper 生成文案/字幕/分段 JSON",
    )
    p.add_argument("input", help="视频或音频文件路径")
    p.add_argument("--model", default="small",
                   help="whisper 模型档位：tiny/base/small/medium/large-v2/large-v3（默认 small）")
    p.add_argument("--language", default=None,
                   help="语言代码（如 zh/en/ja），默认自动检测")
    p.add_argument("--output-dir", "-o", default=None,
                   help="输出目录（默认与输入同目录）")
    p.add_argument("--device", default="auto",
                   help="推理设备 auto/cpu/cuda（默认 auto）")
    p.add_argument("--compute-type", default="auto",
                   help="计算精度 auto/float16/int8（默认 auto）")
    p.add_argument("--beam-size", type=int, default=5,
                   help="beam search 宽度（默认 5，越大越慢越稳）")
    p.add_argument("--hf-mirror", default=None,
                   help="Hugging Face 镜像地址，如 https://hf-mirror.com（国内加速模型下载）")
    p.add_argument("--keep-wav", action="store_true",
                   help="保留中间抽取的 wav 音频文件")
    return p.parse_args()


def fmt_ts(seconds: float) -> str:
    """秒 -> SRT 时间戳 HH:MM:SS,mmm"""
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def extract_audio(input_path: str, wav_path: str) -> None:
    """用 ffmpeg 抽取 16kHz 单声道 wav（whisper 最稳的输入格式）"""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        wav_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "ffmpeg 抽取音频失败。请确认已安装 ffmpeg 且在 PATH 中。\n" + proc.stderr[-2000:]
        )


def build_srt(segments) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)


def main():
    args = parse_args()

    # 在导入 faster_whisper 之前设置环境变量，确保模型能正常下载
    # HF_HUB_DISABLE_XET：禁用 Hugging Face 的 Xet 后端（国内/无鉴权时 Xet 的 CAS 服务器常返回 401，导致下载失败）
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    if args.hf_mirror:
        os.environ.setdefault("HF_ENDPOINT", args.hf_mirror)

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        sys.exit(f"[错误] 找不到文件：{input_path}")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit(
            "[错误] 未安装 faster-whisper。请先运行：\n"
            "  pip install faster-whisper\n"
            "  或运行本 skill 的 scripts/setup_env.py 一键安装。"
        )

    out_dir = Path(args.output_dir).resolve() if args.output_dir else input_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem

    # 1) 抽取音频
    print(f"[1/3] 抽取音频：{input_path.name}", flush=True)
    tmp_dir = tempfile.mkdtemp(prefix="vse_")
    wav_path = os.path.join(tmp_dir, "audio.wav")
    extract_audio(str(input_path), wav_path)

    # 2) 加载模型并转写
    print(f"[2/3] 加载模型 '{args.model}' 并转写（首次会下载模型，请耐心等待）...", flush=True)
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    segments, info = model.transcribe(
        wav_path,
        language=args.language,
        beam_size=args.beam_size,
        vad_filter=True,
    )
    seg_list = list(segments)

    # 3) 写结果
    print(f"[3/3] 写出结果到 {out_dir}", flush=True)
    detected_lang = getattr(info, "language", args.language or "?")
    lang_prob = getattr(info, "language_probability", None)

    # 纯文案
    txt_path = out_dir / f"{stem}.txt"
    txt_path.write_text(
        "\n".join(s.text.strip() for s in seg_list if s.text.strip()),
        encoding="utf-8",
    )

    # 字幕
    srt_path = out_dir / f"{stem}.srt"
    srt_path.write_text(build_srt(seg_list), encoding="utf-8")

    # 完整分段 JSON
    json_path = out_dir / f"{stem}.json"
    json_data = {
        "source": str(input_path),
        "model": args.model,
        "language": detected_lang,
        "language_probability": lang_prob,
        "duration": getattr(info, "duration", None),
        "segments": [
            {
                "id": s.id,
                "start": round(s.start, 3),
                "end": round(s.end, 3),
                "text": s.text.strip(),
                "avg_logprob": round(s.avg_logprob, 4) if s.avg_logprob is not None else None,
                "no_speech_prob": round(s.no_speech_prob, 4) if s.no_speech_prob is not None else None,
            }
            for s in seg_list
        ],
    }
    json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 清理临时文件
    if args.keep_wav:
        import shutil
        keep = out_dir / f"{stem}.wav"
        shutil.move(wav_path, str(keep))
        print(f"  已保留音频：{keep}")
    else:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    word_count = sum(len(s.text) for s in seg_list)
    print("\n✅ 转写完成：")
    print(f"  语言：{detected_lang}" + (f"（置信度 {lang_prob:.0%}）" if lang_prob else ""))
    print(f"  段落数：{len(seg_list)}，字符数：约 {word_count}")
    print(f"  纯文案：{txt_path}")
    print(f"  字幕  ：{srt_path}")
    print(f"  分段  ：{json_path}")


if __name__ == "__main__":
    main()
