#!/usr/bin/env python3
"""
Adversarial Media & Stream Integrity Audit Engine (Challenger 2)
Insilos Senior Expert Council Website Performance Audit & Optimization Campaign

Conducts empirical adversarial verification on all media assets in:
  enterprise/insilos_website/static/src/video/
  enterprise/insilos_website/static/src/img/

Pillars:
  1. MP4 Binary Container Stress Probe:
     - Parses top-level ISO BMFF box headers.
     - Verifies moov precedes mdat in 100% of MP4 files.
     - Verifies byte offset of moov is within first 1024 bytes.
     - Simulates HTTP Range request (bytes=0-1024) to verify instant metadata readability (mvhd parsed).
  2. Audio Integrity & EBU R128 Audit:
     - 13 Gold Master videos: Integrated loudness in [-15.0, -13.0] LUFS, True Peak <= -1.0 dBTP,
       AAC 48,000 Hz stereo (2 channels).
     - hero_act3_datacenter.mp4: Exactly 0 audio streams (ffprobe).
  3. Poster Size & Visual Quality Audit:
     - 139 poster WebP files: file size strictly < 80.0 KB (0 < size < 80 KB).
     - Pillow decode test & Shannon entropy check (asserts valid non-corrupted images).
  4. SVG Security & Validity Audit:
     - 57 SVG files: Valid XML via xml.etree.ElementTree, 0 malformed tags,
       0 <script> tags, 0 inline event attributes, 0 javascript: URIs,
       0 XXE entity definitions, 0 XML comments.
"""

import os
import sys
import math
import json
import struct
import subprocess
import re
import concurrent.futures
from PIL import Image
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VIDEO_DIR = os.path.join(REPO_ROOT, "enterprise/insilos_website/static/src/video")
IMG_DIR = os.path.join(REPO_ROOT, "enterprise/insilos_website/static/src/img")
GOLD_VIDEO_DIR = os.path.join(VIDEO_DIR, "gold_masters")
GOLD_IMG_DIR = os.path.join(IMG_DIR, "gold_masters")
ARTIFACTS_DIR = os.path.join(REPO_ROOT, "tools/test_artifacts_challenger_media")

GOLD_MASTERS = [
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

def audit_single_mp4(filepath):
    rel_path = os.path.relpath(filepath, REPO_ROOT)
    fname = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    # 1. Parse full box hierarchy
    boxes = []
    moov_offset = None
    mdat_offset = None
    with open(filepath, "rb") as fp:
        offset = 0
        while offset < file_size:
            hdr = fp.read(8)
            if len(hdr) < 8:
                break
            sz, name = struct.unpack(">I4s", hdr)
            name_str = name.decode("latin1", errors="ignore")
            current_offset = offset
            
            if sz == 1:
                sz64 = fp.read(8)
                actual_sz = struct.unpack(">Q", sz64)[0]
                box_len = actual_sz
            elif sz == 0:
                box_len = file_size - current_offset
            else:
                box_len = sz
            
            boxes.append((name_str, current_offset, box_len))
            if name_str == "moov" and moov_offset is None:
                moov_offset = current_offset
            elif name_str == "mdat" and mdat_offset is None:
                mdat_offset = current_offset

            offset += box_len
            fp.seek(offset)

    box_names = [b[0] for b in boxes]
    moov_precedes_mdat = (moov_offset is not None and mdat_offset is not None and moov_offset < mdat_offset)
    moov_within_1kb = (moov_offset is not None and moov_offset < 1024)

    # 2. Simulate HTTP Range Request: bytes=0-1024 (1025 bytes slice)
    with open(filepath, "rb") as fp:
        range_chunk = fp.read(1025)
    
    # Parse what streaming client sees in first chunk
    chunk_boxes = []
    chunk_offset = 0
    mvhd_readable = False
    duration_timescale = None

    while chunk_offset + 8 <= len(range_chunk):
        sz, name = struct.unpack(">I4s", range_chunk[chunk_offset:chunk_offset+8])
        name_str = name.decode("latin1", errors="ignore")
        chunk_boxes.append((name_str, chunk_offset, sz))
        if name_str == "moov":
            # inspect internal box mvhd
            moov_inner = chunk_offset + 8
            if moov_inner + 8 <= len(range_chunk):
                sub_sz, sub_name = struct.unpack(">I4s", range_chunk[moov_inner:moov_inner+8])
                sub_name_str = sub_name.decode("latin1", errors="ignore")
                if sub_name_str == "mvhd":
                    mvhd_readable = True
                    # mvhd payload contains version, timespec
                    mvhd_hdr = range_chunk[moov_inner+8:moov_inner+sub_sz]
                    if len(mvhd_hdr) >= 20:
                        version = mvhd_hdr[0]
                        if version == 0 and len(mvhd_hdr) >= 20:
                            timescale = struct.unpack(">I", mvhd_hdr[12:16])[0]
                            duration = struct.unpack(">I", mvhd_hdr[16:20])[0]
                            duration_timescale = (timescale, duration)
            break
        if sz == 1 or sz == 0:
            break
        chunk_offset += sz

    passed = (moov_precedes_mdat and moov_within_1kb and mvhd_readable)
    return {
        "file": fname,
        "rel_path": rel_path,
        "file_size": file_size,
        "boxes": [b[0] for b in boxes],
        "moov_offset": moov_offset,
        "mdat_offset": mdat_offset,
        "moov_precedes_mdat": moov_precedes_mdat,
        "moov_within_1kb": moov_within_1kb,
        "range_0_1024_mvhd_readable": mvhd_readable,
        "duration_timescale": duration_timescale,
        "passed": passed
    }

def audit_single_gold_audio(fname):
    filepath = os.path.join(GOLD_VIDEO_DIR, fname)
    rel_path = os.path.relpath(filepath, REPO_ROOT)

    # 1. ffprobe stream check
    probe_cmd = ["ffprobe", "-v", "error", "-show_streams", "-select_streams", "a", "-of", "json", filepath]
    probe_out = json.loads(subprocess.check_output(probe_cmd).decode())
    streams = probe_out.get("streams", [])
    if len(streams) != 1:
        return {
            "file": fname,
            "rel_path": rel_path,
            "error": f"Expected 1 audio stream, found {len(streams)}",
            "passed": False
        }
    
    astream = streams[0]
    codec = astream.get("codec_name")
    sample_rate = int(astream.get("sample_rate", 0))
    channels = int(astream.get("channels", 0))

    # 2. ffmpeg loudnorm
    cmd = ["ffmpeg", "-i", filepath, "-af", "loudnorm=print_format=json", "-f", "null", "-"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    idx = res.stderr.rfind("[Parsed_loudnorm_")
    sub = res.stderr[idx:]
    b1 = sub.find("{")
    b2 = sub.find("}", b1)
    metrics = json.loads(sub[b1:b2+1])
    
    input_i = float(metrics["input_i"])
    input_tp = float(metrics["input_tp"])
    input_lra = float(metrics["input_lra"])
    input_thresh = float(metrics.get("input_thresh", -24.0))

    loudness_pass = (-15.0 <= input_i <= -13.0)
    tp_pass = (input_tp <= -1.0)
    sr_pass = (sample_rate == 48000)
    ch_pass = (channels == 2)
    codec_pass = (codec == "aac")

    all_pass = (loudness_pass and tp_pass and sr_pass and ch_pass and codec_pass)

    return {
        "file": fname,
        "rel_path": rel_path,
        "codec": codec,
        "sample_rate": sample_rate,
        "channels": channels,
        "integrated_lufs": input_i,
        "true_peak_dbtp": input_tp,
        "loudness_range_lu": input_lra,
        "loudness_pass": loudness_pass,
        "true_peak_pass": tp_pass,
        "sample_rate_pass": sr_pass,
        "channels_pass": ch_pass,
        "codec_pass": codec_pass,
        "passed": all_pass
    }

def audit_datacenter_audio_zero():
    dc_path = os.path.join(VIDEO_DIR, "hero_act3_datacenter.mp4")
    probe_cmd = ["ffprobe", "-v", "error", "-show_streams", "-select_streams", "a", "-of", "json", dc_path]
    probe_out = json.loads(subprocess.check_output(probe_cmd).decode())
    audio_streams = probe_out.get("streams", [])
    passed = (len(audio_streams) == 0)
    return {
        "file": "hero_act3_datacenter.mp4",
        "audio_stream_count": len(audio_streams),
        "passed": passed
    }

def audit_single_poster(filepath):
    rel_path = os.path.relpath(filepath, REPO_ROOT)
    fname = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)
    file_size_kb = file_size / 1024.0

    size_pass = (0 < file_size_kb < 80.0)
    decode_pass = False
    entropy = 0.0
    width = 0
    height = 0
    mode = ""

    try:
        with Image.open(filepath) as img:
            img.verify()
        with Image.open(filepath) as img:
            img.load()
            width, height = img.size
            mode = img.mode
            format_name = img.format
            hist = img.histogram()
            total_pixels = sum(hist)
            if total_pixels > 0:
                entropy = -sum((c / total_pixels) * math.log2(c / total_pixels) for c in hist if c > 0)
            decode_pass = (format_name == "WEBP" and width > 0 and height > 0)
    except Exception as e:
        decode_pass = False

    passed = (size_pass and decode_pass and entropy > 1.0)
    return {
        "file": fname,
        "rel_path": rel_path,
        "size_kb": file_size_kb,
        "dimensions": [width, height],
        "mode": mode,
        "entropy": round(entropy, 3),
        "size_pass": size_pass,
        "decode_pass": decode_pass,
        "passed": passed
    }

def audit_single_svg(filepath):
    rel_path = os.path.relpath(filepath, REPO_ROOT)
    fname = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    with open(filepath, "r", encoding="utf-8", errors="replace") as fp:
        raw_text = fp.read()

    # Adversarial checks
    has_script = bool(re.search(r"<\s*script", raw_text, re.IGNORECASE))
    has_js_link = bool(re.search(r"(?:href|xlink:href)\s*=\s*['\"]javascript:", raw_text, re.IGNORECASE))
    has_xxe = bool(re.search(r"<!entity", raw_text, re.IGNORECASE))
    has_comments = "<!--" in raw_text

    xml_valid = False
    event_attrs = []
    element_count = 0

    try:
        root_el = ET.fromstring(raw_text)
        xml_valid = True
        event_attr_pat = re.compile(r"^on[a-z]+", re.IGNORECASE)
        for elem in root_el.iter():
            element_count += 1
            tag_lower = elem.tag.lower()
            if "script" in tag_lower:
                has_script = True
            for k, v in elem.attrib.items():
                if event_attr_pat.match(k):
                    event_attrs.append(f"{k}={v}")
                if "href" in k.lower() and "javascript:" in v.lower():
                    has_js_link = True
    except Exception as e:
        xml_valid = False

    passed = (xml_valid and not has_script and not has_js_link and not has_xxe and not has_comments and len(event_attrs) == 0)
    return {
        "file": fname,
        "rel_path": rel_path,
        "file_size": file_size,
        "xml_valid": xml_valid,
        "element_count": element_count,
        "has_script": has_script,
        "has_js_link": has_js_link,
        "has_xxe": has_xxe,
        "has_comments": has_comments,
        "event_attrs": event_attrs,
        "passed": passed
    }

def run_adversarial_media_audit():
    print("=" * 80)
    print("🚀 STARTING ADVERSARIAL MEDIA & STREAM AUDIT (CHALLENGER 2)")
    print("=" * 80)

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    # ---------------------------------------------------------
    # PILLAR 1: MP4 Container & Faststart Probe
    # ---------------------------------------------------------
    print("\n[PILLAR 1] MP4 Binary Container Stress Probe & HTTP Range bytes=0-1024...")
    mp4_files = []
    for root, _, files in os.walk(VIDEO_DIR):
        for f in sorted(files):
            if f.endswith(".mp4"):
                mp4_files.append(os.path.join(root, f))
    
    mp4_results = [audit_single_mp4(p) for p in mp4_files]
    mp4_all_pass = all(r["passed"] for r in mp4_results)
    print(f"  Scanned: {len(mp4_results)} MP4 files")
    print(f"  moov precedes mdat: {sum(1 for r in mp4_results if r['moov_precedes_mdat'])} / {len(mp4_results)}")
    print(f"  moov offset < 1024 bytes: {sum(1 for r in mp4_results if r['moov_within_1kb'])} / {len(mp4_results)}")
    print(f"  HTTP Range 0-1024 mvhd readable: {sum(1 for r in mp4_results if r['range_0_1024_mvhd_readable'])} / {len(mp4_results)}")
    print(f"  Pillar 1 Verdict: {'✅ PASS (100%)' if mp4_all_pass else '❌ FAIL'}")

    # ---------------------------------------------------------
    # PILLAR 2: Audio EBU R128 & Stream Audit (Parallel Vibe Code)
    # ---------------------------------------------------------
    print("\n[PILLAR 2] Audio Integrity & EBU R128 Audit (Parallel Multi-Threaded)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        audio_futures = {executor.submit(audit_single_gold_audio, m): m for m in GOLD_MASTERS}
        audio_results = [f.result() for f in concurrent.futures.as_completed(audio_futures)]
    audio_results.sort(key=lambda r: r["file"])

    dc_audio_result = audit_datacenter_audio_zero()

    for r in audio_results:
        print(f"  {r['file']:42s} | {r['codec']} {r['sample_rate']}Hz ch:{r['channels']} | I:{r['integrated_lufs']:6.2f} LUFS | TP:{r['true_peak_dbtp']:5.2f} dBTP | LRA:{r['loudness_range_lu']:4.1f} | {'✅' if r['passed'] else '❌'}")
    print(f"  hero_act3_datacenter.mp4 audio streams: {dc_audio_result['audio_stream_count']} | {'✅' if dc_audio_result['passed'] else '❌'}")
    
    audio_all_pass = all(r["passed"] for r in audio_results) and dc_audio_result["passed"]
    print(f"  Pillar 2 Verdict: {'✅ PASS (100%)' if audio_all_pass else '❌ FAIL'}")

    # ---------------------------------------------------------
    # PILLAR 3: Poster Size & Visual Quality Audit
    # ---------------------------------------------------------
    print("\n[PILLAR 3] Poster Size & Visual Quality Audit (139 Posters)...")
    poster_files = []
    for d in [VIDEO_DIR, GOLD_IMG_DIR]:
        for root, _, files in os.walk(d):
            for f in sorted(files):
                if f.endswith(".webp") and not f.endswith(".tmp.webp"):
                    poster_files.append(os.path.join(root, f))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        poster_results = list(executor.map(audit_single_poster, poster_files))
    
    poster_results.sort(key=lambda r: r["file"])
    max_poster_sz = max(r["size_kb"] for r in poster_results)
    min_poster_sz = min(r["size_kb"] for r in poster_results)
    poster_all_pass = all(r["passed"] for r in poster_results)

    print(f"  Scanned: {len(poster_results)} poster files")
    print(f"  Size Range: {min_poster_sz:.2f} KB to {max_poster_sz:.2f} KB (Strictly < 80.0 KB)")
    print(f"  Valid WebP Decodes: {sum(1 for r in poster_results if r['decode_pass'])} / {len(poster_results)}")
    print(f"  Pillar 3 Verdict: {'✅ PASS (100%)' if poster_all_pass else '❌ FAIL'}")

    # ---------------------------------------------------------
    # PILLAR 4: SVG Security & XML Validity Audit
    # ---------------------------------------------------------
    print("\n[PILLAR 4] SVG Security & Validity Audit (57 SVGs)...")
    svg_files = []
    for root, _, files in os.walk(IMG_DIR):
        for f in sorted(files):
            if f.endswith(".svg"):
                svg_files.append(os.path.join(root, f))
    
    svg_results = [audit_single_svg(p) for p in svg_files]
    svg_all_pass = all(r["passed"] for r in svg_results)

    print(f"  Scanned: {len(svg_results)} SVG files")
    print(f"  Valid XML: {sum(1 for r in svg_results if r['xml_valid'])} / {len(svg_results)}")
    print(f"  Clean of Script Tags: {sum(1 for r in svg_results if not r['has_script'])} / {len(svg_results)}")
    print(f"  Clean of Event Handlers: {sum(1 for r in svg_results if len(r['event_attrs']) == 0)} / {len(svg_results)}")
    print(f"  Clean of Comments: {sum(1 for r in svg_results if not r['has_comments'])} / {len(svg_results)}")
    print(f"  Pillar 4 Verdict: {'✅ PASS (100%)' if svg_all_pass else '❌ FAIL'}")

    # ---------------------------------------------------------
    # CONSOLIDATED SUMMARY & TELEMETRY ARTIFACT
    # ---------------------------------------------------------
    overall_verdict = "APPROVE" if (mp4_all_pass and audio_all_pass and poster_all_pass and svg_all_pass) else "REQUEST_CHANGES"
    print("\n" + "=" * 80)
    print(f"🎯 OVERALL CHALLENGER VERDICT: {overall_verdict}")
    print("=" * 80)

    summary_telemetry = {
        "verdict": overall_verdict,
        "pillar1_mp4_container": {
            "total_files": len(mp4_results),
            "moov_precedes_mdat_count": sum(1 for r in mp4_results if r["moov_precedes_mdat"]),
            "moov_within_1kb_count": sum(1 for r in mp4_results if r["moov_within_1kb"]),
            "range_0_1024_readable_count": sum(1 for r in mp4_results if r["range_0_1024_mvhd_readable"]),
            "passed": mp4_all_pass
        },
        "pillar2_audio_ebu_r128": {
            "gold_masters_count": len(audio_results),
            "gold_masters_passed": all(r["passed"] for r in audio_results),
            "hero_datacenter_audio_zero_passed": dc_audio_result["passed"],
            "details": audio_results,
            "passed": audio_all_pass
        },
        "pillar3_posters": {
            "total_posters": len(poster_results),
            "min_size_kb": round(min_poster_sz, 2),
            "max_size_kb": round(max_poster_sz, 2),
            "all_under_80kb": all(r["size_pass"] for r in poster_results),
            "all_decoded": all(r["decode_pass"] for r in poster_results),
            "passed": poster_all_pass
        },
        "pillar4_svg_security": {
            "total_svgs": len(svg_results),
            "all_xml_valid": all(r["xml_valid"] for r in svg_results),
            "all_secure": all(r["passed"] for r in svg_results),
            "passed": svg_all_pass
        }
    }

    json_path = os.path.join(ARTIFACTS_DIR, "adversarial_media_audit.json")
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(summary_telemetry, fp, indent=2)
    print(f"Saved adversarial audit telemetry to {json_path}")

    return 0 if overall_verdict == "APPROVE" else 1

if __name__ == "__main__":
    sys.exit(run_adversarial_media_audit())
