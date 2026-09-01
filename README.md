# skills

自研的 **AI agent skills 集合**，采用 [anthropic/skills](https://github.com/anthropics/skills) 格式，可安装为 Claude Code 插件或用 `npx skills` 加载，也能被任意支持函数调用的 LLM（DeepSeek / OpenAI / Codex 等）调用。

所有 skill 均**本地离线**运行，数据不上传第三方。

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## 已收录 Skills

| Skill | 说明 |
|-------|------|
| [`video-script-extract`](./tools/video-script-extract) | 视频/音频文案提取与多平台二创：链接下载（yt-dlp）→ 本地 Whisper 中文转写（faster-whisper + ffmpeg）→ 笔记/思维导图 → 4 平台二创（小红书 / 抖音 / 哔哩哔哩 / YouTube，各 3 档强度） |

更多 skill 会陆续开源到本仓库。

## 安装方式

### 1. 作为 Claude Code 插件

```bash
/plugin marketplace add SylvanRoe/skills
/plugin install kk-skills
```

安装后，skill 以 `/kk-skills:video-script-extract` 等形式可用。

### 2. 作为 Skills（`npx skills`）

```bash
# 全部
npx skills add SylvanRoe/skills

# 单个
npx skills add SylvanRoe/skills@video-script-extract
```

### 3. 手动复制

```bash
git clone https://github.com/SylvanRoe/skills.git
cp -r skills/tools/* ~/.claude/skills/
# 或放入你的 agent skills 目录
```

## 快速使用

```bash
cd tools/video-script-extract

# 安装依赖（ffmpeg 需系统先行安装）
python scripts/setup_env.py

# 转写本地视频
python scripts/transcribe.py video.mp4 --model small --language zh -o ./out

# 二创成小红书笔记（中度改写）
python scripts/rewrite.py ./out/video.txt --platform xiaohongshu --style medium
```

## 多 LLM 后端

`rewrite.py` 支持多后端，无需锁定某家模型：

```bash
# 不调用模型，只生成可直接粘贴给任意 LLM 的提示词文件
python scripts/rewrite.py video.txt --platform douyin --style heavy --backend none

# 直接调用 DeepSeek
python scripts/rewrite.py video.txt --platform douyin --style heavy \
    --backend deepseek --api-key $DEEPSEEK_API_KEY

# 本地模型（OpenAI 兼容，如 Ollama）
python scripts/rewrite.py video.txt --platform youtube --style medium \
    --backend local --base-url http://localhost:11434/v1
```

## Agent / 函数调用

`tools/video-script-extract/references/tool_schema.json` 提供了 OpenAI 兼容的 function-calling schema（`vse_fetch_media` / `vse_transcribe` / `vse_rewrite`），任意支持函数调用的模型都能直接把它当工具调用。

## 仓库结构

```
skills/
├── .claude-plugin/plugin.json   # Claude Code 插件注册
├── skills.sh.json               # skills.sh 分组元数据
├── README.md
└── tools/
    └── video-script-extract/
        ├── SKILL.md
        ├── scripts/             # transcribe / fetch_media / rewrite / setup_env
        └── references/          # prompts.json / tool_schema.json / rewrite_prompts.md
```

## License

本仓库默认 **MIT**。各 skill 目录内如含独立 LICENSE 以其为准。
