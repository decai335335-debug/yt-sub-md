#!/usr/bin/env python3
"""使用 yt-dlp 获取 YouTube 字幕 URL，用 requests 下载并转为 Markdown"""
import sys
import json
from pathlib import Path

import requests
import yt_dlp

OUTPUT_DIR = Path("E:/Obsidian/主仓库/11-subtitles/Youtube")

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.youtube.com/",
}


def get_subtitle_data(url: str):
    """用 yt-dlp 获取视频信息和字幕列表"""
    opts = {"skip_download": True, "quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    manual = info.get("subtitles", {})
    auto = info.get("automatic_captions", {})

    # 优先策略：中文(手动) > 英文(手动) > 中文(自动) > 英文(自动) > 其他
    priority = [("zh-CN", manual), ("zh-Hans", manual), ("zh", manual),
                ("en", manual), ("en-US", manual), ("en-GB", manual),
                ("zh-CN", auto), ("zh-Hans", auto), ("zh", auto),
                ("en", auto), ("en-US", auto), ("en-GB", auto),
                ("ja", manual), ("ja", auto), ("ko", manual), ("ko", auto)]

    chosen_lang = None
    chosen_tracks = None
    chosen_kind = None

    for lang, src in priority:
        if lang in src and src[lang]:
            chosen_lang = lang
            chosen_tracks = src[lang]
            chosen_kind = "manual" if src is manual else "auto"
            break

    if not chosen_tracks:
        all_tracks = {**manual, **auto}
        if not all_tracks:
            return None, "无可用字幕"
        chosen_lang = list(all_tracks.keys())[0]
        chosen_tracks = all_tracks[chosen_lang]
        chosen_kind = "manual" if chosen_lang in manual else "auto"

    # 优先选 json3 / srv3 格式（YouTube 原生 JSON，解析最准）
    track = None
    for t in chosen_tracks:
        if t.get("ext") in ("json3", "srv3"):
            track = t
            break
    if not track:
        for t in chosen_tracks:
            if t.get("ext") in ("vtt", "srt"):
                track = t
                break
    if not track:
        track = chosen_tracks[0]

    # 下载字幕原始内容
    sub_url = track["url"]
    resp = requests.get(sub_url, headers=BROWSER_HEADERS, timeout=30)
    resp.raise_for_status()

    return {
        "video_id": info["id"],
        "title": info.get("title", "Unknown"),
        "channel": info.get("channel") or info.get("uploader", "Unknown"),
        "url": url,
        "lang": chosen_lang,
        "kind": chosen_kind,
        "raw": resp.text,
        "ext": track.get("ext", ""),
    }, None


def parse_subtitle(data: dict):
    """根据格式解析字幕"""
    ext = data["ext"]
    text = data["raw"]

    if ext in ("json3", "srv3"):
        return parse_json3(text)
    elif ext in ("vtt", "srt"):
        return parse_vtt(text)
    elif ext in ("ttml", "xml"):
        return parse_xml(text)
    else:
        try:
            return parse_json3(text)
        except Exception:
            return parse_vtt(text)


def parse_json3(text):
    data = json.loads(text)
    events = data.get("events", [])
    result = []
    for event in events:
        t = event.get("tStartMs", 0)
        d = event.get("dDurationMs", 5000)
        segs = event.get("segs", [])
        parts = [s["utf8"] for s in segs if "utf8" in s]
        content = "".join(parts).replace("\n", " ").strip()
        if content:
            result.append({"start": t / 1000, "end": (t + d) / 1000, "text": content})
    return result


def parse_vtt(text):
    result = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "-->" in line:
            times = line.split("-->")
            start = _parse_time(times[0].strip())
            end = _parse_time(times[1].strip().split()[0])
            i += 1
            parts = []
            while i < len(lines) and lines[i].strip():
                parts.append(lines[i].strip())
                i += 1
            content = " ".join(parts)
            if content:
                result.append({"start": start, "end": end, "text": content})
        i += 1
    return result


def parse_xml(text):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(text)
    result = []
    for elem in root.iter():
        if elem.tag in ("p", "text"):
            start = float(elem.get("t", 0)) / 1000
            dur = float(elem.get("d", 5000)) / 1000
            txt = (elem.text or "").strip()
            if txt:
                result.append({"start": start, "end": start + dur, "text": txt})
    return result


def _parse_time(t):
    parts = t.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(t)


def build_md(meta, segments):
    lines = [
        "---",
        f"title: {meta['title']}",
        f"url: {meta['url']}",
        f"video_id: {meta['video_id']}",
        f"channel: {meta['channel']}",
        f"subtitle_lang: {meta['lang']} ({meta['kind']})",
        "---",
        "",
        f"# {meta['title']}",
        "",
    ]
    for seg in segments:
        t = _format_time(seg["start"])
        lines.append(f"**[{t}]** {seg['text']}")
    lines.append("")
    return "\n".join(lines)


def _format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def _safe_name(s):
    for c in '\\/:*?"<>|':
        s = s.replace(c, "_")
    return s.strip()[:80] or "video"


def main():
    urls = sys.argv[1:]
    if not urls:
        print("用法: python download_yt.py <YouTube URL> [URL2] ...")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    success = 0
    fail = 0

    for url in urls:
        print(f"\n处理: {url}")
        try:
            data, err = get_subtitle_data(url)
            if err:
                print(f"  ✗ {err}")
                fail += 1
                continue

            segments = parse_subtitle(data)
            if not segments:
                print(f"  ✗ 字幕内容为空")
                fail += 1
                continue

            md = build_md(data, segments)
            fname = _safe_name(data["title"]) + ".md"
            fpath = OUTPUT_DIR / fname
            fpath.write_text(md, encoding="utf-8")
            print(f"  ✓ 已保存: {fname} ({len(segments)} 行)")
            success += 1
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            fail += 1

    print(f"\n{'='*40}")
    print(f"成功: {success} | 失败: {fail}")
    print(f"输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
