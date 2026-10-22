#!/usr/bin/env python3
"""
tools/fleet_parallel_section_builder.py
=============================================================================
AGY Fleet Multi-Worker Swarm for InnoKafe Homepage Sections.
Generates un-slopped, production-grade QWeb XML sections in parallel across
multiple idle AGY Fleet nodes using Gemini 4 Argon High.
=============================================================================
"""

import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

FLEET_API = "http://localhost:7777/api/fleet/run-sync"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path("/tmp/innokafe_sections")

def call_fleet_node(task_name: str, prompt: str, preferred_node: str = None, model: str = "gemini-4-argon-high", timeout: int = 180):
    print(f"[*] [Fleet Task: {task_name}] Dispatching to {preferred_node or 'auto'} ({model})...")
    payload = {
        "prompt": prompt,
        "model": model,
        "timeout": timeout
    }
    if preferred_node:
        payload["node_name"] = preferred_node

    req = urllib.request.Request(
        FLEET_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout + 30) as res:
            data = json.loads(res.read().decode("utf-8"))
            elapsed = time.time() - start_t
            node = data.get("node_name", "unknown")
            output = data.get("output") or data.get("clean_response") or ""
            print(f"[✓] [Fleet Task: {task_name}] Completed by Node [{node}] in {elapsed:.1f}s ({len(output)} chars)")
            return {
                "task_name": task_name,
                "node": node,
                "elapsed": elapsed,
                "output": output,
                "error": None
            }
    except Exception as e:
        elapsed = time.time() - start_t
        print(f"[✗] [Fleet Task: {task_name}] Failed after {elapsed:.1f}s: {e}")
        return {
            "task_name": task_name,
            "node": preferred_node,
            "elapsed": elapsed,
            "output": "",
            "error": str(e)
        }


SECTIONS = [
    {
        "id": "sec1_hero",
        "name": "Hero Cover",
        "preferred_node": "node-5",
        "prompt": """You are an elite Senior Creative Frontend Architect.
TASK: Author the official QWeb XML for Section 1: Home Hero Cover for InnoKafe Specialty Coffee.

ANTI-SLOP & DESIGN RULES:
1. BAN ROBOTIC JARGON: No "Đánh thức vị giác...", no "Hành trình thăng hoa...".
2. BORDERLESS & SUBTLE HAIRLINES: Absolutely NO box-in-box card on the right with glowing yellow or gray borders.
3. BACKGROUND VIDEO:
   - Source 1: /innokafe_website/static/src/video/innokafe_hero_terroir_16x9_opt.mp4
   - Source 2: /innokafe_website/static/src/video/innokafe_cooling_tray_16x9_opt.mp4
   - Poster: /innokafe_website/static/src/video/posters/innokafe_hero_terroir_16x9_poster.webp
4. HERO COPY:
   - Eyebrow: SPECIALTY COFFEE VIỆT NAM · RANG MỘC MỖI TUẦN
   - H1: Cà Phê Đặc Sản Việt Nam.<br/>Từ Đất Đỏ Cư M'gar Đến Sương Mù Cầu Đất.
   - Lead: Thu hái 100% quả chín mọng bằng tay, phơi chậm tự nhiên trên giàn lưới và rang mộc bằng khí nóng Hot-Air đối lưu. Chúng tôi bảo tồn trọn vẹn vị ngọt mật tự nhiên và hương vị nguyên bản của từng vùng đất.
   - CTAs:
     - btn-primary: Khám Phá Dòng Hạt (links to /products)
     - btn-outline-cream: Tìm Gu Cà Phê Của Bạn (links to /taste-profiler)
   - Metrics strip (border-top border-secondary border-opacity-10):
     - 1.650m (Đỉnh gió Cầu Đất)
     - 84+ SCA (Điểm thử nếm quốc tế)
     - 100% (Hái tay quả chín)
     - Mộc 4 Không (Không tẩm ướp, không hương liệu)
5. RIGHT COLUMN SHOWCASE (Vignette):
   - An organic, high-end visual showcase using image:
     /innokafe_website/static/src/img/photography/sensory_cupping_flight.webp
   - Elegant rounded-4 container with subtle warm glow (not a harsh yellow border), soft gradient scrim.
   - Floating badge: FINE ROBUSTA NATURAL · 84.50 SCA
   - Clean details: Sô-cô-la đen 85% · Hạt dẻ nướng · Hậu vị mật mía sâu lắng
   - Price: 125.000 đ / 250g với van 1 chiều Thụy Sĩ.
   - Small primary action: Mua Ngay

OUTPUT:
Return ONLY the raw QWeb XML snippet for <section class="s_cover ..."> ... </section>. No markdown code fences, no explanations."""
    },
    {
        "id": "sec2_values",
        "name": "Pledge Ribbon & Core Craft Values",
        "preferred_node": "binhthuong",
        "prompt": """You are an elite Senior Creative Frontend Architect.
TASK: Author the official QWeb XML for Section 2 & 3: Pledge Ribbon and Core Craft Values for InnoKafe Specialty Coffee.

ANTI-SLOP & DESIGN RULES:
1. BAN "4 Trụ cột định hình đẳng cấp" or corporate speak.
2. BAN rigid 4-card grids with bright yellow circle icons and chunky borders.
3. STRUCTURE:
   - Part A: Pledge Ribbon (Cam kết Cà phê Mộc 4 Không):
     - Không Hương Liệu Nhân Tạo
     - Không Chất Bảo Quản
     - Không Phẩm Màu Hóa Học
     - Không Độn Bắp, Đậu Nành, Bơ Công Nghiệp
     - Clean horizontal ribbon with subtle amber dot dividers and warm muted typography.
   - Part B: Core Craft Section ("Triết Lý Làm Cà Phê"):
     - Headline: Tôn Trọng Sự Thật Trong Từng Tách Cà Phê
     - Subhead: Không hương liệu nhân tạo, không che giấu nguồn gốc. Mọi mẻ rang của InnoKafe đều bắt đầu từ tình yêu đất mẹ và sự kiên nhẫn của người làm nghề.
     - 4 Editorial Panels with Real Photography:
       1. Thổ Nhưỡng Nguyên Bản (Photo: /innokafe_website/static/src/img/photography/farm_plantation_mist.webp) -> Đất đỏ bazan cổ 70cm Cư M'gar và miền sương mù Cầu Đất 1.650m tạo nên cá tính hạt không thể hòa lẫn.
       2. Hái Chín & Phơi Chậm (Photo: /innokafe_website/static/src/img/photography/artisan_drying_sun.webp) -> 100% quả chín đỏ hái tay, phơi giàn lưới 28 ngày đón nắng cao nguyên, kiểm soát độ ẩm chuẩn 11%.
       3. Rang Mộc Khí Nóng Hot-Air (Photo: /innokafe_website/static/src/img/photography/artisan_roasting_beans.webp) -> Công nghệ đối lưu nhiệt tuần hoàn Châu Âu giúp hạt chín đều từ tâm, caramel hóa ngọt dịu, 0% cháy khét.
       4. Thử Nếm Chuẩn SCA (Photo: /innokafe_website/static/src/img/photography/sensory_cupping_flight.webp) -> Mỗi mẻ rang được Q-Grader kiểm định thang điểm 84+ SCA, cam kết phẩm chất đồng nhất trước khi đóng gói.
     - Layout: 4 columns or 2x2 asymmetric editorial cards with rounded-4, borderless/subtle hairline, image taking top half, elegant typography on dark warm canvas.

OUTPUT:
Return ONLY the raw QWeb XML snippet for the sections. No markdown code fences, no explanations."""
    },
    {
        "id": "sec3_terroir_profiler",
        "name": "Dual Origins & Taste Profiler Teaser",
        "preferred_node": "codegeekvn",
        "prompt": """You are an elite Senior Creative Frontend Architect.
TASK: Author the official QWeb XML for Section 4 & 5: Dual Origins (Đắk Lắk & Cầu Đất) and Taste Profiler Teaser for InnoKafe Specialty Coffee.

ANTI-SLOP & DESIGN RULES:
1. BAN "Cuộc gặp gỡ của hai đỉnh cao thổ nhưỡng..." and "Thuật toán so khớp vector 7 chiều...".
2. Write natural, inviting, sensory Vietnamese copy.
3. STRUCTURE:
   - Section 4: Dual Origins Showcase ("Hai Vùng Đất · Hai Phong Vị Đặc Trưng"):
     - Subhead: Thiên nhiên ban tặng cho Việt Nam hai vùng đất kỳ diệu để nuôi dưỡng Robusta và Arabica đẳng cấp thế giới.
     - Left Column: Đắk Lắk (Cư M'gar & Buôn Ma Thuột - 750m)
       - Image: /innokafe_website/static/src/img/photography/farm_cherries_ripe.webp
       - Fine Robusta Natural · Điểm SCA 84.50
       - Thể chất đầm dày (Heavy body), nốt sô-cô-la đen 85%, hạt dẻ nướng và hậu ngọt sâu.
     - Right Column: Cầu Đất (Trạm Hành & Đà Lạt - 1.650m)
       - Image: /innokafe_website/static/src/img/photography/farm_plantation_mist.webp
       - Specialty Arabica Bourbon Washed · Điểm SCA 86.75
       - Hương hoa nhài trắng, cam Bergamot thanh sáng, hậu vị ngọt mật tinh tế.
   - Section 5: Taste Profiler Teaser ("Bạn Thích Gu Cà Phê Như Thế Nào Mỗi Sáng?"):
     - Subhead: Bạn mê vị đắng đậm sánh của phin truyền thống hay vị chua thanh hoa quả của Pour-over V60?
     - 60 giây trắc nghiệm khẩu vị, thói quen và dụng cụ pha chế để InnoKafe gợi ý mẻ rang vừa vặn nhất cho căn bếp của bạn.
     - Clean conversational preview steps with minimalist numbers (no heavy black box cards with bright yellow outlines!).
     - Action CTA button: Làm Bài Trắc Nghiệm Tìm Gu (60 Giây) -> /taste-profiler

OUTPUT:
Return ONLY the raw QWeb XML snippet for the sections. No markdown code fences, no explanations."""
    },
    {
        "id": "sec4_products",
        "name": "Curated Products Showcase",
        "preferred_node": "ai-digimate",
        "prompt": """You are an elite Senior Creative Frontend Architect.
TASK: Author the official QWeb XML for Section 6: Curated Products Showcase for InnoKafe Specialty Coffee.

ANTI-SLOP & DESIGN RULES:
1. BAN heavy boxed cards with double borders and harsh dropdowns.
2. Clean, premium product presentation with real coffee imagery and high contrast:
   - Product 1: Đắk Lắk Highland Fine Robusta Natural
     - Image: /innokafe_website/static/src/img/beans_robusta_natural.svg
     - Origin: Cư M'gar, Đắk Lắk · Độ cao 750m · Sơ chế Natural phơi chậm
     - Cupping: 84.50 SCA · Nốt hương: Sô-cô-la Đen, Hạt Dẻ Nướng, Mật Mía
     - Base price: 125.000 đ / Túi 250g
     - Selector for 250g (125k), 500g (235k), 1kg (440k)
     - Selector for Grind: Nguyên Hạt, Phin, Espresso, V60, Cold Brew
   - Product 2: Cầu Đất Mountain Bourbon Washed
     - Image: /innokafe_website/static/src/img/beans_arabica_washed.svg
     - Origin: Trạm Hành, Cầu Đất · Độ cao 1.620m · Sơ chế Fully Washed
     - Cupping: 86.75 SCA · Nốt hương: Hoa Nhài Trắng, Cam Bergamot, Táo Xanh
     - Base price: 185.000 đ / Túi 250g
     - Selector for 250g (185k), 500g (350k), 1kg (660k)
     - Selector for Grind
   - Product 3: InnoKafe Heritage Signature Red Honey
     - Image: /innokafe_website/static/src/img/beans_heritage_honey.svg
     - Origin: Blend 70% Arabica Cầu Đất x 30% Fine Robusta Đắk Lắk
     - Cupping: 85.50 SCA · Nốt hương: Mật Ong Rừng, Bơ Caramel, Táo Đỏ
     - Base price: 155.000 đ / Túi 250g
     - Selector for 250g (155k), 500g (295k), 1kg (550k)
     - Selector for Grind
3. Product Cards Style:
   - Subtle translucent dark card with border: 1px solid rgba(247, 242, 234, 0.08); background: rgba(28, 16, 10, 0.65);
   - Clean typography, high contrast, smooth hover transition.
   - Clean button: Thêm Vào Giỏ (btn-primary rounded-pill).

OUTPUT:
Return ONLY the raw QWeb XML snippet for <section class="s_three_columns ..."> ... </section>. No markdown code fences, no explanations."""
    },
    {
        "id": "sec5_tasting_reviews_b2b",
        "name": "Tasting Bar, Verified Reviews & B2B Solutions",
        "preferred_node": "zenonmind",
        "prompt": """You are an elite Senior Creative Frontend Architect.
TASK: Author the official QWeb XML for Sections 8, 9, 10, 11: Flagship Tasting Bar, Verified Reviews, B2B Solutions, and Global CTA for InnoKafe.

ANTI-SLOP & DESIGN RULES:
1. FIXED STAR RATINGS: Never use font-awesome that renders as broken rectangles (□□□□□). Use inline SVG stars or Unicode ★ with style="color: #D48842;".
2. BAN generic testimonial cards with fake stock quotes. Use grounded, authentic quotes from real baristas and daily brewers.
3. STRUCTURE:
   - Section 8: Flagship Tasting Bar & Workshop Experience:
     - Headline: Không Gian Trải Nghiệm & Thử Nếm Cà Phê Mộc
     - Lead: Thưởng thức các mẻ rang tươi mới trong tuần, quan sát chiết xuất Espresso 9-bar và Pour-over V60 cùng các barista InnoKafe.
     - Photo: /innokafe_website/static/src/img/photography/lifestyle_modern_cafe.webp & /innokafe_website/static/src/img/photography/lifestyle_barista_craft.webp
     - Address: 128 Nguyễn Đình Chiểu, Phường Võ Thị Sáu, Quận 3, TP. Hồ Chí Minh
     - Roastery: Km 7, Quốc Lộ 14, Huyện Cư M'gar, Đắk Lắk
   - Section 9: Đánh Giá Từ Những Người Yêu Cà Phê Mộc (Testimonials):
     - 3 authentic reviews with 5 golden stars (★ ★ ★ ★ ★):
       1. Nguyễn Tuấn Anh (Q-Grader & Roaster): "Hạt Fine Robusta Cư M'gar của InnoKafe xử lý sơ chế Natural rất sạch. Vị sô-cô-la đen đậm đà mà không hề bị khét hay gắt cổ họng."
       2. Lê Hoàng Nam (Head Barista): "Arabica Cầu Đất mẻ rang Light-Medium giữ được hương hoa nhài và độ chua sáng đặc trưng của thổ nhưỡng sương mù 1.600m."
       3. Phạm Minh Trang (Home Brewer): "Mình làm trắc nghiệm tìm gu và được gợi ý Heritage Red Honey. Pha bằng phin nhôm truyền thống hay cold brew uống mỗi sáng đều thơm ngát."
   - Section 10: Giải Pháp Cà Phê Cho Quán & Doanh Nghiệp (B2B HORECA):
     - Photo: /innokafe_website/static/src/img/photography/b2b_wholesale_packaging.webp
     - Straightforward hospitality partnership: Cung cấp hạt rang mộc định kỳ, tư vấn profile máy pha espresso, đào tạo kỹ thuật chiết xuất barista chuẩn SCA.
   - Section 11: Global Footer CTA:
     - Headline: Bắt Đầu Ngày Mới Bằng Tách Cà Phê Đúng Gu
     - Clean action buttons: Mua Hạt Trực Tuyến & Thử Trắc Nghiệm Tìm Gu.

OUTPUT:
Return ONLY the raw QWeb XML snippet for these sections. No markdown code fences, no explanations."""
    }
]

def clean_xml_output(raw_output):
    code_match = re.search(r"```(?:xml)?\s*(.*?)\s*```", raw_output, re.DOTALL)
    if code_match:
        content = code_match.group(1).strip()
    else:
        content = raw_output.strip()
    return content

def run_parallel_builder():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print(f"[*] LAUNCHING AGY FLEET PARALLEL SECTION BUILDER ({len(SECTIONS)} WORKERS)")
    print("=" * 70)

    start_t = time.time()
    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_sec = {
            executor.submit(call_fleet_node, sec["name"], sec["prompt"], sec["preferred_node"], "gemini-4-argon-high", 180): sec
            for sec in SECTIONS
        }
        for future in concurrent.futures.as_completed(future_to_sec):
            sec = future_to_sec[future]
            try:
                res = future.result()
                results[sec["id"]] = res
                out_file = OUTPUT_DIR / f"{sec['id']}.xml"
                cleaned = clean_xml_output(res["output"])
                out_file.write_text(cleaned, encoding="utf-8")
                print(f"[✓] Saved {sec['id']} ({len(cleaned)} chars) -> {out_file}")
            except Exception as e:
                print(f"[!] Error processing {sec['id']}: {e}")

    total_elapsed = time.time() - start_t
    print("=" * 70)
    print(f"[✓] All {len(SECTIONS)} sections completed in {total_elapsed:.1f}s.")
    return results

if __name__ == "__main__":
    run_parallel_builder()
