#!/usr/bin/env python3
"""
Dispatch deep architecture prompt to Claude Opus Thinking on AGY Fleet node nebula.
"""
import json
import urllib.request
import sys
import time

PROMPT = """# BÁO CÁO & ĐỀ BÀI KIẾN TRÚC CAO CẤP: HARD REFACTOR ZERO ODOO CODE GENESIS (KHÔNG VÙNG CẤM)

Kính gửi: Hội đồng Kiến trúc Sư trưởng & Chuyên gia Phản biện Cấp cao (Node Opus 5.5 - Claude Opus High Reasoning)
Dự án: Insilos Platform 20.0 (Hard Fork Sovereign Enterprise Platform)
Môi trường: Repository /home/zen/O20, Git Branch insilos-genesis-fork (HEAD: d491b57e5), Database PostgreSQL odoo20_dev trên port 5434, Server daemon port 28069.

---

## 1. BỐI CẢNH VÀ THÀNH TỰU ĐÃ ĐẠT ĐƯỢC (COHORTS 1 - 10 ĐÃ HOÀN TẤT 100%)
Chúng tôi đã hoàn thành xuất sắc 10 Cohorts cốt lõi của quá trình Hard Fork tái cấu trúc thực thể ORM & Database Table sang Danh pháp Doanh nghiệp IBM (IBM Banking & Enterprise Data Warehouse Taxonomy), đạt 100% kiểm định thực nghiệm trên live database odoo20_dev:
1. Cohort 01: party.classification <-> res.partner.category (Commit e4d1cd40d)
2. Cohort 02: system.attachment <-> ir.attachment (Commit bb48661c5)
3. Cohort 03: organization.unit <-> res.company (Commit 8c5156a06)
4. Cohort 04: party.master <-> res.partner (Commit c7f354557)
5. Cohort 05: catalog.item & catalog.sku <-> product.template & product.product (Commit fb3b953ea)
6. Cohort 06: procurement.order & procurement.order.line <-> purchase.order & purchase.order.line (Commit 90df68acc)
7. Cohort 07: order.header & order.line <-> sale.order & sale.order.line (Commit c22d4dffa)
8. Cohort 08: logistics.transfer & logistics.movement <-> stock.picking & stock.move (Commit c2705ada5)
9. Cohort 09: manufacturing.order & manufacturing.bom <-> mrp.production & mrp.bom (Commit 9d4c92218)
10. Cohort 10: finance.journal.entry & finance.journal.line <-> account.move & account.move.line (Commit d491b57e5)

### Các cơ chế kỹ thuật cốt lõi đã thiết lập thành công:
- Database Schema Dual Invariance: 260 SQL Updatable Views với INSTEAD OF INSERT/UPDATE/DELETE triggers + 120 M2M cross-aliased sorted views (ví dụ: logistics_transfer_procurement_order_rel <-> procurement_order_logistics_transfer_rel).
- Core ORM Comodel Resolution: Nâng cấp odoo/orm/fields_relational.py với _is_matching_comodel và setup_related(self, model) cho phép ORM tự động phân giải quan hệ One2many/Many2many/Many2one khi model gốc hoặc comodel sử dụng tên aliased mới.
- Sequence Mirroring: Tự động nhân bản ir_sequence sang code mới bảo toàn implementation và number_next.

---

## 2. NHIỆM VỤ DÀNH CHO NODE OPUS 5.5: ĐÀO SÂU KHẢ NĂNG HARD REFACTOR ZERO ODOO CODE GENESIS (KHÔNG VÙNG CẤM)

User yêu cầu: "tiếp tục đào sâu khả năng Hard Refactor Zero Odoo Code Genesis không vùng cấm".
Nguyên tắc "Không vùng cấm" (No Forbidden Zones) xác lập rằng không một tầng nào của hệ thống được phép duy trì vĩnh viễn dấu vết legacy genesis: từ Python runtime imports, package root directory, QWeb XML engine, OWL 3 JavaScript client, cho đến toàn bộ các phân hệ mở rộng (HRM, PM, PS, QM, CRM, Fleet).

Yêu cầu Node Opus 5.5 phân tích, phản biện sâu sắc, đưa ra kiến trúc giải pháp chi tiết và đặc tả kỹ thuật cho 6 MẶT TRẬN (FRONTIERS) then chốt sau:

### MẶT TRẬN 1: Virtualization & Dual-Namespacing Tầng Python Runtime (odoo.* -> insilos.*)
- Lập trình cơ chế sys.meta_path finder & loader tùy chỉnh (insilos.core.importer hoặc tương đương) cho phép các tệp mã nguồn có thể viết import insilos, from insilos import models, fields, api, from insilos.addons.base import ... một cách tự nhiên và chính thức.
- Cơ chế ánh xạ ngược (proxy / alias shim) để bảo đảm các module bên thứ 3 hoặc add-ons cũ vẫn gọi import odoo mà không gãy.
- Phân tích rủi ro cyclic imports, sys.modules cache pollution, và cách xử lý __name__, __package__, __spec__.
- Cung cấp code Python hoàn chỉnh của insilos_importer.py sẵn sàng nhúng vào boot sequence.

### MẶT TRẬN 2: QWeb & View XML Engine Tương Thích Hai Chiều Không Vùng Cấm
- Hiện tại các file view XML bắt đầu bằng <odoo><data>... Làm thế nào để QWeb View Engine và ir.ui.view chấp nhận thẻ gốc <insilos><data>... hoặc <insilos> làm first-class citizen?
- Cơ chế giải quyết XPath và Model Aliasing trong XML: Nếu view kế thừa gọi model="res.partner" hay model="party.master", hoặc xpath trỏ vào model aliased, làm thế nào để View Validation (_check_xml, read_combined) nhận diện tương đương 100%?
- Tẩy rửa các class mang tiền tố genesis (oe_*, o_*) ở tầng parser / compiler của QWeb.
- Cung cấp đoạn code can thiệp chuẩn mực vào ir_ui_view.py và qweb.py.

### MẶT TRẬN 3: OWL 3 & Client JS Framework Sovereign Independence
- Trong Web Client OWL 3 (addons/web/static/src/):
  - Thay thế window.odoo thành window.insilos kèm bidirectional Proxy shim.
  - Tái cấu trúc registry odoo.define thành insilos.define hoặc ES6 modules thuần túy.
  - Các service @web/... -> @insilos/core/...
  - RPC endpoints: /web/dataset/call_kw và session management (insilos_session_id).
- Cung cấp code JavaScript shim và chiến lược chuyển đổi OWL 3 sạch sẽ.

### MẶT TRẬN 4: Mở Rộng 6 Cohorts Tiếp Theo (Cohorts 11 - 16) Chuẩn IBM Enterprise
Lập bảng danh mục chi tiết (Model Odoo cũ -> Model Insilos mới -> Tên Table SQL mới) cho 6 Cohort tiếp theo:
- Cohort 11: Project Systems (SAP PS / IBM Project Management): project.project, project.task, project.milestone
- Cohort 12: Plant Maintenance (SAP PM / IBM Enterprise Asset Mgmt): maintenance.equipment, maintenance.request, maintenance.team
- Cohort 13: Human Capital Management (SAP HCM / IBM HR): hr.employee, hr.department, hr.job, hr.contract
- Cohort 14: Quality Management (SAP QM / IBM Quality): quality.point, quality.check, quality.alert
- Cohort 15: Pipeline & CRM (IBM Customer Engagement): crm.lead, crm.stage, crm.team
- Cohort 16: Fleet Logistics & Telemetry: fleet.vehicle, fleet.vehicle.log.services, fleet.vehicle.odometer

### MẶT TRẬN 5: The Sovereign AST-Grep PDCA Engine (Tự Động Hóa Quét & Sửa Mã Cấu Trúc)
- User nhấn mạnh: "Tôi từng thành công khi tuần tự PDCA AST Grep để sửa chữa khoanh vùng các Odoo code footprint mà không có vùng cấm từ OWL3, QWEB cho đến ORM , Table name. Hãy document yêu cầu này, bạn có chưa có cách làm nó".
- Hãy đặc tả chi tiết một Engine AST-Grep PDCA hoàn chỉnh:
  * Bộ quy tắc (Ruleset) mẫu bằng AST-Grep (sgconfig.yml và rule YAMLs) cho Python, JavaScript (OWL), và XML.
  * Quy trình 4 bước PDCA:
    1. Plan (AST Pattern Matching & Impact Matrix)
    2. Do (AST Structural Rewrite & Dual-Declaration Insertion)
    3. Check (HOOT tests, Python compilation, Council Gates)
    4. Act (Git Commit & Lock Invariance)
  * So sánh vượt trội của AST-Grep so với regex string replacement thông thường (tránh false positives, bảo toàn AST semantics).

### MẶT TRẬN 6: Lộ Trình Chuyển Đổi Vật Lý (Physical Directory Harmonization) & Single Branch Invariant
- Chiến lược chuyển đổi thư mục vật lý odoo/ -> insilos/ trong Git branch insilos-genesis-fork mà không làm đứt gãy lịch sử Git (git log follow), không làm hỏng symlinks hoặc virtual environments (.venv).
- Cơ chế Rollback và Redundancy bảo vệ hệ thống live.

---

## 3. YÊU CẦU ĐẦU RA TỪ OPUS 5.5
1. Bản phản biện và định hướng kiến trúc sâu sắc, chi tiết, mang tính học thuật và kỹ thuật thực thi cao nhất.
2. Code mẫu cụ thể cho insilos_importer.py (sys.meta_path hook).
3. Code mẫu cụ thể cho QWeb engine support <insilos>.
4. Bảng đặc tả 6 Cohorts mới (Cohorts 11-16) kèm SQL view definitions và ORM aliases.
5. Bộ quy tắc AST-Grep mẫu (.yaml) sẵn sàng áp dụng.
6. Kế hoạch hành động cụ thể để phối hợp Fleet (Gemini Flash High song song) triển khai ngay sau đó.
"""

def main():
    payload = {
        "prompt": PROMPT,
        "model": "claude-opus-4.8",
        "node_name": "nebula",
        "timeout": 600
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:7777/api/fleet/run-sync",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    print(f"[{time.strftime('%X')}] Dispatching request to Claude Opus Thinking on nebula...", flush=True)
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            duration = time.time() - start_time
            print(f"[{time.strftime('%X')}] Received response in {duration:.1f}s. Status: {result.get('status')}", flush=True)
            output_text = result.get("clean_response") or result.get("stdout") or result.get("output", "")
            if not output_text:
                print("DEBUG: result=", json.dumps(result)[:500])
            with open("/home/zen/O20/docs/PROPOSAL_ZERO_GENESIS_FRONTIERS_OPUS.md", "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"Successfully wrote output to /home/zen/O20/docs/PROPOSAL_ZERO_GENESIS_FRONTIERS_OPUS.md ({len(output_text)} chars)")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
