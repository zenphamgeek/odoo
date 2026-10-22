#!/usr/bin/env python3
"""
tools/fleet_innokafe_cardless_vibe.py
Parallel Vibe Coding Engine via AGY Fleet for InnoKafe Specialty Coffee.
Generates Cardless / Liquid Spatial UI with restraint and ZERO AI Slop.
"""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

FLEET_URL = "http://localhost:7777"

TASKS = [
    {
        "id": "HERO_AND_RIBBON",
        "node": "pro-1",
        "model": "gemini-4-argon-high",
        "prompt": """You are an elite frontend UI/UX architect and artisan copywriter for InnoKafe (Specialty Coffee Vietnam, https://innokafe.com).
Write the XML QWeb snippet for Section 1 (Hero Cover) and Section 2 (Pledge Ribbon) for enterprise/innokafe_website/views/home.xml.

DESIGN REQUIREMENTS (CARDLESS / LIQUID SPATIAL UI WITH RESTRAINT):
1. Canvas: Atmospheric espresso background (#140C07 or #1E120B).
2. Left Column:
   - Eyebrow: Pure typography, NO pill badges, NO glowing dots. e.g. <p class="text-uppercase tracking-widest text-warning small font-monospace mb-3">Thổ Nhưỡng Cư M'gar &amp; Sương Lạnh Cầu Đất</p>
   - H1: "Hạt Cà Phê Đặc Sản <br/><span class="inno-amber-text">Đất Đỏ &amp; Sương Khói Cao Nguyên</span>"
   - Lead paragraph: Natural, humble, passionate copy about hand-picked 100% ripe cherries, 28-day slow sun drying on raised beds, and small-batch hot-air roasting every week.
   - 2 CTA buttons: "Khám Phá Dòng Hạt" (btn-primary rounded-pill) -> /products, "Trắc Nghiệm Tìm Gu (60s)" (btn-outline-secondary rounded-pill) -> /taste-profiler.
   - Metric strip (.inno-fluid-strip): 4 metrics (1.650m Cầu Đất, 84+ SCA Chuẩn Quốc Tế, 100% Quả Chín Hái Tay, Mộc 4 Không).
3. Right Column:
   - CRITICAL UNSLOP RULE: ZERO fake review stars, ZERO price tags, ZERO add-to-cart buttons on the hero photo!
   - Pure, evocative, cinematic photography frame:
     <div class="position-relative rounded-4 overflow-hidden shadow-2xl" style="aspect-ratio: 4 / 3;">
       <img src="/innokafe_website/static/src/img/photography/sensory_cupping_flight.webp" alt="Thử nếm cảm quan cà phê đặc sản InnoKafe" class="img-fluid w-100 h-100 object-fit-cover"/>
       <div class="position-absolute bottom-0 start-0 p-4 w-100" style="background: linear-gradient(180deg, transparent 40%, rgba(15, 8, 4, 0.95) 100%);">
         <span class="text-warning small font-monospace text-uppercase d-block mb-1">Mẻ Rang Mới Mỗi Tuần · SCA 84.50+</span>
         <p class="text-white small mb-0 fw-medium">Hạt Fine Robusta Cư M'gar &amp; Specialty Arabica Cầu Đất rang mộc khí nóng đối lưu</p>
       </div>
     </div>
4. Section 2: 4-Không Pledge Ribbon:
   - Clean, horizontal fluid strip with 4 pledges: Không hương liệu nhân tạo · Không phụ gia bơ bắp · Không che giấu vùng trồng · Không rang cháy khét.

OUTPUT FORMAT:
Return ONLY the raw QWeb XML snippet for these sections (from <!-- 1. HERO --> to end of <!-- 2. PLEDGE -->). Do not wrap in markdown or backticks."""
    },
    {
        "id": "CRAFT_AND_TERROIR",
        "node": "zenonmind",
        "model": "gemini-4-argon-high",
        "prompt": """You are an elite frontend UI/UX architect and artisan copywriter for InnoKafe (https://innokafe.com).
Write the XML QWeb snippet for Section 3 (Craft Story) and Section 4 (Dual Terroir Showcase) for enterprise/innokafe_website/views/home.xml.

DESIGN REQUIREMENTS (CARDLESS / LIQUID SPATIAL UI WITH RESTRAINT):
1. Section 3: Craft Story (Triết Lý Làm Nghề)
   - CRITICAL UNSLOP RULE: NO 4 repetitive box cards in a row with borders!
   - Re-architect as an ASYMMETRICAL EDITORIAL LAYOUT:
     - Left column (col-lg-5): Large evocative vertical image (/innokafe_website/static/src/img/photography/natural_raised_beds_drying.webp) showing raised beds drying coffee cherries in the sun, with a delicate caption.
     - Right column (col-lg-7): 3 fluid, cardless craft stages separated by delicate hairlines (var(--inno-spatial-hairline)):
       * 01 · THỔ NHƯỠNG MẸ ĐẤT: Đất đỏ bazan Cư M'gar & sương lạnh 1.650m Cầu Đất.
       * 02 · NÂNG NIU QUẢ CHÍN: 100% hái quả chín mọng đỏ au (Brix > 20%), phơi giàn lưới 28 ngày đón nắng gió Tây Nguyên.
       * 03 · LỬA MỘC ĐỐI LƯU: Rang mộc khí nóng Hot-Air, hạt chín đều từ tâm nhân, tuyệt đối không bơ bắp phụ gia.
2. Section 4: Dual Terroir Showcase (Hai Miền Thổ Nhưỡng)
   - Clean cardless 2-column comparison:
     - Column 1: Đắk Lắk · Cư M'gar (Fine Robusta 750m, đất bazan 70cm, thể chất dày mật mía & sô-cô-la đen, ảnh: /innokafe_website/static/src/img/photography/farm_cherries_ripe.webp).
     - Column 2: Cầu Đất · Trạm Hành (Specialty Arabica 1.650m, sương mù quanh năm, hương hoa nhài & cam Bergamot, ảnh: /innokafe_website/static/src/img/photography/farm_plantation_mist.webp).
   - Understated CTA: "Khám Phá Hành Trình Nông Trại" -> /story.

OUTPUT FORMAT:
Return ONLY the raw QWeb XML snippet for these sections (from <!-- 3. CRAFT STORY --> to end of <!-- 4. DUAL TERROIR -->). Do not wrap in markdown or backticks."""
    },
    {
        "id": "TASTE_PROFILER_AND_PRODUCTS",
        "node": "fast",
        "model": "gemini-4-argon-high",
        "prompt": """You are an elite frontend UI/UX architect and artisan copywriter for InnoKafe (https://innokafe.com).
Write the XML QWeb snippet for Section 5 (Taste Profiler Teaser) and Section 6 (Curated Specialty Products) for enterprise/innokafe_website/views/home.xml.

DESIGN REQUIREMENTS (CARDLESS / LIQUID SPATIAL UI WITH RESTRAINT):
1. Section 5: Taste Profiler Teaser
   - Use Liquid Spatial WITH INTENT: Floating glass pod (.inno-spatial-layer.inno-floating-pod) representing the interactive sensory quiz.
   - Copy: "Tìm Mẻ Rang Vừa Vặn Khẩu Vị Của Bạn" - 60 giây dạo bước qua 4 câu hỏi cảm quan để tìm dòng hạt phù hợp.
   - Primary button: "Làm Bài Trắc Nghiệm (60s)" -> /taste-profiler.
2. Section 6: Curated Specialty Products (Bộ Sưu Tập Mùa Vụ Mới)
   - CRITICAL UNSLOP RULE: ZERO raw <select> dropdowns for pack size or grind size on homepage cards! (Those belong on /products).
   - 3 Curated Products in a refined, cardless grid:
     * Product 1: Đắk Lắk Highland Fine Robusta Natural (Cư M'gar · 750m · 84.50 SCA).
       Image: /innokafe_website/static/src/img/photography/cooling_tray_artisan_roast.webp
       Notes: Dark Chocolate · Roasted Hazelnut · Molasses.
       Price: Từ 125.000 đ / 250g.
       CTA: <a href="/products#sku-robusta-natural" class="btn btn-outline-secondary rounded-pill px-4 py-2">Khám Phá &amp; Chọn Cỡ Xay →</a>
     * Product 2: Cầu Đất Mountain Bourbon Washed (Trạm Hành · 1.620m · 86.75 SCA).
       Image: /innokafe_website/static/src/img/photography/farm_plantation_mist.webp
       Notes: White Jasmine · Bergamot · Green Apple.
       Price: Từ 185.000 đ / 250g.
       CTA: <a href="/products#sku-arabica-washed" class="btn btn-outline-secondary rounded-pill px-4 py-2">Khám Phá &amp; Chọn Cỡ Xay →</a>
     * Product 3: Heritage Blend Red Honey (Cư M'gar &amp; Cầu Đất · 85.25 SCA).
       Image: /innokafe_website/static/src/img/photography/artisan_drying_sun.webp
       Notes: Wild Honey · Toasted Almond · Citrus Zest.
       Price: Từ 155.000 đ / 250g.
       CTA: <a href="/products#sku-heritage-honey" class="btn btn-outline-secondary rounded-pill px-4 py-2">Khám Phá &amp; Chọn Cỡ Xay →</a>
   - Understated footer link: "Xem Toàn Bộ 8 Dòng Hạt Đặc Sản" -> /products.

OUTPUT FORMAT:
Return ONLY the raw QWeb XML snippet for these sections (from <!-- 5. TASTE PROFILER --> to end of <!-- 6. PRODUCTS -->). Do not wrap in markdown or backticks."""
    },
    {
        "id": "TASTING_BAR_AND_B2B",
        "node": "codegeekvn",
        "model": "gemini-4-argon-high",
        "prompt": """You are an elite frontend UI/UX architect and artisan copywriter for InnoKafe (https://innokafe.com).
Write the XML QWeb snippet for Section 7 (Flagship Tasting Bar & Roastery) and Section 8 (B2B Partner Teaser) for enterprise/innokafe_website/views/home.xml.

DESIGN REQUIREMENTS (CARDLESS / LIQUID SPATIAL UI WITH RESTRAINT):
1. Section 7: Flagship Tasting Bar & Roastery
   - Atmospheric warm wood interior showcase:
     - Left column: High-res photo (/innokafe_website/static/src/img/photography/bar_warm_amber_wood_interior.webp) showing the amber wood tasting bar.
     - Right column: Invitation to visit the tasting bar, enjoy slow pour-over V60 flights, meet the roasters, and experience coffee cupping.
     - Address & Hours: 128 Nguyễn Đình Chiểu, Q.3, TP.HCM & Trạm Hành, Đà Lạt.
     - CTA: "Đặt Chỗ Thử Nếm Cupping" -> /contactus.
2. Section 8: B2B Specialty Coffee Partner Teaser
   - CRITICAL UNSLOP RULE: ZERO raw 4-input lead forms on the homepage!
   - 2-column editorial partnership showcase:
     - Left: Professional barista photo (/innokafe_website/static/src/img/photography/barista_pourover_v60_flow.webp) or packaging (/innokafe_website/static/src/img/photography/b2b_wholesale_packaging.webp).
     - Right: 3 concise wholesale benefits:
       * Hạt Rang Mộc Tươi Dưới 7 Ngày: Cung cấp ổn định hàng tuần cho quán specialty và văn phòng sáng tạo.
       * Tài Trợ & Cân Chỉnh Thiết Bị: Hỗ trợ máy pha La Marzocco, máy xay Mahlkönig, căn chỉnh profile chiết xuất theo nguồn nước.
       * Đào Tạo Barista Chuẩn SCA: Chuyển giao quy trình pha chế, kiểm soát TDS và bảo tồn hương vị.
     - CTA: <a href="/solutions-b2b" class="btn btn-primary rounded-pill px-4 py-3">Tìm Hiểu Giải Pháp Quán &amp; Doanh Nghiệp →</a>

OUTPUT FORMAT:
Return ONLY the raw QWeb XML snippet for these sections (from <!-- 7. TASTING BAR --> to end of <!-- 8. B2B -->). Do not wrap in markdown or backticks."""
    },
    {
        "id": "REVIEWS_AND_CTA",
        "node": "binhthuong",
        "model": "gemini-4-argon-high",
        "prompt": """You are an elite frontend UI/UX architect and artisan copywriter for InnoKafe (https://innokafe.com).
Write the XML QWeb snippet for Section 9 (Barista & Q-Grader Reviews) and Section 10 (Global CTA) for enterprise/innokafe_website/views/home.xml.

DESIGN REQUIREMENTS (CARDLESS / LIQUID SPATIAL UI WITH RESTRAINT):
1. Section 9: Barista & Q-Grader Reviews
   - Cardless layout: 3 authentic testimonials without oversized yellow star walls or plastic review cards.
   - Quote 1: Nguyễn Tuấn Anh (SCA Certified Q-Grader) about Fine Robusta Cư M'gar sweetness and body.
   - Quote 2: Lê Hoàng Nam (Head Barista, Artisan Cafe) about Arabica Cầu Đất floral jasmine and bergamot acidity in V60.
   - Quote 3: Phạm Minh Trang (Coffee Lover) about Heritage Red Honey brewed via Phin at home.
   - Clean typographic layout with subtle quotation marks and author credentials.
2. Section 10: Reusable Global CTA
   - Reference the call: <t t-call="innokafe_website.innokafe_global_cta"/>

OUTPUT FORMAT:
Return ONLY the raw QWeb XML snippet for these sections (from <!-- 9. REVIEWS --> to end of home template). Do not wrap in markdown or backticks."""
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
            print(f"[*] {tid} enqueued -> job {job_id} on node {node}")
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
                    # Strip any markdown code fence if wrapped
                    lines = out.strip().splitlines()
                    if lines and lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    clean = "\n".join(lines).strip()
                    print(f"[✓] {tid} COMPLETED ({len(clean)} chars)")
                    return tid, clean
                elif d.get("status") == "failed":
                    print(f"[✗] {tid} FAILED: {d.get('stderr')}")
                    return tid, None
        except Exception:
            pass
    print(f"[!] {tid} timed out")
    return tid, None

def main():
    print("=== LAUNCHING PARALLEL FLEET RUN FOR INNOKAFE CARDLESS / LIQUID SPATIAL UI ===")
    results = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(run_task, t): t["id"] for t in TASKS}
        for f in futures:
            tid, out = f.result()
            results[tid] = out

    out_dir = "/home/zen/O20/artifacts/fleet_cardless_results"
    os.makedirs(out_dir, exist_ok=True)
    for tid, content in results.items():
        if content:
            path = os.path.join(out_dir, f"{tid}.xml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[✓] Saved {tid} to {path}")

    # Verify all parts received
    missing = [t["id"] for t in TASKS if not results.get(t["id"])]
    if missing:
        print(f"[!] Warning: Missing parts: {missing}")
        return 1

    print("[✓] All 5 sections successfully generated by AGY Fleet nodes!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
