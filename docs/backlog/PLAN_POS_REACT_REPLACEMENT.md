# Kế hoạch nghiên cứu khả thi: Thay POS OWL/QWeb bằng React + Carbon Design

**Ngày**: 2026-07-27 (Cập nhật: 2026-10-13) | **Trạng thái**: PoC & Advanced Parity 100% Pass | **Quyết định**: Sẵn sàng Shadow Pilot

---
## Lock this plan 
Đưa Plan vào Backlog với điều kiện kích hoạt rõ ràng.
## 1. Tóm tắt

POS là ứng dụng duy nhất trong hệ thống Insilos có kiến trúc **offline-first độc lập**
— nó không phụ thuộc vào OWL/webclient để chạy, chỉ dùng chung RPC và bundle cơ sở.
Điều này khiến POS là **ứng cử viên khả thi nhất** để thử nghiệm thay framework frontend.
Tuy nhiên, chi phí thực vượt xa 244 file client — phải tính đến 66 module mở rộng,
~250 file test, 52 model backend, 45 model được đồng bộ xuống client, và 112 entry
asset bundle.

**Khuyến nghị**: KHÔNG làm toàn diện ở thời điểm này. Chỉ làm PoC (Proof of Concept)
với phạm vi tối thiểu để đo lường. Đưa toàn bộ phần còn lại vào Backlog với điều kiện
kích hoạt rõ ràng.

---

## 2. Hiện trạng (số liệu thật từ khảo sát)

### 2.1. Quy mô toàn hệ thống

| Thành phần | Con số |
|---|---|
| File `.js` trong `static/src` (addons + apps) | **~5,200+** |
| File template `.xml` trong `static/src` | **~1,800+** |
| Component OWL/wli (`extends Component`) | **~410** |
| Tổng dòng JS (không tính lib/test) | **~380,000+** |
| Có React trong repo? | **Không** — 0 file dùng `from "react"` |
| Có Vite/webpack/rollup? | **Không** — dùng bundler nội bộ của Insilos |
| Bundle CSS hiện tại | Terser + SCSS compiler nội bộ, GIL-blocking khi `workers=0` |

Framework hiện tại: **wli** (hard-fork từ OWL 2), nằm ở `addons/web/static/lib/wli/`,
phân phối qua AMD-style module loader (`module_loader.js`).

### 2.2. Quy mô riêng module POS

| Thành phần | Con số |
|---|---|
| File `.js` client (`static/src`) | **166** |
| File `.xml` client | **78** |
| Tổng file client | **244** |
| File `.py` model backend | **52** (108 khai báo `_name`/`_inherit`) |
| Controller endpoint | **8 route** (6 `user`, 2 `public`) |
| Asset bundle POS dùng | **11 bundle**, **112 entry** |
| Module phụ thuộc vào POS | **66** (45 addons, 21 apps) |
| Test Python | **28 file** |
| Test JS | **~145 file** (25 tour, 41 data mock, 17 helper tour, ...) |
| Model đồng bộ xuống client | **45 model** |
| Client ORM (offline) | **7 file** (`related_models/`) |
| Lưu trữ offline | IndexedDB (chính) + localStorage (phụ) + Service Worker |
| Component màn hình | 11 screen |

### 2.3. Kiến trúc giao tiếp POS ↔ Server

POS dùng **RPC ORM chuẩn** (`/web/dataset/call_kw`) — không có route riêng cho
dữ liệu. Các method server đều là method trên model:

```
Client                                     Server
─────────────────────────────────────────────────────
pos.session.load_data_params()         →   schema fields/relations
pos.session.load_data([44 models])     →   toàn bộ dữ liệu khởi tạo
pos.session.filter_local_data()        →   id cần xoá khỏi IndexedDB
pos.order.sync_from_ui([orders])       →   đẩy đơn lên
/pos/ping (jsonrpc)                    →   dò online
```

**Hệ quả quan trọng**: POS mới không cần thay đổi backend. Chỉ cần gọi đúng 4 RPC
này và mô phỏng đúng ORM phía client (`related_models/`).

### 2.4. `simpos` (GitHub)

Đã tra cứu repo `hieuhani/simpos`. Đây là bản viết lại POS bằng React + Vite, loại
bỏ OWL nhưng vẫn gọi API của Insilos. Các đặc điểm:
- React + TypeScript + Vite
- IndexedDB cho offline
- Không dùng OWL template nào
- Tự dựng UI POS từ đầu (product grid, cart, payment, receipt)
- Vẫn gọi RPC Insilos để đồng bộ

**Khác biệt then chốt với repo này**: `simpos` chỉ làm POS, không có 66 module
mở rộng (l10n, cổng thanh toán, restaurant, loyalty...). Mỗi module đó thêm
component, template, asset bundle riêng vào POS.

---

## 3. Phân tích chi phí — 5 nhóm công việc

### Nhóm A: Core POS màn hình chính (có thể PoC)

| Việc | Ước lượng | Ghi chú |
|---|---|---|
| Viết lại 11 screen bằng React | 40-80h | Product, payment, receipt, ticket, partner, login... |
| Viết lại 20 popup | 20-40h | Discount, note, customer, payment... |
| Port client ORM (`related_models/`) | 20-30h | 7 file, logic phức tạp: lazy load, computed field, inverse |
| Port IndexedDB layer | 10-15h | Có thể dùng thư viện `idb` thay vì tự viết |
| Port data sync service | 15-20h | `data_service.js` → React context hoặc Zustand |
| Tích hợp Vite bundle | 10-15h | Cần plugin custom để gọi đúng RPC endpoint |
| **Tổng nhóm A** | **115-200h** | Phạm vi: **chỉ POS lõi, không extension** |

### Nhóm B: 66 module mở rộng (phần lớn công sức)

| Loại module | Số lượng | Mỗi module cần | Tổng ước lượng |
|---|---|---|---|
| Thanh toán (Stripe, Adyen...) | 13 | Component + hook thanh toán | 65-130h |
| Restaurant (bàn, tầng, bếp) | 1 | 3 screen + 8 component | 80-120h |
| Bản địa hoá (l10n) | 20 | Template hóa đơn, cấu hình thuế | 40-80h |
| Khác (loyalty, discount, sale, mrp...) | 32 | 1-3 component mỗi module | 64-160h |
| **Tổng nhóm B** | **66** | | **249-490h** |

### Nhóm C: Test (~250 file)

| Việc | Ước lượng |
|---|---|
| Port 148 tour test sang Playwright/Cypress | 80-120h |
| Viết lại unit test cho component React | 40-60h |
| Viết test tích hợp IndexedDB + sync | 20-30h |
| **Tổng nhóm C** | **140-210h** |

### Nhóm D: Asset bundle & build system

| Việc | Ước lượng |
|---|---|
| Tích hợp Vite output vào asset bundle Insilos | 20-30h |
| Xử lý manifest asset cho 66 module | 15-20h |
| CSS: port SCSS POS sang Carbon tokens | 30-50h |
| **Tổng nhóm D** | **65-100h** |

### Nhóm E: Song song hai hệ thống (transition)

Không thể cắt ngay — 66 module vẫn trỏ vào bundle POS cũ. Chiến lược:

| Giai đoạn | Thời gian |
|---|---|
| PoC: POS lõi chạy React ở route riêng (`/pos/react/<id>`) | 2-3 tuần |
| Song song: POS cũ + POS React, chọn bằng config | 2-4 tháng |
| Migration module: từng module một | 6-12 tháng |
| Cắt POS cũ | Sau khi module cuối cùng migrate |

---

## 4. Carbon Design vs hiện trạng

| Tiêu chí | Hiện tại (wli/OWL) | Carbon Design (React) |
|---|---|---|
| Bundle size | 9.9 MB (toàn bộ `web.assets_web.min.js`) | React + Carbon: ~200KB gzipped |
| Offline | Tự viết, đầy đủ | Phải tự viết lại toàn bộ |
| Component library | Không có — POS tự dựng hết | Có sẵn: Button, Modal, Table, Grid, Form... |
| Design system | Bootstrap POS theme | Carbon v11 (IBM) |
| Learning curve | OWL/Virtual DOM riêng | React phổ thông |
| Ecosystem | Đóng, không dùng được npm | Mở, toàn bộ npm |

Carbon Design **không có sẵn component POS** (product grid, numpad, cart, receipt).
Nó là design system cho enterprise dashboard — không phải POS. Dùng Carbon cho
POS tương đương dùng Bootstrap cho POS: có ích cho button/modal nhưng vẫn phải
tự dựng phần đặc thù POS.

---

## 5. Quyết định & Khuyến nghị

### 5.1. KHÔNG làm toàn diện

Lý do:
1. **Chi phí 500-1000h** cho toàn bộ, chưa kể test và 66 module.
2. **Không có lợi ích kinh doanh ngay** — POS hiện tại chạy ổn định, offline-first
   đã hoàn chỉnh, đã pass 141/146 SWEEP.
3. **66 module mở rộng** là phần lớn chi phí — mỗi module thêm component vào POS
   qua cơ chế kế thừa template. React cần cơ chế plugin tương đương.
4. **Rủi ro hồi quy cao** — POS đang xử lý tiền thật của khách hàng. Mọi lỗi sync
   đều mất dữ liệu.

### 5.2. LÀM PoC với phạm vi tối thiểu

Nếu vẫn muốn thử, đề xuất:

| Thành phần | Phạm vi PoC |
|---|---|
| Màn hình | **Chỉ Product Screen** — 1 screen chính |
| Chức năng | Hiển thị danh mục sản phẩm, thêm vào cart, xem cart |
| Không làm | Thanh toán, sync, offline, printer, customer display |
| Bundle | Route riêng `/pos/react/<id>`, không đụng bundle cũ |
| Framework | React 19 + Vite + IndexedDB (qua `idb`) |
| Design | Tối giản — Carbon hoặc CSS thuần, quyết định sau |
| Thời gian | 2-3 ngày |
| Tiêu chí dừng | Đo bundle size, tốc độ render, DX (developer experience) |

### 5.3. Điều kiện kích hoạt giai đoạn tiếp theo

Chỉ làm tiếp nếu PoC chứng minh được **cả ba** điều sau:

1. **Bundle size giảm ≥70%** so với `point_of_sale.assets_prod` hiện tại
2. **Cơ chế plugin** cho phép module ngoài (`pos_restaurant`, `pos_stripe`...)
   đăng ký component React mà không cần sửa core POS
3. **Migration path** cho 66 module rõ ràng — mỗi module cần ≤4h để port

---

## 6. Việc nên làm NGAY (không cần React)

| Việc | Lý do | Chi phí |
|---|---|---|
| Tách `point_of_sale.assets_prod` khỏi `web._assets_core` | POS đang kéo theo ~30% core backend không dùng | 2-4h |
| Đo chính xác bundle size POS | Chưa có số riêng cho POS — biết đúng mới quyết định được | 30 phút |
| Viết gate `check_pos_bundle_size.py` | Cảnh báo khi bundle tăng >5% | 1h |
| Audit `pos_load_mixin` — model nào thực sự cần nạp? | 45 model, nhiều cái POS không dùng (vd `is.module.module`) | 2h |

---

## 7. Tài liệu tham khảo

- `simpos`: https://github.com/hieuhani/simpos — React + Vite POS thay thế Insilos POS
- Carbon Design System: https://carbondesignsystem.com/
- `idb` (IndexedDB wrapper): https://github.com/jakearchibald/idb
- PoC hiện có trong repo: `tools/_probe_new.js`, `tools/_probe_fail.js` (mẫu Playwright)
- POS architecture (đã khảo sát): `insilos/addons/point_of_sale/models/pos_session.py:139-188`, `insilos/addons/point_of_sale/controllers/main.py`

---

## 8. Tiến độ Thực tế & Trạng thái Đưa sang /O20 (2026-10-12)

**Trạng thái**: ĐÃ HOÀN TẤT ĐƯA SANG `/O20` & KIỂM THỬ E2E LIVE 100% PASS

### 8.1. Các Phân hệ Đã Tích hợp
- `enterprise/pos_react`: Core React 18 SPA POS Terminal (`/pos/react/<config_id>`), offline IndexedDB store, tax engine, pricelist engine, websocket realtime, receipt printer.
- `enterprise/pos_discount_react`: Plugin chiết khấu theo tỷ lệ / số tiền cố định.
- `enterprise/pos_hr_react`: Plugin đăng nhập / khóa màn hình nhân viên theo mã PIN và quyền hạn.
- `addons/pos_sale`: Plugin liên kết đơn bán hàng Sales Summary.
- `addons/pos_stripe`: Plugin cổng thanh toán thẻ điện tử.
- `addons/pos_restaurant`: Plugin quản lý bàn ăn, chuyển bàn và số lượng khách.
- `enterprise/pos_barcodelookup`: Plugin tạo sản phẩm và tìm kiếm nhanh qua mã vạch.

### 8.2. Các Lỗi Kiến trúc Đã Khắc phục Khi Chuyển Sang Insilos 20 / O20
1. **Empty Fields Validation (`offline_store.js`)**: Khi `fields` rỗng (ví dụ `pos.config`), nạp danh sách `model_fields` từ ORM để sinh `relations` hợp lệ, đảm bảo metadata validation vượt qua.
2. **Missing `id` trong `ir.ui.view` Receipt Templates**: Gán fallback `'id': key` trong `ir_ui_view.py` và chuẩn hóa trong `load_data` backend.
3. **Many2many Ambiguity (`Many2many relation must have only one inverse`)**: Sắp xếp trường không tính toán lên trước và lọc trùng `(comodel, relation_table)` trong `_load_pos_data_relations`.
4. **Model Aliases (`rs.partner` / `rs.company` / `rs.users`)**: Ánh xạ hai chiều giữa sovereign aliases (`party.master`, `organization.unit`), `res.*`, và `rs.*` trong cả Python backend và JS frontend.
5. **Deprecated `check_access_rule` trong Insilos 20 / O20**: Chuyển đổi toàn bộ sang `session.check_access("read")` theo chuẩn ORM Insilos 20.
6. **Dummy Inverse M2M Leaks**: Lọc bỏ các trường synthetic `dummy: true` (ví dụ `<-pos.config.available_pricelist_ids`) khỏi danh sách `read()` và `serializeOrm()`.
7. **Draft Reconcile False Alarm**: Chuẩn hóa `lineSnapshot` chỉ đối soát 5 trường nghiệp vụ cốt lõi (`uuid`, `product_id`, `qty`, `price_unit`, `discount`), triệt tiêu hiện tượng khóa sai đơn hàng khi đồng bộ draft.

### 8.3. Kết quả Kiểm thử Nghiệm thu
- **Unit Test JS Suite**: `node --test enterprise/pos_react/tests/*.test.js` -> **4/4 PASS (100%)** (`cart_lines`, `metadata_graph`, `pricelist_engine`, `tax_engine`).
- **Live Playwright E2E**: `node tools/test_pos_react_live_e2e.js` -> **100% PASS**:
  - Giao diện nạp đầy đủ 31 sản phẩm mẫu và 19 danh mục.
  - Chọn khách hàng, tìm kiếm món, thêm vào giỏ hàng (`Croissant` + `Espresso` = $7.30).
  - Thanh toán thành công bằng tiền mặt ("Pay cash"), đồng bộ tức thời tạo đơn hàng `pos.order` trạng thái `paid` trên PostgreSQL `odoo20_dev`.
  - Giỏ hàng tự động làm sạch về $0.00, hàng đợi IndexedDB trống (0 pending).
  - 0 lỗi console, 0 fatal exceptions.
  - Ảnh thực nghiệm: `pos_react_live_verified.png`, `pos_react_cart_interactive.png`, `pos_react_payment_completed.png`.

### 8.4. Nâng Cấp Advanced Parity (2026-10-13)
- **Multi-Order Tabs**: Quản lý nhiều đơn hàng đồng thời trong phiên làm việc với thanh tab ngang mượt mà, chuyển đổi qua lại tức thời không mất dữ liệu giỏ hàng.
- **Tactile Ergonomic Numpad**: Bàn phím số 4x4 chuẩn công nghiệp hỗ trợ 3 chế độ (`Qty`, `% Disc`, `Price`), phím chuyển dấu âm dương `+/-`, và phím xóa lùi `⌫`.
- **Restaurant Floor Plan & Table Selection (Epic 7)**: Hỗ trợ sơ đồ mặt bằng tầng và phòng VIP, gán đơn hàng vào từng bàn ăn với số lượng khách (`TableChip` trong giỏ hàng).
- **Kitchen Order Dispatching & Prep Display (Epic 8)**: Gửi lệnh gọi món trực tiếp vào bếp (`pos.prep.order`), hiển thị nhãn `KITCHEN SENT` và màn hình chuẩn bị món (`kitchen_display.js`).
- **Dedicated Split Payment Screen**: Màn hình thanh toán chuyên dụng chia tách 3 cột trực quan (Tóm tắt đơn, Numpad tiền lẻ nhận nhanh, Phương thức thanh toán), hỗ trợ tách hóa đơn và hoàn tiền.
- **Thermal Receipt Preview & Printing**: Mẫu hóa đơn nhiệt chuẩn 80mm tối ưu typography monospaced cho máy in POS nhiệt (`@media print` clean layout).
- **Playwright Advanced Parity Test Suite**: `node tools/test_pos_react_advanced_parity.js` -> **100% PASS (Zero Console Errors)**.


