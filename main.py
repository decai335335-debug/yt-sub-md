"""YouTube 字幕批量下载器 — CLI 入口

交互方式参考 github-repo-downloader：简洁命令 + 交互式询问
"""
import asyncio
import random
from pathlib import Path
from typing import Optional, List

import typer
from rich.prompt import Prompt, Confirm

from config import DEFAULT_OUTPUT_DIR, MAX_CONCURRENT, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX
from models import BatchReport, DownloadResult, VideoMeta, DownloadTask
from core.extractor import extract_video_id, is_playlist_url, filter_video_urls
from core.metadata import fetch_metadata
from core.downloader import download_with_delay, download_bilingual_with_delay
from utils.logger import console, print_banner, print_result, print_report

app = typer.Typer(
    name="ytmd",
    help="下载 YouTube 字幕为 Markdown（无时间轴）",
    add_completion=False,
)


def _expand_playlist(url: str) -> tuple[str, List[str]]:
    """用 yt-dlp 展开播放列表，返回 (标题, 视频链接列表)"""
    import yt_dlp
    urls = []
    opts = {"quiet": True, "extract_flat": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get("title", "playlist")
        for entry in info.get("entries", []):
            if entry:
                urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
    return title, urls


def _safe_folder_name(name: str) -> str:
    """生成安全的文件夹名"""
    from config import FILENAME_BAD_CHARS
    safe = name.strip()
    for ch in FILENAME_BAD_CHARS:
        safe = safe.replace(ch, "_")
    safe = safe[:80].strip("._")
    if not safe:
        safe = "playlist"
    return safe


def _read_url_file(path: Path) -> List[str]:
    """从 txt/csv 读取链接，每行一个"""
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def _collect_tasks(
    raw_urls: List[str],
    base_output: Path,
) -> List[DownloadTask]:
    """
    将原始链接解析为下载任务列表。
    自动识别播放列表，展开为视频任务，每个播放列表单独建子文件夹。
    同一视频在同一输出目录下会去重。
    """
    tasks: List[DownloadTask] = []
    seen = set()  # 去重: (video_id, output_dir_str)

    def _log(msg: str):
        """兼容 Windows 控制台的日志输出"""
        try:
            console.print(msg)
        except UnicodeEncodeError:
            # Windows GBK 控制台降级为普通 print
            plain = msg.replace("[blue]", "").replace("[/blue]", "")
            plain = plain.replace("[bold]", "").replace("[/bold]", "")
            plain = plain.replace("[yellow]", "").replace("[/yellow]", "")
            plain = plain.replace("ℹ", "[i]").replace("⚠", "[w]")
            print(plain)

    for raw in raw_urls:
        raw = raw.strip()
        if not raw:
            continue

        if is_playlist_url(raw):
            try:
                playlist_title, video_urls = _expand_playlist(raw)
                folder_name = _safe_folder_name(playlist_title)
                playlist_output = base_output / folder_name
                _log(
                    f"[blue]ℹ[/blue] 播放列表 '[bold]{playlist_title}[/bold]' → "
                    f"{len(video_urls)} 个视频 → 文件夹 '{folder_name}/'"
                )
                for vurl in video_urls:
                    vid = extract_video_id(vurl)
                    key = (vid, str(playlist_output))
                    if key not in seen:
                        seen.add(key)
                        tasks.append(DownloadTask(url=vurl, output_dir=playlist_output))
            except Exception as e:
                _log(f"[yellow]⚠[/yellow] 播放列表展开失败: {raw} — {e}")
        else:
            try:
                vid = extract_video_id(raw)
                key = (vid, str(base_output))
                if key not in seen:
                    seen.add(key)
                    tasks.append(DownloadTask(url=raw, output_dir=base_output))
            except ValueError:
                _log(f"[yellow]⚠[/yellow] 跳过无效链接: {raw}")

    return tasks


@app.command()
def download(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="YouTube 视频链接或播放列表链接"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="链接列表文件 (txt/csv)，支持混合视频和播放列表"),
    output: Optional[Path] = typer.Option(DEFAULT_OUTPUT_DIR, "--output", "-o", help="输出目录"),
    lang: Optional[str] = typer.Option(None, "--lang", "-l", help="指定语言代码，如 en, zh-Hans, ja"),
    max_concurrent: int = typer.Option(MAX_CONCURRENT, "--max-concurrent", "-c", help="最大并发数"),
    bilingual: bool = typer.Option(False, "--bilingual", "-b", help="中英双语模式（每句英文下跟中文）"),
):
    """
    下载 YouTube 字幕为 Markdown。
    支持混合输入视频链接和播放列表链接，自动识别播放列表并创建子文件夹。
    不指定参数时进入交互式询问。
    """
    print_banner()

    # 交互式补全参数
    if not url and not file:
        console.print("[dim]未检测到参数，进入交互模式...[/dim]\n")
        mode = Prompt.ask(
            "输入方式",
            choices=["links", "file"],
            default="links",
        )

        if mode == "links":
            console.print()
            console.print("-" * 50)
            console.print("  [bold]粘贴 YouTube 链接[/bold]")
            console.print("  · 支持视频链接 + 播放列表链接混合粘贴")
            console.print("  · 空格、逗号、换行分隔均可")
            console.print("  · 播放列表会自动展开到同名子文件夹")
            console.print("  · 输入空行结束")
            console.print("-" * 50)
            raw_lines = []
            while True:
                line = input("  > ")
                if line.strip() == "":
                    break
                raw_lines.append(line)

            # 合并并解析（兼容空格、逗号、换行）
            all_text = "\n".join(raw_lines)
            parts = [p.strip() for p in all_text.replace(",", " ").split() if p.strip() and not p.strip().startswith("#")]
            # 去重保持顺序
            seen = set()
            raw_urls = []
            for p in parts:
                if p not in seen:
                    seen.add(p)
                    raw_urls.append(p)
            console.print(f"[blue]ℹ[/blue] 解析到 {len(raw_urls)} 个链接\n")

        else:  # file
            file = Path(Prompt.ask("链接文件路径"))
            raw_urls = []

        # 通用后续选项
        if Confirm.ask("是否指定输出目录？", default=False):
            custom = Prompt.ask("输出目录", default=str(DEFAULT_OUTPUT_DIR))
            output = Path(custom)

        if not bilingual and Confirm.ask("是否指定语言？", default=False):
            lang = Prompt.ask("语言代码", default="auto")
            if lang == "auto":
                lang = None

        if not bilingual:
            bilingual = Confirm.ask("是否中英双语模式？", default=False)

    # 收集所有原始链接（命令行模式）
    if 'raw_urls' not in locals():
        raw_urls: List[str] = []
    if file and file.exists():
        raw_urls = _read_url_file(file)
        console.print(f"[blue]ℹ[/blue] 从文件读取 {len(raw_urls)} 个链接")
    elif url and not raw_urls:
        raw_urls = [url]

    # 过滤无效链接（搜索页、频道页等）
    before_filter = len(raw_urls)
    raw_urls = filter_video_urls(raw_urls)
    filtered = before_filter - len(raw_urls)
    if filtered:
        console.print(f"[yellow]⚠[/yellow] 过滤掉 {filtered} 个无效链接（搜索页/频道页/无法解析）")

    if not raw_urls:
        console.print("[red]错误：没有有效的视频链接[/red]")
        raise typer.Exit(1)

    # 展开播放列表，生成带目标目录的任务列表
    console.print("[dim]正在解析链接并展开播放列表...[/dim]")
    tasks = _collect_tasks(raw_urls, output)

    # 统计信息
    playlist_tasks = [t for t in tasks if t.output_dir != output]
    single_tasks = [t for t in tasks if t.output_dir == output]
    involved_playlists = len({t.output_dir for t in playlist_tasks})

    console.print(
        f"[dim]共 {len(tasks)} 个视频任务"
        f"（{len(single_tasks)} 个单视频 + {len(playlist_tasks)} 个来自 {involved_playlists} 个播放列表）"
        f"，并发 {max_concurrent}，根目录: {output}[/dim]\n"
    )

    if not tasks:
        console.print("[red]错误：没有有效的视频任务[/red]")
        raise typer.Exit(1)

    # 异步批量下载
    async def _batch():
        semaphore = asyncio.Semaphore(max_concurrent)
        results: List[DownloadResult] = []

        async def _task(task: DownloadTask):
            async with semaphore:
                # 1. 获取元数据（放到线程池，不阻塞事件循环）
                try:
                    meta: VideoMeta = await asyncio.to_thread(fetch_metadata, task.url)
                except Exception as e:
                    console.print(f"[red]✗[/red] 元数据获取失败: {task.url} — {e}")
                    return DownloadResult(
                        video_id="", title=task.url, status="error", error=str(e)
                    )

                # 2. 随机延迟防反爬
                await asyncio.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

                # 3. 下载字幕到对应目录
                if bilingual:
                    res = await download_bilingual_with_delay(meta, task.output_dir)
                else:
                    res = await download_with_delay(meta, task.output_dir, preferred_lang=lang)

                print_result(res)
                return res

        coros = [_task(t) for t in tasks]
        results = await asyncio.gather(*coros)
        return results

    results = asyncio.run(_batch())

    # 生成报告
    success = sum(1 for r in results if r.status == "success")
    report = BatchReport(
        total=len(results),
        success=success,
        failed=len(results) - success,
        results=results,
    )
    print_report(report)

    # 保存 CSV 报告
    report_path = output / "_download_report.csv"
    _write_csv_report(report, report_path)
    console.print(f"\n[dim]报告已保存: {report_path}[/dim]")


def _write_csv_report(report: BatchReport, path: Path):
    """将结果写入 CSV"""
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["video_id", "title", "status", "language", "filepath", "error"])
        for r in report.results:
            writer.writerow([
                r.video_id,
                r.title,
                r.status,
                r.language or "",
                str(r.filepath) if r.filepath else "",
                r.error or "",
            ])


if __name__ == "__main__":
    app()
