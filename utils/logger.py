"""Rich 控制台日志"""
import urllib.parse

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from config import OBSIDIAN_VAULT_NAME, OBSIDIAN_VAULT_ROOT

console = Console(force_terminal=True)


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]YouTube 字幕批量下载器[/bold cyan]\n"
        "[dim]Markdown 输出 · 无时间轴 · 原语言优先[/dim]",
        border_style="cyan",
    ))


def print_result(result):
    """打印单条结果"""
    if result.status == "success":
        console.print(f"[green]✓[/green] {result.title[:50]} → [dim]{result.language}[/dim]")
    else:
        console.print(f"[red]✗[/red] {result.title[:50]} — [yellow]{result.error}[/yellow]")


def print_report(report):
    """打印批次统计 + 可点击文件列表"""
    table = Table(title="下载报告", show_header=True, header_style="bold magenta")
    table.add_column("状态", style="bold")
    table.add_column("数量", justify="right")
    table.add_column("比例")

    total = report.total
    table.add_row("[green]成功", str(report.success), f"{report.success/total*100:.1f}%")
    table.add_row("[red]失败", str(report.failed), f"{report.failed/total*100:.1f}%")
    table.add_row("总计", str(total), "100.0%")

    console.print()
    console.print(table)

    # Obsidian 可点击文件列表
    success_results = [r for r in report.results if r.status == "success" and r.filepath]
    if success_results:
        file_table = Table(title="下载结果")
        file_table.add_column("视频", style="green")
        file_table.add_column("文件路径")
        for r in success_results:
            try:
                rel_path = r.filepath.relative_to(OBSIDIAN_VAULT_ROOT).with_suffix('')
                rel_path_str = str(rel_path).replace('\\', '/')
                vault = urllib.parse.quote(OBSIDIAN_VAULT_NAME)
                file = urllib.parse.quote(rel_path_str, safe='/')
                obsidian_url = f"obsidian://open?vault={vault}&file={file}"
                path_text = Text(r.filepath.name, style=f"link {obsidian_url}")
            except ValueError:
                file_link = r.filepath.parent.resolve().as_uri()
                path_text = Text(r.filepath.name, style=f"link {file_link}")
            file_table.add_row(r.title or "-", path_text)
        console.print()
        console.print(file_table)
