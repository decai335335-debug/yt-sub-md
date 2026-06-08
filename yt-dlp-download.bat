@echo off
cd /d "E:/GitHubDownloads/kimi/yt-sub-md"
echo [YouTube Subtitle Download via yt-dlp]
echo Output: E:/Obsidian/Ö÷²Ö¿â/11-subtitles/Youtube
echo.
echo Paste YouTube URLs (one per line, empty line to finish):
echo --------------------------------------------------
set /p urls="URLs (space-separated): "
echo.
"e:/gitÏîÄ¿/.venv/Scripts/python.exe" download_yt.py %urls%
echo.
echo Done.
pause
