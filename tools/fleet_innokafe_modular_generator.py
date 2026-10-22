#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

FLEET_URL = "http://localhost:7777"

TASKS = [
    {
        "id": "TASK_HOME_CRAFT",
        "node": "node-4",
        "model": "gemini-4-argon-high",
        "prompt": """You are an authentic Vietnamese specialty coffee roaster and copywriter for InnoKafe.
Write 4 craft storytelling blocks (in natural, humble, authentic Vietnamese) replacing the 4 cards on InnoKafe homepage.
ZERO AI SLOP: Ban "đẳng cấp thế giới", "đánh thức vị giác", "cuộc gặp gỡ đỉnh cao", "4 trụ cột định hình đẳng cấp".

Pillars:
1. Terroir Nguyên Bản: Đất đỏ bazan Cư M'gar (Đắk Lắk) & Sương lạnh Cầu Đất (1.650m).
2. Phơi Chậm Giàn Lưới: 100% hái quả chín đỏ bằng tay, phơi giàn lưới 28 ngày đón gió Tây Nguyên.
3. Rang Mộc Hot-Air: Rang đối lưu khí nóng hồi lưu, hạt chín đều từ lõi, không cháy cạnh, không tẩm bơ bắp.
4. Thử Nếm Cupping 84+: Đánh giá theo chuẩn SCA quốc tế, minh bạch từng mẻ rang.

For each pillar, provide:
- Tagline (e.g. 01 · THỔ NHƯỠNG BAZAN)
- Title (h4)
- Description (p - 2 to 3 natural sentences)
- Fact badge (e.g. "Độ dày tầng đất 70cm")
Return in clean structured JSON."""
    },
    {
        "id": "TASK_STORY_TIMELINE",
        "node": "gaopham",
        "model": "gemini-4-argon-high",
        "prompt": """You are the Lead Heritage Storyteller for InnoKafe.
Write 4 natural milestones for the /story (Câu chuyện Nông trại) Farm-to-Cup timeline in authentic Vietnamese.
ZERO BUZZWORDS: Write like a passionate roaster who visits the farm every harvest.

Milestones:
1. 05:00 Sáng Trên Nông Trại: Người nông dân chọn hái quả chín đỏ mọng brix > 20%.
2. Lên Men Tự Nhiên & Phơi Chậm: Honey process & Natural process trên giàn cách đất 80cm.
3. Kiểm Định Cupping Phòng Lab: Đạt chuẩn Fine Robusta và Specialty Arabica 84+ điểm SCA.
4. Rang Mộc Tươi & Đóng Túi Van 1 Chiều: Rang mới hàng tuần, chuyển đến tay người yêu cà phê trong 7 ngày sau rang.

Return in clean structured JSON with 'step', 'title', 'time_or_metric', 'narrative'."""
    },
    {
        "id": "TASK_B2B_TEXT",
        "node": "fast",
        "model": "gemini-4-argon-high",
        "prompt": """You are the Specialty Coffee B2B Solutions Director for InnoKafe.
Write natural, transparent, professional copy for /solutions-b2b in Vietnamese.
NO GENERIC MARKETING SLOP (ban "giải pháp toàn diện hàng đầu", "vươn tầm quốc tế", "đối tác tin cậy bậc nhất").

Provide copy for:
1. B2B Value Proposition: Cung cấp cà phê rang mộc theo mẻ cho quán specialty coffee, khách sạn boutique và văn phòng sáng tạo. Gửi mẫu thử miễn phí, hồ sơ cupping và date rang dưới 7 ngày.
2. Thiết Bị & Hiệu Chuẩn: Phân phối & bảo dưỡng máy pha La Marzocco, Synesso, máy xay Mahlkönig; cân chỉnh profile chiết xuất theo nguồn nước từng quán.
3. Đào Tạo Barista: Hiểu hạt, căn chỉnh cỡ xay, kiểm soát TDS và tỷ lệ brew ratio.

Return in clean structured JSON."""
    }
]

def run_task(task):
    tid = task["id"]
    node = task["node"]
    model = task["model"]
    payload = {
        "prompt": task["prompt"],
        "node_name": node,
        "model": model,
        "timeout": 120
    }
    req = urllib.request.Request(
        f"{FLEET_URL}/api/fleet/run",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            job_id = json.loads(r.read().decode())["job_id"]
            print(f"[*] {tid} enqueued as {job_id} on {node}")
    except Exception as e:
        print(f"[!] {tid} dispatch error: {e}")
        return tid, None

    for _ in range(40):
        time.sleep(2)
        try:
            poll_req = urllib.request.Request(f"{FLEET_URL}/api/fleet/jobs/{job_id}")
            with urllib.request.urlopen(poll_req, timeout=10) as r:
                d = json.loads(r.read().decode())
                if d.get("status") == "completed":
                    out = d.get("clean_response") or d.get("output") or ""
                    print(f"[✓] {tid} COMPLETED ({len(out)} chars)")
                    return tid, out
                elif d.get("status") == "failed":
                    print(f"[✗] {tid} FAILED: {d.get('stderr')}")
                    return tid, None
        except Exception:
            pass
    print(f"[!] {tid} timed out")
    return tid, None

def main():
    print("=== LAUNCHING MODULAR PARALLEL FLEET TASKS ===")
    results = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(run_task, t): t["id"] for t in TASKS}
        for f in futures:
            tid, out = f.result()
            results[tid] = out

    out_dir = "/home/zen/O20/artifacts/fleet_modular_results"
    os.makedirs(out_dir, exist_ok=True)
    for tid, content in results.items():
        if content:
            path = os.path.join(out_dir, f"{tid}.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[✓] Saved {tid} to {path}")

if __name__ == "__main__":
    main()
