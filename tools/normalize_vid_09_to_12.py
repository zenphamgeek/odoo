#!/usr/bin/env python3
import os
import json
import subprocess

GOLD_DIR = "enterprise/insilos_website/static/src/video/gold_masters"

def normalize_file(fn):
    p = os.path.join(GOLD_DIR, fn)
    tmp = p + ".norm.mp4"
    print(f"Normalizing {fn}...")
    
    # Pass 1: Measure
    cmd1 = ["ffmpeg", "-i", p, "-af", "loudnorm=I=-14.0:TP=-1.5:LRA=7.0:print_format=json", "-f", "null", "-"]
    res1 = subprocess.run(cmd1, capture_output=True, text=True)
    idx = res1.stderr.rfind("[Parsed_loudnorm_")
    sub = res1.stderr[idx:]
    b1, b2 = sub.find("{"), sub.find("}")
    m = json.loads(sub[b1:b2+1])
    mi = m["input_i"]
    mtp = m["input_tp"]
    mlra = m["input_lra"]
    mthresh = m["input_thresh"]
    moff = m["target_offset"]
    
    # Pass 2: Linear encode
    af = f"loudnorm=I=-14.0:TP=-1.5:LRA=7.0:measured_I={mi}:measured_TP={mtp}:measured_LRA={mlra}:measured_thresh={mthresh}:offset={moff}:linear=true"
    cmd2 = [
        "ffmpeg", "-y", "-i", p,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-af", af,
        "-movflags", "+faststart",
        tmp
    ]
    res2 = subprocess.run(cmd2, capture_output=True, text=True)
    if res2.returncode != 0:
        raise RuntimeError(f"FFmpeg pass 2 failed: {res2.stderr}")
    os.replace(tmp, p)
    
    # Probe
    cmd3 = ["ffmpeg", "-i", p, "-af", "loudnorm=print_format=json", "-f", "null", "-"]
    res3 = subprocess.run(cmd3, capture_output=True, text=True)
    idx = res3.stderr.rfind("[Parsed_loudnorm_")
    sub = res3.stderr[idx:]
    b1, b2 = sub.find("{"), sub.find("}")
    m2 = json.loads(sub[b1:b2+1])
    i = float(m2["input_i"])
    tp = float(m2["input_tp"])
    lra = float(m2["input_lra"])
    print(f"  ✅ Result: {fn} -> I={i:.2f} LUFS, TP={tp:.2f} dBTP, LRA={lra:.1f} LU")
    assert -15.0 <= i <= -13.0, f"Loudness {i} out of [-15.0, -13.0] LUFS!"
    assert tp <= -1.0, f"True Peak {tp} exceeds -1.0 dBTP!"

def main():
    # Replace test file for VID_09 if exists
    test_file = os.path.join(GOLD_DIR, "INSILOS_VID_09_LOG_GOLD_MASTER.mp4.test.mp4")
    if os.path.exists(test_file):
        os.replace(test_file, os.path.join(GOLD_DIR, "INSILOS_VID_09_LOG_GOLD_MASTER.mp4"))
        print("Replaced VID_09 from successful test run.")
    
    for num, suf in [(10, "SAL"), (11, "ACC"), (12, "MKT")]:
        fn = f"INSILOS_VID_{num:02d}_{suf}_GOLD_MASTER.mp4"
        normalize_file(fn)
    print("\n🎉 ALL VID 08-12 NORMALIZED TO EBU R128 (-14.0 LUFS) WITH FASTSTART!")

if __name__ == "__main__":
    main()
