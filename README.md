# Skills

我（kk / SylvanRoe）开发的 **WorkBuddy Skills** 开源集合。本仓库会持续收纳多个自研 skill，每个 skill 独立成目录。

> 这里的 skill **不绑定任何单一 AI 产品**：脚本是纯 Python，二创支持任意 OpenAI 兼容 LLM（DeepSeek / OpenAI / 本地），并附带函数调用 schema，可被任意支持 function-calling 的模型（DeepSeek、OpenAI、Codex 等）直接调用。

## 已收录

### [`video-script-extract`](./video-script-extract) — 视频/音频文案提取与二次创作（通用版）

把视频/音频变成可复用文本资产，再加工成笔记或各平台风格脚本。

- **提取文案**：`ffmpeg` + `faster-whisper` **本地离线**转写 → `.txt` 文案 / `.srt` 字幕 / `.json` 分段（不上传、不联网识别）。
- **多平台下载**：`yt-dlp` 拉取 抖音 / B站 / 快手 / 小红书 / 微博 / YouTube 等链接。
- **结构化**：知识笔记、思维导图大纲。
- **多平台二创**：覆盖 **小红书 / 抖音 / 哔哩哔哩 / YouTube**，各 3 档强度（轻度 / 中度 / 重度）。

**三种用法（任选）：**

```bash
# ① 纯命令行
python video-script-extract/scripts/transcribe.py 视频.mp4 --model small --language zh -o ./out
python video-script-extract/scripts/rewrite.py ./out/视频.txt --platform xiaohongshu --style medium

# ② 任意 OpenAI 兼容 LLM 做二创（DeepSeek 示例）
python video-script-extract/scripts/rewrite.py 视频.txt --platform douyin --style heavy \
    --backend deepseek --api-key $DEEPSEEK_API_KEY
# 本地 Ollama（免 key）
python video-script-extract/scripts/rewrite.py 视频.json --platform bilibili --backend local

# ③ 接入任意支持函数调用的 Agent
# 把 video-script-extract/references/tool_schema.json 的 3 个函数
# （vse_transcribe / vse_fetch_media / vse_rewrite）注册为工具即可。
```

无 API key 时 `--backend none`（默认）只生成**组装好的提示词文件**，可直接粘给任意大模型或人工执行。

## 依赖与离线说明

- `video-script-extract` 依赖 `ffmpeg`、`faster-whisper`、`yt-dlp`，首次使用运行 `scripts/setup_env.py` 一键安装。
- 转写与下载均**本地离线**完成，视频不会上传到任何第三方服务器；只有「二创」这一步会调用你指定的 LLM。

## 规划中

更多自研 skill 会陆续开源到本仓库。欢迎 Watch / Star 跟踪更新。

## License

各 skill 目录内如含独立 LICENSE 以其为准；本仓库默认 **MIT**。
