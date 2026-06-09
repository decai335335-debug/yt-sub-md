"""全局配置"""
from pathlib import Path

# 默认输出目录（你的 Obsidian 仓库）
DEFAULT_OUTPUT_DIR = Path("E:/Obsidian/主仓库/11-subtitles")

# Obsidian Vault 配置（用于生成 obsidian:// 可点击链接）
OBSIDIAN_VAULT_ROOT = Path("E:/Obsidian/主仓库")
OBSIDIAN_VAULT_NAME = "主仓库"

# 并发与限速
MAX_CONCURRENT = 5
REQUEST_DELAY_MIN = 1.0
REQUEST_DELAY_MAX = 3.0

# 重试
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_MIN = 2
RETRY_BACKOFF_MAX = 10

# 文件名安全映射（Windows 保留字符）
FILENAME_BAD_CHARS = '\\/:*?"<>|'
