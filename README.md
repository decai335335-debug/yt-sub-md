# yt-sub-md

一键批量下载 YouTube 视频字幕，自动转为无时间轴的 Markdown 文件。默认提取视频**原语言**（非翻译字幕），支持**中英双语逐句对照**模式，直接写入 Obsidian 笔记库。

---

## 解决什么痛点

**以前是这样的：**

- 想精读一个 YouTube 视频，只能开着视频反复暂停、抄写字幕
- 看到好的教程想整理进笔记，手动复制字幕到 Markdown，还要逐条删除时间戳
- 批量调研一个播放列表的内容，只能一个个视频点进去复制字幕
- 下载的字幕默认是英文，需要自己再去翻设置找原语言
- 文件名带 `\ / : * ? " < > |` 等特殊符号，保存到 Windows 上直接报错

**现在是这样的：**

- 粘贴一个链接或一整页链接，回车即下载，全部变成干净的 Markdown
- 自动去掉 `[Music]` 等噪音标签，按语义重新分段，阅读体验接近文章
- 默认优先下载原语言字幕（手动字幕 > 自动生成 > 翻译），不用每次都选语言
- 播放列表直接展开，一次批量处理几十个视频
- 文件名自动清理非法字符，重名自动加后缀，零报错

**适合谁用：**

- **外语学习者** —— 想精读 YouTube 教程、演讲、纪录片，把字幕当阅读材料
- **知识整理者 / Obsidian 用户** —— 看到好视频想存进笔记库，后续检索、批注、关联
- **内容调研者** —— 需要快速扫描一个播放列表里多个视频的内容梗概

---

## 核心功能

| 功能 | 解决什么问题 |
|------|-------------|
| **批量多链接粘贴** | 一次复制 20 个视频链接，空行结束即可批量下载，不用逐个输入 |
| **播放列表自动展开** | 给一个播放列表链接，自动提取里面所有视频逐一处理 |
| **原语言优先策略** | 默认先拿上传者手打的原语言字幕，没有再拿自动生成，省去手动选语言的麻烦 |
| **无时间轴 Markdown** | 去掉所有时间戳，按句末标点自动分段，输出像文章一样可读 |
| **智能文件名** | 自动去除 Windows 保留字符、截断过长标题、重名自动加序号后缀 |
| **并发限速下载** | 默认 5 并发 + 1~3 秒随机延迟，防 YouTube 反爬，失败自动重试 3 次 |
| **无效链接过滤** | 自动过滤搜索结果页、频道页等无效链接，只保留可处理的视频/播放列表 |
| **中英双语模式** | 每句英文下紧跟中文翻译，适合需要对照阅读的深度学习者 |
| **CSV 报告导出** | 每次下载后自动生成 `_download_report.csv`，一眼看到哪些成功、哪些失败及原因 |

---

## 安装方法

### 1. 克隆或下载项目

```bash
cd E:/GitHubDownloads/kimi
git clone <仓库地址> yt-sub-md
```

或者直接解压到 `yt-sub-md` 文件夹。

### 2. 安装依赖

```bash
cd yt-sub-md
pip install -r requirements.txt
```

> **依赖：** Python 3.10+

### 3. 修改默认输出目录（可选）

打开 `config.py`，把 `DEFAULT_OUTPUT_DIR` 改成你的 Obsidian 仓库路径：

```python
DEFAULT_OUTPUT_DIR = Path("E:/Obsidian/主仓库/11-subtitles")
```

---

## 使用方法

### 场景一：粘贴多个视频链接批量下载（最常用）

**什么时候用：** 在浏览器里打开了一堆视频，想全部下载字幕保存到笔记库。

```bash
python main.py download
```

1. 不输入任何参数，程序自动进入交互模式
2. 选择输入方式 `links`
3. 逐行粘贴链接，**输入空行结束**：
   ```
   > https://www.youtube.com/watch?v=vgYXjI_-fj0
   > https://www.youtube.com/watch?v=LExqMSdX7iA
   > https://www.youtube.com/watch?v=55xgBZx1Jcg
   >
   ```
4. 按提示确认输出目录和语言（直接回车用默认）
5. 等待下载完成，打开输出目录查看 `.md` 文件和 `_download_report.csv`

### 场景二：从文件批量读取链接

**什么时候用：** 链接数量很多（50+），提前整理在一个文本文件里。

1. 创建一个 `links.txt`，每行一个链接，井号开头是注释：
   ```txt
   # 游戏设计相关
   https://www.youtube.com/watch?v=vgYXjI_-fj0
   https://www.youtube.com/watch?v=LExqMSdX7iA
   ```
2. 运行：
   ```bash
   python main.py download -f links.txt
   ```

### 场景三：下载播放列表（自动识别）

**什么时候用：** 发现一个系列教程或播客播放列表，想全部归档；或者同时有视频链接和播放列表链接要一起下载。

```bash
python main.py download
```

交互模式下，你可以混合粘贴视频链接和播放列表链接：

```
> https://www.youtube.com/watch?v=vgYXjI_-fj0
> https://www.youtube.com/playlist?list=PLwxDjxJeenFRGKsshkLvj8fYWM-t0hevY
> https://www.youtube.com/watch?v=55xgBZx1Jcg
>
```

程序自动识别播放列表链接，提取其中所有视频，并为每个播放列表创建一个以播放列表名称命名的子文件夹存放字幕。单视频链接则直接放入输出目录根目录。

> 💡 **提示**：同一个视频出现在不同播放列表中，或同时以单视频形式出现，只要目标文件夹不同，都会分别下载。

### 场景四：中英双语逐句对照（每句英文下跟中文）

**什么时候用：** 英文视频想同时保存原文和中文翻译，方便对照精读。

```bash
# 命令行
python main.py download -f links.txt --bilingual

# 交互模式：在最后一步选择 "是" 即可
```

输出示例：
```markdown
Forsaken.

被遗弃者。

Abandoned to the Dark.

被遗弃在黑暗中。
```

### 场景五：指定语言（覆盖默认原语言）

**什么时候用：** 视频有英文字幕但你想下载中文字幕，或者想强制下载某种语言。

```bash
python main.py download -f links.txt -l zh-Hans
```

### 场景六：命令行直接下载单个视频

```bash
python main.py download -u "https://www.youtube.com/watch?v=xxxx"
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| CLI 框架 | Typer —— 优雅的命令行参数解析和交互提示 |
| 控制台输出 | Rich —— 彩色日志、表格、Banner、进度反馈 |
| 字幕获取 | youtube-transcript-api —— 专门用于获取 YouTube 字幕 |
| 元数据 / 播放列表 | yt-dlp —— 提取视频标题、频道、时长、展开播放列表 |
| 数据校验 | Pydantic —— 类型安全的模型定义 |
| 重试机制 | Tenacity —— 指数退避重试 |
| 异步并发 | asyncio + Semaphore —— 控制并发量，避免触发反爬 |

---

## 文件结构

```
yt-sub-md/
├── main.py              # CLI 入口（typer），交互逻辑和批量调度
├── config.py            # 全局配置：输出目录、并发数、限速、重试、文件名安全映射
├── models.py            # Pydantic 数据模型：VideoMeta、DownloadResult、BatchReport
├── requirements.txt     # Python 依赖
├── core/                # 核心引擎
│   ├── __init__.py
│   ├── extractor.py     # YouTube URL → 11 位 Video ID（支持 6 种链接格式）
│   ├── metadata.py      # yt-dlp 提取标题、频道、时长、原语言标记
│   ├── downloader.py    # 字幕下载主逻辑：语言决策、重试、文件保存
│   └── formatter.py     # 字幕 JSON → 无时间轴 Markdown（语义分段、去噪、元数据头）
└── utils/               # 工具层
    ├── __init__.py
    ├── logger.py        # Rich 控制台输出：Banner、单条结果、统计表格
    └── retry.py         # Tenacity 通用重试装饰器
```

---

## 常见问题

**Q: 运行时报错 `type object 'YouTubeTranscriptApi' has no attribute 'list_transcripts'`**

A: `youtube-transcript-api` 在 v1.x 版本中 API 发生了 Breaking Change，类方法改成了实例方法。
- 已修复：`list_transcripts(video_id)` → `YouTubeTranscriptApi().list(video_id)`
- 已修复：`get_transcript(video_id)` → `YouTubeTranscriptApi().fetch(video_id).to_raw_data()`
- 如仍遇到此问题，请确保 `requirements.txt` 中的版本号已安装，并重新执行 `pip install -r requirements.txt`

**Q: 粘贴多个链接，程序只识别到第一个**

A: 早期版本使用 `typer` 的 `Prompt.ask()`，它只读取单行输入。后续已改为 `while input()` 循环 + 空行结束，支持多行批量粘贴。请更新到最新版本。

**Q: 为什么之前下载到中文，现在变成英文了？**

A: 早期版本语言策略是"第一个手动字幕优先"，不区分原语言和翻译。很多英文视频上传者同时提供了中文字幕，导致优先下载了中文。v0.1.3 修复后，程序会先读取 yt-dlp 返回的 `original_language` 标记，**优先下载视频原语言**（通常是英文），不会再误取翻译字幕。

**Q: 视频有字幕但下载失败，提示 "无可用字幕"**

A: 该视频可能只有自动生成字幕但没有手动字幕，且你指定了 `--lang` 强制语言。尝试不指定 `-l` 参数，让程序按默认策略自动寻找。如果确实没有任何字幕，建议用 Whisper 转录音频。

**Q: 下载文件名是乱码或包含奇怪字符**

A: 程序会自动替换 Windows 保留字符（`\ / : * ? " < > |`）为下划线。如仍有异常，请检查视频原标题是否包含 emoji 或特殊 Unicode，可在 `config.py` 中扩展 `FILENAME_BAD_CHARS`。

**Q: 如何只下载特定语言的字幕？**

A: 使用 `-l` 参数，如 `-l en` 强制英文，`-l zh-Hans` 强制简体中文。注意：如果视频没有该语言字幕，会记录失败。

---

## 更新日志

### v0.1.4（2025-06-06）
- **新增** 播放列表自动识别：混合粘贴视频链接和播放列表链接，程序自动展开播放列表
- **新增** 播放列表子文件夹归档：每个播放列表的字幕自动放入以播放列表名称命名的子文件夹
- **优化** 去重策略增强：按 `(video_id, output_dir)` 去重，同一视频在不同播放列表中可分别下载
- **修复** Windows GBK 控制台 Rich 输出编码错误

### v0.1.3（2025-06-05）
- **修复** 语言策略：优先使用 yt-dlp 返回的 `original_language` 下载原语言字幕，避免误取翻译字幕
- **新增** 中英双语下载模式（`--bilingual`），每句英文下跟中文翻译
- **优化** 元数据获取改为"随下载随获取"，不再开头卡死等待所有元数据
- **优化** 自动过滤搜索结果页、频道页等无效链接
- **修复** `download_one` 改为在线程池执行，避免阻塞 asyncio 事件循环

### v0.1.2（2025-06-05）
- **修复** 交互模式支持多行链接粘贴（参考 github-repo-downloader 的 `prompt_links` 设计）
- **修复** 支持空格、逗号、换行混合分隔的链接输入
- **优化** 输入链接自动去重

### v0.1.1（2025-06-05）
- **修复** 适配 `youtube-transcript-api` v1.x API（`list_transcripts` → `list`，`get_transcript` → `fetch`）
- **修复** `fetch()` 返回对象需调用 `.to_raw_data()` 获取原始数据

### v0.1.0（2025-06-05）
- **新增** 基础功能：URL 解析、元数据获取、字幕下载、Markdown 格式化
- **新增** 交互模式（links / file / playlist）
- **新增** 并发下载、限速、重试、CSV 报告
- **新增** 原语言优先策略（手动字幕 > 自动生成 > 翻译）
