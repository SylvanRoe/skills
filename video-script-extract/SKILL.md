---
name: video-script-extract
description: 视频/音频文案提取与二次创作（通用版，可脱离 WorkBuddy 被任意 AI 调用）。覆盖本地离线转写（ffmpeg + faster-whisper）、多平台链接下载（yt-dlp）、结构化笔记/思维导图，以及多平台二创——小红书、抖音、哔哩哔哩、YouTube。二创支持多种 LLM 后端（DeepSeek / OpenAI / 本地 / 无密钥仅出提示词）。Use when the user provides a video/audio file or link and wants transcription, subtitles, structured notes, a mind map, or platform-specific rewrites (Xiaohongshu / Douyin / Bilibili / YouTube). Works standalone via CLI and with any OpenAI-compatible LLM or agent.
agent_created: true
---

# 视频文案提取及二次创作（通用版）

## 这个 skill 能干什么

把一段视频/音频变成可复用的文本资产，再加工成笔记或各平台风格脚本：

1. **提取文案**：`ffmpeg` + `faster-whisper` 本地离线转写 → 纯文案 `.txt` / 字幕 `.srt` / 分段 `.json`（不上传、不联网识别）。
2. **多平台下载**：`yt-dlp` 拉取抖音 / B站 / 快手 / 小红书 / 微博 / YouTube 等链接。
3. **结构化**：知识笔记、思维导图大纲。
4. **多平台二创**：小红书 / 抖音 / 哔哩哔哩 / YouTube，各 3 档强度（轻度/中度/重度）。

## 它是「通用」的（重点）

本 skill **不绑定 WorkBuddy**，三种用法任选：

- **① 纯命令行（任何人/任何环境）**
  ```bash
  python scripts/transcribe.py 视频.mp4 --model small --language zh -o ./out
  python scripts/rewrite.py ./out/视频.txt --platform xiaohongshu --style medium
  ```
- **② 任意 OpenAI 兼容 LLM 做二创**（DeepSeek / OpenAI / 本地 Ollama 等）
  ```bash
  # DeepSeek
  python scripts/rewrite.py 视频.txt --platform douyin --style heavy \
      --backend deepseek --api-key $DEEPSEEK_API_KEY
  # 本地 Ollama（OpenAI 兼容，免 key）
  python scripts/rewrite.py 视频.json --platform bilibili --backend local
  ```
  无 API key 时 `--backend none`（默认）只输出**组装好的提示词文件**，可直接粘给任意大模型或人工执行。
- **③ 接入任意支持函数调用的 Agent**（DeepSeek / OpenAI / Codex 等）
  把 `references/tool_schema.json` 里的 3 个函数（`vse_transcribe` / `vse_fetch_media` / `vse_rewrite`）注册为工具，模型即可自主决定何时调用。SKILL.md 的脚本即这些函数的实现。

## 何时使用

- 用户发来视频/音频文件或粘贴平台链接，要求「提取文案/转文字/字幕/笔记/思维导图」。
- 用户要求「二创」「改写脚本」「小红书笔记/抖音脚本/B站稿/YouTube 方案」。
- 会议录音、课程、访谈、播客的转写与归档。

## 工作流

```
链接 ──▶ fetch_media.py ──┐
                          ├──▶ transcribe.py ──▶ .txt/.srt/.json ──▶ rewrite.py / 笔记 / 导图
本地文件 ─────────────────┘
```

1. **链接输入** → `scripts/fetch_media.py "链接" [--audio-only] [-o ./downloads]`；需登录加 `--cookies chrome`。
2. **本地文件** → 直接转写。
3. **转写** → `scripts/transcribe.py "路径" --model small --language zh -o ./out`（首次下载模型，国内加 `--hf-mirror https://hf-mirror.com`）。
4. **加工** → 笔记/导图：用 `references/rewrite_prompts.md` 模板；二创：用 `scripts/rewrite.py --platform <平台> --style <强度>`。

## 二创平台与强度

| 平台（`--platform`） | 产物 |
|------|------|
| `xiaohongshu` 小红书 | 图文笔记（标题+正文+话题标签） |
| `douyin` 抖音 | 短视频口播脚本（黄金钩子+分镜+互动） |
| `bilibili` 哔哩哔哩 | 中长视频稿（章节小标题+梗点+三连引导） |
| `youtube` YouTube | 视频方案（中文脚本+英文标题/描述/标签/章节） |

强度（`--style`）：`light` 轻度保真 / `medium` 中度平衡（默认）/ `heavy` 重度原创。
另支持 `--mode notes`（结构化笔记）、`--mode mindmap`（思维导图）。

**铁律**：只重组原文信息，不捏造原文没有的事实/数据/人名；无法支撑处标注「（原文未提及）」。

## 资源清单

- `scripts/transcribe.py` —— 核心转写（ffmpeg 抽音频 + faster-whisper 识别）。
- `scripts/fetch_media.py` —— 多平台链接下载（yt-dlp）。
- `scripts/rewrite.py` —— 通用二创客户端（多后端、多平台、无 key 出提示词）。
- `scripts/setup_env.py` —— 一键装依赖（faster-whisper、yt-dlp）。
- `references/prompts.json` —— 机器可读的提示词库（平台×强度 + 笔记/导图）。
- `references/rewrite_prompts.md` —— 提示词人文档（含 4 平台说明）。
- `references/tool_schema.json` —— OpenAI 兼容函数调用 schema（供任意 agent 接入）。
