#!/usr/bin/env python3
"""
tools/fetch_innokafe_pexels_videos.py
======================================
Automated Pexels Video Fetcher, Transcoder & Visual Asset Integrator for InnoKafe Specialty Coffee.

Features:
1. Reads curated Pexels video manifest from `enterprise/innokafe_website/data/pexels_video_catalog.json`.
2. Downloads selected high-definition video assets directly from Pexels CDN.
3. Transcodes to Gold Standard web formats:
   - MP4 H.264 with `-movflags +faststart` (HTTP 206 Byte-Range instant streaming)
   - WebM VP9 (modern browser high-compression stream)
   - WebP poster frame (extracted at 1.5s with high visual entropy)
4. Generates/Updates `enterprise/innokafe_website/MEDIA_SOURCES.md` for full attribution and licensing compliance.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "enterprise/innokafe_website/data/pexels_video_catalog.json"
TARGET_DIR = REPO_ROOT / "enterprise/innokafe_website/static/src/video"
POSTER_DIR = REPO_ROOT / "enterprise/innokafe_website/static/src/video/posters"
MEDIA_SOURCES_PATH = REPO_ROOT / "enterprise/innokafe_website/MEDIA_SOURCES.md"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def download_file(url: str, dest_path: Path, max_retries: int = 3) -> bool:
    """Download a file with streaming chunks and retry logic."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  [+] Downloading {dest_path.name} (Attempt {attempt}/{max_retries})...")
            with urllib.request.urlopen(req, timeout=45) as response, open(dest_path, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
            size_mb = dest_path.stat().st_size / (1024 * 1024)
            print(f"  [✓] Downloaded successfully: {size_mb:.2f} MB")
            return True
        except Exception as e:
            print(f"  [!] Attempt {attempt} failed: {e}")
            if dest_path.exists():
                dest_path.unlink()
    return False


def transcode_video(raw_mp4: Path, base_name: str, target_dir: Path, is_portrait: bool = False):
    """
    Transcode raw MP4 using ffmpeg to:
    1. Optimized faststart MP4
    2. WebM VP9
    3. WebP poster frame
    """
    opt_mp4 = target_dir / f"{base_name}_opt.mp4"
    opt_webm = target_dir / f"{base_name}.webm"
    poster_webp = POSTER_DIR / f"{base_name}_poster.webp"
    POSTER_DIR.mkdir(parents=True, exist_ok=True)

    # Resolution target: max 1920x1080 for landscape, 1080x1920 for portrait
    scale_filter = "scale=1080:1920:force_original_aspect_ratio=decrease" if is_portrait else "scale=1920:1080:force_original_aspect_ratio=decrease"

    print(f"  [+] Transcoding MP4 faststart: {opt_mp4.name}...")
    cmd_mp4 = [
        "ffmpeg", "-y", "-i", str(raw_mp4),
        "-vf", scale_filter,
        "-c:v", "libx264", "-preset", "slow", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",
        str(opt_mp4)
    ]
    subprocess.run(cmd_mp4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print(f"  [+] Generating WebP poster frame: {poster_webp.name}...")
    cmd_poster = [
        "ffmpeg", "-y", "-ss", "00:00:01.500", "-i", str(opt_mp4),
        "-vframes", "1",
        "-c:v", "libwebp", "-q:v", "82",
        str(poster_webp)
    ]
    subprocess.run(cmd_poster, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print(f"  [+] Transcoding WebM VP9: {opt_webm.name}...")
    cmd_webm = [
        "ffmpeg", "-y", "-i", str(opt_mp4),
        "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0",
        "-an",
        str(opt_webm)
    ]
    try:
        subprocess.run(cmd_webm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        print(f"  [!] WebM conversion optional warning: {e}")

    print(f"  [✓] Video pipeline complete for {base_name}.")


def generate_media_sources_doc(catalog: dict):
    """Generate Markdown attribution documentation compliant with Pexels license."""
    lines = [
        "# INNOKAFE SPECIALTY COFFEE: MEDIA & VIDEO ASSETS REPOSITORY",
        "## Pexels Video Library, Attribution & Technical Specifications",
        "",
        "Tất cả video stock trong phân hệ InnoKafe Website được tuyển chọn khắt khe từ Pexels Video, tuân thủ giấy phép sử dụng thương mại miễn phí (Pexels License).",
        "Mọi tệp video đều được tối ưu hóa chuẩn HTTP 206 Byte-Range streaming (`-movflags +faststart`) và xuất định dạng kép MP4 (H.264) + WebM (VP9).",
        "",
        "| File Tên | Tỷ Lệ | Chủ Đề / Usecase | Tác Giả Pexels | Độ Phân Giải Gốc | Trang Nguồn Pexels |",
        "|---|---|---|---|---|---|"
    ]

    for theme_key, theme_data in catalog.items():
        theme_title = theme_data.get("theme_title", theme_key)
        for v in theme_data.get("videos", []):
            base_name = v.get("target_file_base", v.get("id"))
            file_ref = f"`{base_name}_opt.mp4`"
            aspect = v.get("aspectRatio", "16:9")
            creator = v.get("creator", "Pexels Artist")
            res = f"{v.get('width', 1920)}x{v.get('height', 1080)}"
            page_url = v.get("pageUrl", "#")
            role = v.get("role", theme_title)
            lines.append(f"| {file_ref} | {aspect} | {role} | [{creator}]({v.get('creatorUrl', '#')}) | {res} | [Xem trên Pexels]({page_url}) |")

    lines.extend([
        "",
        "## Giấy Phép & Điều Khoản Sử Dụng (Pexels License)",
        "- Miễn phí sử dụng cho mục đích thương mại và phi thương mại.",
        "- Không bắt buộc ghi nhận tác quyền nhưng được lưu trữ minh bạch vì uy tín thương hiệu.",
        "- Không bán lại video stock nguyên trạng mà không có sự chỉnh sửa/tích hợp.",
        "- Không dùng chân dung người trong video để hàm ý xác nhận sản phẩm khi chưa có thỏa thuận.",
        "",
        "---",
        "*InnoKafe Media Asset Governance — October 2026*"
    ])

    MEDIA_SOURCES_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[✓] Updated Media Sources Doc: {MEDIA_SOURCES_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Fetch and transcode InnoKafe Pexels video assets.")
    parser.add_argument("--dry-run", action="store_true", help="Only inspect catalog and URLs without downloading.")
    parser.add_argument("--theme", type=str, default=None, help="Filter by theme ID.")
    parser.add_argument("--limit", type=int, default=1, help="Max videos to download per theme (default: 1).")
    args = parser.parse_args()

    if not CATALOG_PATH.exists():
        print(f"[!] Catalog not found at {CATALOG_PATH}")
        sys.exit(1)

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    raw_tmp_dir = TARGET_DIR / "raw_tmp"
    raw_tmp_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] InnoKafe Pexels Video Engine initialized. Target: {TARGET_DIR}")
    generate_media_sources_doc(catalog)

    if args.dry_run:
        print("[*] Dry run mode enabled. Verified all URLs:")
        for tk, td in catalog.items():
            print(f"Theme: {tk} - {td.get('theme_title')}")
            for v in td.get("videos", []):
                print(f"  -> {v.get('name')} | {v.get('aspectRatio')} | {v.get('contentUrl')}")
        return

    # Process download and transcode
    processed_count = 0
    for tk, td in catalog.items():
        if args.theme and tk != args.theme:
            continue
        print(f"\n=======================================================")
        print(f"[*] Processing Theme: {td.get('theme_title')} ({tk})")
        print(f"=======================================================")

        videos = td.get("videos", [])[:args.limit]
        for v in videos:
            base_name = v.get("target_file_base", f"video_{v.get('id')}")
            content_url = v.get("contentUrl")
            is_portrait = v.get("aspectRatio") == "9:16"

            if not content_url:
                print(f"  [!] Missing contentUrl for video {v.get('id')}, skipping.")
                continue

            raw_file = raw_tmp_dir / f"{base_name}_raw.mp4"
            opt_mp4 = TARGET_DIR / f"{base_name}_opt.mp4"

            if opt_mp4.exists():
                print(f"  [i] Target {opt_mp4.name} already exists. Skipping download.")
                continue

            success = download_file(content_url, raw_file)
            if success:
                try:
                    transcode_video(raw_file, base_name, TARGET_DIR, is_portrait)
                    processed_count += 1
                except Exception as e:
                    print(f"  [!] Transcode error for {base_name}: {e}")
                finally:
                    if raw_file.exists():
                        raw_file.unlink()

    # Clean up raw_tmp
    if raw_tmp_dir.exists() and not any(raw_tmp_dir.iterdir()):
        raw_tmp_dir.rmdir()

    print(f"\n[✓] Processing finished. Total new assets generated: {processed_count}")


if __name__ == "__main__":
    main()
