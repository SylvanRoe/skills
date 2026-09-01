---
name: video-script-extract
description: "Extract transcript and repurpose video/audio into platform-ready scripts. Local, offline pipeline: download from links (Douyin/Bilibili/Xiaohongshu/YouTube/etc.) via yt-dlp, transcribe speech to text in Chinese/English with faster-whisper + ffmpeg, then rewrite into Xiaohongshu notes, Douyin scripts, Bilibili video outlines, or YouTube scripts (3 rewrite strengths each). Use for: 提取文案, 视频转写, 字幕生成, 短视频脚本, 小红书笔记, 口播稿, 二创, transcribe video, extract transcript, video script, subtitles, repurpose content, repurposing, content repurposing, speech to text, whisper transcription, douyin script, xiaohongshu, bilibili, youtube script."
allowed-tools: Bash(python:*), Bash(pip:*), Bash(ffmpeg:*), Bash(ffprobe:*), Bash(yt-dlp:*)
---

# Video Script Extract

Extract a video or audio file's transcript and repurpose it into ready-to-publish scripts for multiple platforms — entirely **offline / local**, no third-party upload.

![video-script-extract](https://img.shields.io/badge/local-offline-2ea44f)

## What it does

1. **Fetch** — download video/audio from a URL (yt-dlp supports Douyin, Bilibili, Xiaohongshu, Kuaishou, Weibo, YouTube, and more).
2. **Transcribe** — extract audio with `ffmpeg`, run `faster-whisper` locally to get text + `.srt` subtitles + segmented `.json`.
3. **Structure** — turn the transcript into notes / a mind-map outline.
4. **Repurpose** — rewrite into platform-native scripts: **Xiaohongshu**, **Douyin**, **Bilibili**, **YouTube**, each at 3 strengths (light / medium / heavy).

All processing runs on the user's machine. The video never leaves the device.

## Quick Start

```bash
cd tools/video-script-extract

# 1. Install dependencies (ffmpeg must be installed system-wide first)
python scripts/setup_env.py

# 2. Transcribe a local file -> .txt / .srt / .json
python scripts/transcribe.py "video.mp4" --model small --language zh --output-dir ./out

# 3. Repurpose the transcript into a Xiaohongshu note (medium strength)
python scripts/rewrite.py ./out/video.txt --platform xiaohongshu --style medium
```

## Features

| Capability | How |
|------------|-----|
| Multi-platform link download | `scripts/fetch_media.py` (yt-dlp) |
| Local speech-to-text (CN/EN) | `scripts/transcribe.py` (ffmpeg + faster-whisper) |
| Notes & mind-map outline | prompts in `references/prompts.json` (`notes`, `mindmap`) |
| 4-platform repurposing | `scripts/rewrite.py` + `references/prompts.json` |
| Multi-LLM backend | `--backend deepseek / openai / local / none` |
| Agent / function-calling | `references/tool_schema.json` |

## Step 1 — Download from a link

```bash
python scripts/fetch_media.py "https://www.bilibili.com/video/BVxxxx" --audio-only -o ./downloads
```

If you already have a local file, skip this step.

## Step 2 — Transcribe

```bash
python scripts/transcribe.py "video.mp4" \
    --model small \          # tiny | small | medium | large-v3
    --language zh \          # zh / en / auto-detect
    --hf-mirror https://hf-mirror.com \
    --output-dir ./out
```

Outputs in `./out`:

| File | Contents |
|------|----------|
| `*.txt` | Plain transcript |
| `*.srt` | Subtitles (editable in any editor) |
| `*.json` | Segments with timestamps + language + confidence |

`--model` trade-off: `small` is fast and accurate for clear CN speech; use `large-v3` for heavy accent, jargon, or noisy audio (slower, more RAM).

## Step 3 — Repurpose / Rewrite

```bash
python scripts/rewrite.py ./out/video.txt \
    --platform xiaohongshu \   # xiaohongshu | douyin | bilibili | youtube
    --style medium \            # light | medium | heavy
    --backend none              # none | deepseek | openai | local
```

### Platforms

| `--platform` | Target | Deliverable |
|--------------|--------|-------------|
| `xiaohongshu` | 小红书 | Image-text note (标题/正文/标签) |
| `douyin` | 抖音 | Short-video voiceover script (hook + beats + CTA) |
| `bilibili` | 哔哩哔哩 | Mid-long video outline (分P/章节/文案) |
| `youtube` | YouTube | Video script + English SEO (title/description/tags) |

### Strengths

- **light** — keep the original structure and wording, light polish only.
- **medium** — restructure for the platform, keep the core message.
- **heavy** — full reimagining: new angle, hook, and format native to the platform.

### Backends

- `--backend none` (default): writes a ready-to-use prompt file (`*.{platform}_{style}.md`) you can paste into any LLM, or execute manually. No API key needed.
- `--backend deepseek` / `openai`: calls the model directly (set `DEEPSEEK_API_KEY` / `OPENAI_API_KEY`, or pass `--api-key`).
- `--backend local`: calls an OpenAI-compatible endpoint (e.g. Ollama) via `--base-url`.

```bash
# Direct call to DeepSeek
python scripts/rewrite.py ./out/video.txt --platform douyin --style heavy \
    --backend deepseek --api-key $DEEPSEEK_API_KEY
```

## Agent / Function-calling usage

To let any OpenAI-compatible model (DeepSeek, GPT, Codex, etc.) drive this skill, register the three functions from `references/tool_schema.json`:

- `vse_fetch_media` — download from a URL
- `vse_transcribe` — transcribe a file
- `vse_rewrite` — repurpose a transcript

The schema is standard `functions`/`tools` format; the model decides when to call them.

## Examples

**Link → Xiaohongshu note**

```bash
python scripts/fetch_media.py "https://v.douyin.com/xxxx/" --audio-only -o ./d
python scripts/transcribe.py ./d/*.mp4 --model small --language zh -o ./out
python scripts/rewrite.py ./out/*.txt --platform xiaohongshu --style medium
```

**Local file → YouTube script (heavy, English SEO)**

```bash
python scripts/transcribe.py "talk.mp4" --model large-v3 --language en -o ./out
python scripts/rewrite.py ./out/talk.txt --platform youtube --style heavy
```

## Use Cases

- **Content repurposing** — turn one long video into clips/scripts for 4 platforms.
- **Subtitles** — generate `.srt` for any video.
- **Meeting / interview notes** — transcribe and summarize.
- **Competitor teardown** — extract a rival's video script and adapt it.
- **Course / podcast digest** — transcript → structured notes + mind map.

## Requirements

- Python 3.10+
- `ffmpeg` + `ffprobe` on `PATH` (install system-wide; not via pip)
- First run: `python scripts/setup_env.py` installs `faster-whisper`, `yt-dlp`
- Whisper model downloaded on first use (set `--hf-mirror` in CN)

## References

- `references/prompts.json` — machine-readable prompt library (4 platforms × 3 strengths + notes + mindmap)
- `references/tool_schema.json` — OpenAI-compatible function-calling schema
- `references/rewrite_prompts.md` — human-readable rewrite guide

## Related Skills

This repo will collect more skills over time. Track updates or open an issue to suggest one.

## Documentation

- Whisper (OpenAI): https://github.com/openai/whisper
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- Repo: https://github.com/SylvanRoe/skills
