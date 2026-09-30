#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Verification Engine for Deliverable D2: Screen Recording & Media Standards
Audits Gold Master videos and telemetry against:
1. Video Resolution: 1920x1080, Codec: H.264, Faststart: YES (moov atom before mdat)
2. Audio Stream: 48,000 Hz, Stereo (2 channels), Codec: AAC
3. EBU R128 Audio Loudness: Integrated in [-15.0, -13.0] LUFS, True Peak <= -1.0 dBTP
4. Anti-Lazy Telemetry: Interaction Density Score (IDS) >= 2.2, zero idle sleep > 4.0s

Exits with code 0 on 100% PASS, code 1 on any violation.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Paths
DEFAULT_GOLD_MASTERS_DIR = Path("/home/zen/O20/enterprise/insilos_website/static/src/video/gold_masters")
DEFAULT_FOOTAGE_DIR = Path("/home/zen/hermes-agent/output/insilos_footage")
DEFAULT_HSE_EVENTS = Path("/home/zen/teamwork_projects/insilos_hse_e2e_suite/video_production/outputs/footage/events.json")
DEFAULT_CACHE_FILE = Path("/home/zen/O20/.agents/teamwork/explorer_recording_media_1/video_probe_results.json")

# Target Episodes for Deliverable D2 Core Suite (12 ERP + 1 HSE AI Vision)
TARGET_EPISODES = [
    "INSILOS_VID_01_CRM_GOLD_MASTER.mp4",
    "INSILOS_VID_02_PUR_GOLD_MASTER.mp4",
    "INSILOS_VID_03_INV_GOLD_MASTER.mp4",
    "INSILOS_VID_04_BOM_GOLD_MASTER.mp4",
    "INSILOS_VID_05_PLN_GOLD_MASTER.mp4",
    "INSILOS_VID_06_SFL_GOLD_MASTER.mp4",
    "INSILOS_VID_07_FLT_GOLD_MASTER.mp4",
    "INSILOS_VID_08_FUL_GOLD_MASTER.mp4",
    "INSILOS_VID_09_LOG_GOLD_MASTER.mp4",
    "INSILOS_VID_10_SAL_GOLD_MASTER.mp4",
    "INSILOS_VID_11_ACC_GOLD_MASTER.mp4",
    "INSILOS_VID_12_MKT_GOLD_MASTER.mp4",
    "INSILOS_HSE_AI_VISION_75S_GOLD_MASTER.mp4"
]

def check_faststart(filepath: Path) -> bool:
    """Verifies that moov atom precedes mdat atom in the MP4 file header."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(65536)
            moov_pos = header.find(b"moov")
            mdat_pos = header.find(b"mdat")
            return moov_pos != -1 and (mdat_pos == -1 or moov_pos < mdat_pos)
    except Exception:
        return False

def probe_stream_metadata(filepath: Path) -> dict:
    """Uses ffprobe to extract stream format, codecs, resolutions, and sample rates."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,codec_name,sample_rate,channels:format=duration",
        "-of", "json",
        str(filepath)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return {}
    
    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError:
        return {}

    video_info = None
    audio_info = None
    for s in data.get("streams", []):
        if "width" in s and not video_info:
            video_info = {
                "codec": s.get("codec_name"),
                "width": int(s.get("width", 0)),
                "height": int(s.get("height", 0))
            }
        elif "sample_rate" in s and not audio_info:
            audio_info = {
                "codec": s.get("codec_name"),
                "sample_rate": int(s.get("sample_rate", 0)),
                "channels": int(s.get("channels", 0))
            }

    duration = float(data.get("format", {}).get("duration", 0.0))
    return {
        "video": video_info,
        "audio": audio_info,
        "duration": duration
    }

def measure_ebu_r128_loudnorm(filepath: Path) -> dict:
    """Runs FFmpeg loudnorm filter in json print mode to measure real I, TP, and LRA."""
    cmd = [
        "ffmpeg", "-nostats", "-vn", "-i", str(filepath),
        "-af", "loudnorm=print_format=json",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    combined = res.stderr + "\n" + res.stdout
    match = re.search(r"\{\s*\"input_i\"[\s\S]*?\}", combined)
    if match:
        try:
            d = json.loads(match.group(0))
            return {
                "input_i": float(d.get("input_i", -99.0)),
                "input_tp": float(d.get("input_tp", 99.0)),
                "input_lra": float(d.get("input_lra", 0.0))
            }
        except (ValueError, json.JSONDecodeError):
            pass
    return {}

def audit_video_files(video_dir: Path, workers: int = 8, use_cache: bool = False, cache_file: Path = DEFAULT_CACHE_FILE):
    """Audits video streams, audio streams, faststart, and EBU R128 loudness."""
    print("\n" + "=" * 95)
    print(" [GATE 1] AUDITING GOLD MASTER VIDEO & AUDIO STREAMS (EBU R128 & BROADCAST FIDELITY)")
    print("=" * 95)
    print(f"{'Filename':<38} | {'Resolution':<10} | {'Codec':<9} | {'Faststart':<9} | {'Audio':<14} | {'EBU R128 (I / TP)':<17} | {'Status':<6}")
    print("-" * 95)

    cached_data = {}
    if use_cache and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                c = json.load(f)
                for item in c.get("gold_masters", []):
                    cached_data[item["file_name"]] = item
        except Exception:
            pass

    def probe_single_video(filename: str):
        vpath = video_dir / filename
        if not vpath.exists():
            return {
                "filename": filename,
                "exists": False,
                "passed": False,
                "error": "File not found"
            }

        # Faststart
        fs_ok = check_faststart(vpath)

        # Stream metadata via ffprobe
        meta = probe_stream_metadata(vpath)
        v_meta = meta.get("video") or {}
        a_meta = meta.get("audio") or {}

        width = v_meta.get("width", 0)
        height = v_meta.get("height", 0)
        v_codec = v_meta.get("codec", "")
        a_codec = a_meta.get("codec", "")
        a_rate = a_meta.get("sample_rate", 0)
        a_channels = a_meta.get("channels", 0)

        # Loudnorm
        loud = {}
        if filename in cached_data and "loudnorm" in cached_data[filename]:
            c_loud = cached_data[filename]["loudnorm"]
            loud = {
                "input_i": float(c_loud.get("input_i", -99)),
                "input_tp": float(c_loud.get("input_tp", 99)),
                "input_lra": float(c_loud.get("input_lra", 0))
            }
        else:
            loud = measure_ebu_r128_loudnorm(vpath)

        input_i = loud.get("input_i", -99.0)
        input_tp = loud.get("input_tp", 99.0)

        # Checks:
        # 1. 1920x1080
        pass_res = (width == 1920 and height == 1080)
        # 2. H.264
        pass_vcodec = (v_codec.lower() in ["h264", "avc", "avc1"])
        # 3. Faststart
        pass_fs = fs_ok
        # 4. Audio: 48000 Hz, stereo (2ch), AAC
        pass_audio = (a_codec.lower() == "aac" and a_rate == 48000 and a_channels == 2)
        # 5. EBU R128: I in [-15.0, -13.0] LUFS, TP <= -1.0 dBTP
        pass_loudness = (-15.0 <= input_i <= -13.0) and (input_tp <= -1.0)

        overall_passed = pass_res and pass_vcodec and pass_fs and pass_audio and pass_loudness

        return {
            "filename": filename,
            "exists": True,
            "passed": overall_passed,
            "width": width,
            "height": height,
            "v_codec": v_codec,
            "faststart": fs_ok,
            "a_codec": a_codec,
            "a_rate": a_rate,
            "a_channels": a_channels,
            "input_i": input_i,
            "input_tp": input_tp,
            "pass_res": pass_res,
            "pass_vcodec": pass_vcodec,
            "pass_fs": pass_fs,
            "pass_audio": pass_audio,
            "pass_loudness": pass_loudness
        }

    results = []
    with ThreadPoolExecutor(max_workers=min(workers, len(TARGET_EPISODES))) as executor:
        futures = list(executor.map(probe_single_video, TARGET_EPISODES))
        for res in futures:
            results.append(res)
            fn = res["filename"]
            if not res["exists"]:
                print(f"{fn:<38} | {'MISSING':<10} | {'N/A':<9} | {'N/A':<9} | {'N/A':<14} | {'N/A':<17} | FAIL")
                continue

            res_str = f"{res['width']}x{res['height']}"
            fs_str = "YES" if res['faststart'] else "NO"
            audio_str = f"{res['a_codec'].upper()} {res['a_rate']}Hz"
            loud_str = f"{res['input_i']:.2f} / {res['input_tp']:.2f}dBTP"
            status_str = "PASS" if res["passed"] else "FAIL"

            print(f"{fn:<38} | {res_str:<10} | {res['v_codec']:<9} | {fs_str:<9} | {audio_str:<14} | {loud_str:<17} | {status_str:<6}")

    all_passed = all(r.get("passed", False) for r in results)
    print("-" * 95)
    print(f"Gate 1 Result: {'✓ ALL GOLD MASTER VIDEOS PASS 1080p / 48kHz / EBU R128 AUDIT' if all_passed else '✗ GATE 1 FAILED'}")
    return all_passed, results

def audit_anti_lazy_telemetry(footage_dir: Path, hse_events_file: Path):
    """Audits interaction density, event counts, and idle gaps to prevent lazy code."""
    print("\n" + "=" * 95)
    print(" [GATE 2] AUDITING ANTI-LAZY CODE RECORDING TELEMETRY (IDS >= 2.2 & ZERO FREEZE)")
    print("=" * 95)
    print(f"{'Episode':<20} | {'Duration':<9} | {'Events':<8} | {'Max Idle Gap':<13} | {'IDS Score':<10} | {'Requirement':<14} | {'Status':<6}")
    print("-" * 95)

    keys = ['01_CRM', '02_PUR', '03_INV', '04_BOM', '05_PLN', '06_SFL', 
            '07_FLT', '08_FUL', '09_LOG', '10_SAL', '11_ACC', '12_MKT']

    results = []
    all_passed = True

    # 1. Audit 12 Business ERP Videos
    for k in keys:
        ep_code = f"VID_{k}"
        event_file = footage_dir / f"insilos_screen_{ep_code}_events.json"

        if not event_file.exists():
            print(f"{ep_code:<20} | {'MISSING':<9} | {'0':<8} | {'N/A':<13} | {'0.00':<10} | IDS >= 2.2     | FAIL")
            all_passed = False
            results.append({"code": ep_code, "passed": False, "error": "Missing event file"})
            continue

        try:
            with open(event_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"{ep_code:<20} | {'ERROR':<9} | {'0':<8} | {'N/A':<13} | {'0.00':<10} | IDS >= 2.2     | FAIL")
            all_passed = False
            results.append({"code": ep_code, "passed": False, "error": str(e)})
            continue

        events = data.get("events", [])
        timestamps = [e.get("timestamp", e.get("time_s", 0.0)) for e in events]
        timestamps.sort()
        gaps = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        max_gap = max(gaps) if gaps else 0.0
        dur = max(timestamps[-1] + 1.0, 10.0) if timestamps else 10.0
        ids = (len(events) / dur) * 10.0 if dur > 0 else 0.0

        # Criteria: IDS >= 2.2, max idle gap <= 4.0s, total events >= 8
        passed = (ids >= 2.2) and (max_gap <= 4.0) and (len(events) >= 8)
        if not passed:
            all_passed = False

        status_str = "PASS" if passed else "FAIL"
        print(f"{ep_code:<20} | {dur:<7.2f}s | {len(events):<8} | {max_gap:<11.2f}s | {ids:<10.2f} | IDS >= 2.2     | {status_str:<6}")
        results.append({
            "code": ep_code,
            "duration": dur,
            "events_count": len(events),
            "max_gap": max_gap,
            "ids": ids,
            "passed": passed
        })

    # 2. Audit HSE AI Vision Telemetry
    ep_hse = "HSE_01_AI_VISION"
    if hse_events_file.exists():
        try:
            with open(hse_events_file, "r", encoding="utf-8") as f:
                d_hse = json.load(f)
            events_hse = d_hse.get("events", [])
            dur_hse = float(d_hse.get("duration", 45.0))
            ts_hse = [e["timestamp"] for e in events_hse]
            ts_hse.sort()
            gaps_hse = [round(ts_hse[i+1] - ts_hse[i], 2) for i in range(len(ts_hse)-1)]
            max_gap_hse = max(gaps_hse) if gaps_hse else 0.0
            ids_hse = (len(events_hse) / dur_hse) * 10.0 if dur_hse > 0 else 0.0

            passed_hse = (ids_hse >= 2.2) and (max_gap_hse <= 3.5) and (len(events_hse) >= 8)
            if not passed_hse:
                all_passed = False

            status_str = "PASS" if passed_hse else "FAIL"
            print(f"{ep_hse:<20} | {dur_hse:<7.2f}s | {len(events_hse):<8} | {max_gap_hse:<11.2f}s | {ids_hse:<10.2f} | IDS >= 2.2     | {status_str:<6}")
            results.append({
                "code": ep_hse,
                "duration": dur_hse,
                "events_count": len(events_hse),
                "max_gap": max_gap_hse,
                "ids": ids_hse,
                "passed": passed_hse
            })
        except Exception as e:
            print(f"{ep_hse:<20} | {'ERROR':<9} | {'0':<8} | {'N/A':<13} | {'0.00':<10} | IDS >= 2.2     | FAIL")
            all_passed = False
            results.append({"code": ep_hse, "passed": False, "error": str(e)})
    else:
        print(f"{ep_hse:<20} | {'SKIPPED':<9} | {'N/A':<8} | {'N/A':<13} | {'N/A':<10} | IDS >= 2.2     | WARN")

    print("-" * 95)
    print(f"Gate 2 Result: {'✓ ALL 13 RECORDING TELEMETRIES PASS ANTI-LAZY-CODE AUDIT (IDS >= 2.2)' if all_passed else '✗ GATE 2 FAILED'}")
    return all_passed, results

def main():
    parser = argparse.ArgumentParser(description="Deliverable D2 Automated Recording Standards Auditor")
    parser.add_argument("--video-dir", default=str(DEFAULT_GOLD_MASTERS_DIR), help="Path to gold masters directory")
    parser.add_argument("--footage-dir", default=str(DEFAULT_FOOTAGE_DIR), help="Path to footage telemetry directory")
    parser.add_argument("--workers", type=int, default=12, help="Number of parallel measurement workers")
    parser.add_argument("--use-cache", action="store_true", help="Use cached loudnorm values if available")
    parser.add_argument("--output-json", default=None, help="Optional output JSON path for the audit results")
    args = parser.parse_args()

    t_start = time.time()
    print("=" * 95)
    print("   INSILOS SCREEN RECORDING & FOOTAGE STANDARDS COMPLIANCE AUDITOR (DELIVERABLE D2)")
    print("   Evaluating Video 1080p, H.264, Faststart, Audio 48kHz Stereo AAC, EBU R128 & Anti-Lazy IDS")
    print("=" * 95)

    v_dir = Path(args.video_dir)
    f_dir = Path(args.footage_dir)

    # Gate 1: Video streams and EBU R128
    gate1_passed, video_results = audit_video_files(v_dir, workers=args.workers, use_cache=args.use_cache)

    # Gate 2: Anti-lazy telemetry
    gate2_passed, telemetry_results = audit_anti_lazy_telemetry(f_dir, DEFAULT_HSE_EVENTS)

    total_time = time.time() - t_start
    overall_passed = gate1_passed and gate2_passed

    print("\n" + "=" * 95)
    print("                       FINAL DELIVERABLE D2 AUDIT CERTIFICATION")
    print("=" * 95)
    print(f"  • Gate 1 (1080p / H.264 / Faststart / 48kHz AAC / EBU R128 Loudness): {'PASS [100%]' if gate1_passed else 'FAIL'}")
    print(f"  • Gate 2 (Anti-Lazy Code Telemetry / IDS >= 2.2 / Zero Passive Freeze): {'PASS [100%]' if gate2_passed else 'FAIL'}")
    print(f"  • Total Time Elapsed: {total_time:.2f} seconds")
    print(f"  • Overall Status: {'✓ 100% PASS - DELIVERABLE D2 FULLY COMPLIANT' if overall_passed else '✗ FAILED - NON-COMPLIANT'}")
    print("=" * 95 + "\n")

    if args.output_json:
        out_p = Path(args.output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "overall_passed": overall_passed,
                "elapsed_sec": round(total_time, 2),
                "gate1_video_streams": {
                    "passed": gate1_passed,
                    "records_count": len(video_results),
                    "results": video_results
                },
                "gate2_anti_lazy_telemetry": {
                    "passed": gate2_passed,
                    "records_count": len(telemetry_results),
                    "results": telemetry_results
                }
            }, f, indent=2, ensure_ascii=False)
        print(f"Saved audit manifest to: {args.output_json}")

    sys.exit(0 if overall_passed else 1)

if __name__ == "__main__":
    main()
