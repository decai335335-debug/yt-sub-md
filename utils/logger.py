"""Rich 控制台日志"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


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
    """打印批次统计"""
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
