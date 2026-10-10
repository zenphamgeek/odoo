#!/usr/bin/env python3
"""
Empirical Challenger Test Harness: Media Streaming & E2E Test Suite Stress
==========================================================================
Challenger: challenger_media_and_e2e_stress_2
Target: InnoKafe Platform (enterprise/innokafe_website)

Validates:
1. MP4 FastStart moov atom positioning (moov before mdat) and WebM/VP9 codecs.
2. WebP poster sizes (< 120 KB = 122,880 bytes), dimensions, entropy, and headers.
3. Quality Gate execution in verbose offline mode.
4. E2E Test Suite stress execution: single-run, 5x sequential loop, 3x parallel concurrent workers.
5. Database schema invariance via tools/verify_schema_invariance.py.
"""

import re
import os
import sys
import time
import math
import struct
import json
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image, WebPImagePlugin

Image.init()

REPO_ROOT = Path("/home/zen/O20")
VIDEO_DIR = REPO_ROOT / "enterprise" / "innokafe_website" / "static" / "src" / "video"
POSTERS_DIR = VIDEO_DIR / "posters"
TOOLS_DIR = REPO_ROOT / "enterprise" / "innokafe_website" / "tools"
PYTHON_BIN = sys.executable

MAX_POSTER_BYTES = 120 * 1024  # 122,880 bytes

def parse_mp4_atoms(file_path):
    """Parse top-level atoms in an MP4 file."""
    atoms = []
    file_size = file_path.stat().st_size
    with open(file_path, "rb") as f:
        offset = 0
        while offset < file_size:
            f.seek(offset)
            header = f.read(8)
            if len(header) < 8:
                break
            size, fourcc = struct.unpack(">I4s", header)
            atom_type = fourcc.decode("latin1", errors="replace")
            
            if size == 1:
                # 64-bit large size
                largesize_data = f.read(8)
                if len(largesize_data) < 8:
                    break
                size = struct.unpack(">Q", largesize_data)[0]
                header_size = 16
            elif size == 0:
                # Extends to EOF
                size = file_size - offset
                header_size = 8
            else:
                header_size = 8

            atoms.append({
                "type": atom_type,
                "offset": offset,
                "size": size,
                "header_size": header_size
            })
            if size <= 0:
                break
            offset += size
    return atoms

def calculate_entropy(file_path):
    """Compute Shannon entropy of a binary file."""
    with open(file_path, "rb") as f:
        data = f.read()
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    total = len(data)
    entropy = 0.0
    for count in freq:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy

def probe_video_ffprobe(file_path):
    """Run ffprobe to extract stream telemetry."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except Exception as e:
        return {"error": str(e)}

def probe_all_media():
    print("=" * 80)
    print("1. EMPIRICAL PROBE: VIDEO CONTAINER ATOMS & POSTER ASSETS")
    print("=" * 80)

    results = {
        "mp4": {},
        "webm": {},
        "posters": {},
        "all_passed": True
    }

    # 1. MP4 files
    mp4_files = sorted(VIDEO_DIR.glob("*.mp4"))
    print(f"\nFound {len(mp4_files)} MP4 files in {VIDEO_DIR}:")
    for mp4 in mp4_files:
        atoms = parse_mp4_atoms(mp4)
        atom_types = [a["type"] for a in atoms]
        print(f"\n--- Probing MP4: {mp4.name} ({mp4.stat().st_size:,} bytes) ---")
        print(f"Top-level atoms: {' -> '.join(atom_types)}")
        for a in atoms:
            print(f"  [{a['offset']:>10} .. {a['offset']+a['size']:>10}] atom '{a['type']}' size={a['size']:,} bytes")

        moov_atom = next((a for a in atoms if a["type"] == "moov"), None)
        mdat_atom = next((a for a in atoms if a["type"] == "mdat"), None)
        ftyp_atom = next((a for a in atoms if a["type"] == "ftyp"), None)

        is_faststart = False
        if moov_atom and mdat_atom:
            is_faststart = (moov_atom["offset"] < mdat_atom["offset"])

        ff_meta = probe_video_ffprobe(mp4)
        video_stream = next((s for s in ff_meta.get("streams", []) if s.get("codec_type") == "video"), {})

        codec = video_stream.get("codec_name")
        width = video_stream.get("width")
        height = video_stream.get("height")
        duration = ff_meta.get("format", {}).get("duration")

        print(f"  FastStart compliant (moov < mdat): {is_faststart} (moov@{moov_atom['offset'] if moov_atom else 'N/A'}, mdat@{mdat_atom['offset'] if mdat_atom else 'N/A'})")
        print(f"  Codec: {codec}, Resolution: {width}x{height}, Duration: {duration}s")

        passed = is_faststart and (codec == "h264")
        if not passed:
            results["all_passed"] = False

        results["mp4"][mp4.name] = {
            "size": mp4.stat().st_size,
            "atoms": atoms,
            "faststart": is_faststart,
            "codec": codec,
            "resolution": f"{width}x{height}",
            "duration": duration,
            "passed": passed
        }
        status_label = "✅ PASS" if passed else "❌ FAIL"
        print(f"  Result: {status_label}")

    # 2. WebM files
    webm_files = sorted(VIDEO_DIR.glob("*.webm"))
    print(f"\nFound {len(webm_files)} WebM files in {VIDEO_DIR}:")
    for webm in webm_files:
        with open(webm, "rb") as f:
            header = f.read(16)
        is_ebml = header.startswith(b"\x1a\x45\xdf\xa3")
        ff_meta = probe_video_ffprobe(webm)
        video_stream = next((s for s in ff_meta.get("streams", []) if s.get("codec_type") == "video"), {})
        codec = video_stream.get("codec_name")
        width = video_stream.get("width")
        height = video_stream.get("height")
        duration = ff_meta.get("format", {}).get("duration")

        passed = is_ebml and (codec == "vp9")
        if not passed:
            results["all_passed"] = False

        print(f"\n--- Probing WebM: {webm.name} ({webm.stat().st_size:,} bytes) ---")
        print(f"  EBML Header valid: {is_ebml}")
        print(f"  Codec: {codec}, Resolution: {width}x{height}, Duration: {duration}s")
        status_label = "✅ PASS" if passed else "❌ FAIL"
        print(f"  Result: {status_label}")

        results["webm"][webm.name] = {
            "size": webm.stat().st_size,
            "is_ebml": is_ebml,
            "codec": codec,
            "resolution": f"{width}x{height}",
            "duration": duration,
            "passed": passed
        }

    # 3. WebP Poster files
    poster_files = sorted(POSTERS_DIR.glob("*.webp"))
    print(f"\nFound {len(poster_files)} WebP poster files in {POSTERS_DIR}:")
    for poster in poster_files:
        size = poster.stat().st_size
        entropy = calculate_entropy(poster)
        with open(poster, "rb") as f:
            header = f.read(12)
        is_riff_webp = header.startswith(b"RIFF") and header[8:12] == b"WEBP"
        
        try:
            with Image.open(str(poster)) as img:
                dimensions = img.size
                img_format = img.format
        except Exception as e:
            dimensions = (0, 0)
            img_format = f"Error: {e}"

        size_ok = (size < MAX_POSTER_BYTES)
        passed = size_ok and is_riff_webp and (img_format == "WEBP")
        if not passed:
            results["all_passed"] = False

        print(f"\n--- Probing Poster: {poster.name} ---")
        print(f"  Size: {size:,} bytes ({size/1024:.2f} KB) -> Strict < 120 KB (122,880 bytes): {size_ok}")
        print(f"  RIFF WEBP Header: {is_riff_webp}, Format: {img_format}, Dimensions: {dimensions[0]}x{dimensions[1]}")
        print(f"  Shannon Entropy: {entropy:.4f} bits/byte")
        status_label = "✅ PASS" if passed else "❌ FAIL"
        print(f"  Result: {status_label}")

        results["posters"][poster.name] = {
            "size": size,
            "size_kb": round(size / 1024, 2),
            "size_ok": size_ok,
            "is_riff_webp": is_riff_webp,
            "dimensions": f"{dimensions[0]}x{dimensions[1]}",
            "entropy": round(entropy, 4),
            "passed": passed
        }

    return results

def run_quality_gate():
    print("\n" + "=" * 80)
    print("2. EMPIRICAL VERIFICATION: QUALITY GATE (--offline --verbose)")
    print("=" * 80)
    cmd = [
        PYTHON_BIN,
        str(TOOLS_DIR / "quality_gate.py"),
        "--offline",
        "--verbose"
    ]
    start = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)
    print(f"Exit Code: {res.returncode} (Duration: {duration:.2f}s)")
    return {
        "exit_code": res.returncode,
        "duration": duration,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "passed": (res.returncode == 0)
    }

def run_single_e2e_suite():
    cmd = [
        PYTHON_BIN,
        str(TOOLS_DIR / "test_e2e_suite.py"),
        "--verbose"
    ]
    start = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start
    return {
        "exit_code": res.returncode,
        "duration": duration,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "passed": (res.returncode == 0)
    }

def stress_test_e2e_suite(iterations=5, concurrency=3):
    print("\n" + "=" * 80)
    print(f"3. STRESS TESTING E2E TEST SUITE: {iterations} SEQUENTIAL RUNS + {concurrency} PARALLEL WORKERS")
    print("=" * 80)

    # A. Sequential Stress
    print(f"\nA. Executing {iterations} Sequential Iterations to test for flakiness / state leaks...")
    seq_results = []
    for i in range(1, iterations + 1):
        t0 = time.time()
        res = run_single_e2e_suite()
        dt = time.time() - t0
        passed = (res["exit_code"] == 0)
        # Extract test count and pass count
        match = re.search(r"(\d+)/(\d+)\s+tests\s+Passed", res["stdout"])
        pass_info = match.group(0) if match else "count unknown"
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  Iteration {i}/{iterations}: {status} in {dt:.2f}s ({pass_info})")
        seq_results.append({
            "iteration": i,
            "exit_code": res["exit_code"],
            "duration": dt,
            "pass_info": pass_info,
            "passed": passed
        })

    seq_all_passed = all(r["passed"] for r in seq_results)

    # B. Concurrent Stress
    print(f"\nB. Executing {concurrency} Concurrent Parallel Workers running E2E suite simultaneously...")
    par_results = []
    t_par_start = time.time()
    with ProcessPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(run_single_e2e_suite): worker_id for worker_id in range(1, concurrency + 1)}
        for future in as_completed(futures):
            worker_id = futures[future]
            try:
                res = future.result()
                passed = (res["exit_code"] == 0)
                match = re.search(r"(\d+)/(\d+)\s+tests\s+Passed", res["stdout"])
                pass_info = match.group(0) if match else "count unknown"
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  Worker {worker_id}: {status} in {res['duration']:.2f}s ({pass_info})")
                par_results.append({
                    "worker_id": worker_id,
                    "exit_code": res["exit_code"],
                    "duration": res["duration"],
                    "pass_info": pass_info,
                    "passed": passed
                })
            except Exception as exc:
                print(f"  Worker {worker_id}: ❌ Exception {exc}")
                par_results.append({
                    "worker_id": worker_id,
                    "exit_code": -1,
                    "error": str(exc),
                    "passed": False
                })
    total_par_time = time.time() - t_par_start
    par_all_passed = all(r["passed"] for r in par_results)
    print(f"Concurrent stress completed in {total_par_time:.2f}s. All passed: {par_all_passed}")

    return {
        "sequential": seq_results,
        "seq_all_passed": seq_all_passed,
        "concurrent": par_results,
        "par_all_passed": par_all_passed,
        "passed": seq_all_passed and par_all_passed
    }

def run_schema_invariance():
    print("\n" + "=" * 80)
    print("4. EMPIRICAL VERIFICATION: POSTGRESQL SCHEMA INVARIANCE")
    print("=" * 80)
    cmd = [
        PYTHON_BIN,
        str(REPO_ROOT / "tools" / "verify_schema_invariance.py")
    ]
    start = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start
    print(res.stdout)
    if res.stderr:
        print("STDERR:\n", res.stderr)
    print(f"Exit Code: {res.returncode} (Duration: {duration:.2f}s)")
    return {
        "exit_code": res.returncode,
        "duration": duration,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "passed": (res.returncode == 0)
    }

def main():
    start_total = time.time()
    media_res = probe_all_media()
    qg_res = run_quality_gate()
    stress_res = stress_test_e2e_suite(iterations=5, concurrency=3)
    schema_res = run_schema_invariance()
    total_duration = time.time() - start_total

    print("\n" + "=" * 80)
    print("FINAL SUMMARY REPORT")
    print("=" * 80)
    print(f"1. Media Containers & Posters: {'✅ PASS' if media_res['all_passed'] else '❌ FAIL'}")
    print(f"2. Quality Gate (Offline):     {'✅ PASS' if qg_res['passed'] else '❌ FAIL'}")
    print(f"3. E2E Suite Stress Test:      {'✅ PASS' if stress_res['passed'] else '❌ FAIL'} (5/5 seq, 3/3 par)")
    print(f"4. Database Schema Invariance: {'✅ PASS' if schema_res['passed'] else '❌ FAIL'}")
    print(f"Total Challenger Runtime: {total_duration:.2f}s")

    all_verdicts = [
        media_res["all_passed"],
        qg_res["passed"],
        stress_res["passed"],
        schema_res["passed"]
    ]
    overall_approve = all(all_verdicts)
    verdict_str = "APPROVE" if overall_approve else "REJECT"
    print(f"\nCHALLENGER VERDICT: {verdict_str}")
    print("=" * 80)

    # Save structured results to json for handoff inclusion
    summary_path = REPO_ROOT / "tools" / "challenger_media_e2e_stress_report.json"
    summary_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdict": verdict_str,
        "total_duration": total_duration,
        "media": media_res,
        "quality_gate": {
            "exit_code": qg_res["exit_code"],
            "duration": qg_res["duration"],
            "passed": qg_res["passed"]
        },
        "stress_test": {
            "sequential_iterations": 5,
            "seq_all_passed": stress_res["seq_all_passed"],
            "concurrency_workers": 3,
            "par_all_passed": stress_res["par_all_passed"],
            "passed": stress_res["passed"]
        },
        "schema_invariance": {
            "exit_code": schema_res["exit_code"],
            "duration": schema_res["duration"],
            "passed": schema_res["passed"]
        }
    }
    with open(summary_path, "w") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Full JSON telemetry saved to: {summary_path}")

    sys.exit(0 if overall_approve else 1)

if __name__ == "__main__":
    main()
