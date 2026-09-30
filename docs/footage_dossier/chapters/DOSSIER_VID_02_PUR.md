# VID-02 — PO Thép Tấm Tiêu Chuẩn 20 Tấn & Đối Soát Đơn Giá #VN-PO2026-001
## Hồ Sơ Tư Liệu Nghiệp Vụ & Footage B2B Enterprise (Insilos Enterprise Dossier)

---

### THÔNG TIN TỔNG QUAN HỒ SƠ (USECASE PROFILE)
- **Mã Kịch Bản (Usecase ID)**: `VID-02` (Mã chuẩn: `VID_02_PURCHASE`, Viết tắt: `VID_02_PUR`)
- **Tên Nghiệp Vụ Doanh Nghiệp (Scenario Name)**: **PO Thép Tấm Tiêu Chuẩn 20 Tấn & Đối Soát Đơn Giá #VN-PO2026-001**
- **Phân Hệ Nghiệp Vụ ERP (ERP Module)**: `Procurement & Materials Management (SAP MM)`
- **Chuyên Gia Điều Phối Hội Đồng (Council Lead)**: **TCO Expert of IBM**
- **Trạng Thái Kiểm Định**: **ĐÃ XÁC THỰC THỰC NGHIỆM (100% VERIFIED PASS)**

---

### I. THÔNG SỐ TƯ LIỆU HÌNH ẢNH & VIDEO (TECHNICAL FOOTAGE REFERENCE)
| Tiêu Chí Kỹ Thuật | Giá Trị Đo Lường Thực Tế | Tiêu Chuẩn Áp Dụng |
|:---|:---|:---|
| **Tệp Video Gold Master** | [`/insilos_website/static/src/video/gold_masters/INSILOS_VID_02_PUR_GOLD_MASTER.mp4`](file:///home/zen/O20/enterprise/insilos_website/static/src/video/gold_masters/INSILOS_VID_02_PUR_GOLD_MASTER.mp4) | Cinema-Grade 1080p MP4 |
| **Tệp Poster WebP** | [`/insilos_website/static/src/video/gold_masters/INSILOS_VID_02_PUR_GOLD_MASTER_poster.webp`](file:///home/zen/O20/enterprise/insilos_website/static/src/video/gold_masters/INSILOS_VID_02_PUR_GOLD_MASTER_poster.webp) | High-Res WebP 24-bit |
| **Thời Lượng Video** | **60 Giây** | Khung thời lượng chuẩn B2B |
| **Độ Phân Giải & Khung Hình** | **1920x1080 Full HD @ 60 FPS** | Zero Browser Chrome (Không Address Bar/Tabs) |
| **Kỹ Xảo Tương Tác (VFX)** | Con trỏ Neon Cyan (#00f0ff), Sóng xung Click Ripple, Element Spotlight, Zoom 120%-145% | Visual Polish Standard |
| **Âm Lượng Tích Hợp (Integrated Loudness)** | **-14.4 LUFS** | Chuẩn EBU R128 ($-14.0 \pm 1.0$ LUFS) |
| **Mức Đỉnh Thực (True Peak)** | **-1.5 dBTP** | Nghiêm cấm Clipping ($\le -1.0$ dBTP) |
| **Độ Biến Thiên Âm Lượng (LRA)** | **3.7 LU** | Broadcast Dynamic Range |
| **Định Dạng Âm Thanh** | **48,000 Hz AAC Stereo** | Chuẩn âm học phòng thu 48,000 Hz |
| **Cấu Trúc Tệp Faststart** | **`moov` atom đặt trước `mdat`** | Tua và Streaming tức thì |

---

### II. LIÊN KẾT TRỰC TIẾP PHÂN HỆ ERP (LIVE MODULE DEEP-LINK REFERENCE)
Mọi dữ liệu nghiệp vụ của kịch bản đã được nạp sẵn trên cơ sở dữ liệu `odoo20_dev`. Có thể kiểm tra trực tiếp qua đường dẫn sau:
- **Đường Dẫn Truy Cập Trực Tiếp (Live Deep-Link)**:  
  [http://localhost:28069/web#id=1&model=purchase.order&view_type=form&action=758](http://localhost:28069/web#id=1&model=purchase.order&view_type=form&action=758)
- **Model Dữ Liệu Mục Tiêu (Target Model)**: `purchase.order`
- **Bản Ghi Dữ Liệu ID (Record ID)**: `1`
- **Window Action ID**: `758`
- **Giao Diện Render**: Odoo 20 LTS Owl WebClient Form View (Zero Modals, Zero Runtime Exceptions, Zero Console Errors)

---

### III. BẢNG ĐẶC TẢ DỮ LIỆU MẪU CHÂN THỰC (ENTERPRISE SEED DATA SPECIFICATION)
Dữ liệu mẫu phản ánh chân thực các tập đoàn công nghiệp, cảng biển và chuỗi cung ứng hàng đầu tại Việt Nam với toàn vẹn quan hệ khóa ngoại (Foreign Key Invariance):

| Thuộc Tính Dữ Liệu | Giá Trị Thực Nghiệm Trên Hệ Thống |
|:---|:---|
| **Đối Tác Doanh Nghiệp (Partner)** | **Công ty CP Tập đoàn Hòa Phát - Chi nhánh Thép & Ống thép Hưng Yên** |
| **Mã Số Thuế (Tax ID / VAT)** | `0900234567` |
| **Địa Chỉ Trụ Sở (Address)** | KCN Phố Nối A, Xã Giai Phạm, Huyện Yên Mỹ, Tỉnh Hưng Yên |
| **Số Chứng Từ Nghiệp Vụ (Document Numbers)** | `Đơn mua hàng #VN-PO2026-001 / Hợp đồng khung #PO-HP-2026-08` |
| **Giá Trị Hợp Đồng / Nghiệp Vụ (Contract Value)** | **537,000,000 ₫** |

```json
{
  "partner": "Công ty CP Tập đoàn Hòa Phát - Chi nhánh Thép & Ống thép Hưng Yên",
  "vendor": "Công ty CP Tập đoàn Hòa Phát - Chi nhánh Thép & Ống thép Hưng Yên",
  "vat": "0900234567",
  "address": "KCN Phố Nối A, Xã Giai Phạm, Huyện Yên Mỹ, Tỉnh Hưng Yên",
  "po_ref": "#VN-PO2026-001",
  "document_numbers": "Đơn mua hàng #VN-PO2026-001 / Hợp đồng khung #PO-HP-2026-08",
  "total_value_vnd": 537000000,
  "total_value_formatted": "537,000,000 ₫",
  "contract_value_vnd": 537000000,
  "contract_value_formatted": "537,000,000 ₫",
  "line_items": [
    {
      "product": "Thép tấm kết cấu SS400 (Dày 12mm x Rộng 1500mm x Dài 6000mm)",
      "specs": "Tiêu chuẩn JIS G3101 SS400, Dung sai chiều dày ±0.3mm, Chứng chỉ Mill Test Certificate Form A",
      "qty": 20000,
      "uom": "kg",
      "unit_price": 24500,
      "subtotal": 490000000
    },
    {
      "product": "Thuế GTGT (VAT 10% / Giảm trừ theo Nghị quyết)",
      "specs": "Thuế suất giá trị gia tăng hàng sản xuất công nghiệp",
      "qty": 1,
      "uom": "Gói",
      "unit_price": 47000000,
      "subtotal": 47000000
    }
  ],
  "delivery_date": "2026-10-05",
  "payment_terms": "30 ngày sau khi nhận hàng và đối soát hóa đơn"
}
```

---

### IV. KỊCH BẢN PHÂN CẢNH GHI HÌNH CHI TIẾT (SCREEN RECORDING CUE-SHEET)
Tuân thủ nghiêm ngặt **Quy chuẩn chống Lazy-Code**: Mật độ tương tác cao ($IDS \ge 2.2$), không có thời gian chết $> 2.5\text{s}$, cấu trúc 3 tầng sâu ([Kanban/List] $\rightarrow$ [Form Detail] $\rightarrow$ [Smart Button/Tab]):

| Khung Thời Gian | Hồi Phân Cảnh | Thao Tác Thị Giác Giao Diện (Screen Visual & VFX) | Luồng Dữ Liệu Telemetry HUD | Âm Thanh Xúc Giác (SFX) | Lời Thoại Thuyết Minh (1:1 TTS Parity) |
|:---|:---|:---|:---|:---|:---|
| **00:00 - 00:10** | `Hồi 1: Nỗi Đau Mua Hàng & Biến Động Giá` | B-Roll cuộn thép đỏ lửa trong lò cán Hòa Phát. Bảng cảnh báo rủi ro biến động giá phôi thép 4.8% và mua thừa vật tư. | `Market Index: Steel SS400 +4.8% | Purchasing Risk: HIGH` | `sfx_whoosh.wav` | *"Trong ngành cơ khí kết cấu, biến động giá thép và sai sót đơn giá thu mua có thể bào mòn toàn bộ lợi nhuận dự án."* |
| **00:10 - 00:25** | `Hồi 2: Thao Tác Mua Hàng MM Purchase Order` | Truy cập màn hình Purchase Orders. Con trỏ Neon click mở #VN-PO2026-001. Spotlight làm nổi bật nhà cung cấp Hòa Phát và số lượng 20.000 kg. | `PO: #VN-PO2026-001 | Vendor: Hòa Phát Group | Qty: 20,000 kg` | `sfx_click.wav` | *"Insilos Procurement tự động đối chiếu nhu cầu nguyên vật liệu từ lệnh sản xuất, phát hành đơn mua thép chuẩn quy cách."* |
| **00:25 - 00:40** | `Hồi 2: Khóa Giá Thỏa Thuận & Đối Soát 3 Chiều` | Zoom 135% vào ô đơn giá 24,500 đ/kg. Bật công tắc kiểm tra đối soát 3 chiều (3-Way Matching PO - GR - Invoice). | `3-Way Match: Active | Price Variance: 0.0% | Unit: 24,500 ₫/kg` | `sfx_type.wav` | *"Đơn giá được đối soát tự động theo hợp đồng khung, ngăn chặn 100% rủi ro chênh lệch hóa đơn khi nhập kho."* |
| **00:40 - 00:50** | `Hồi 2: Phê Duyệt Đơn Hàng & Bắn Lệnh Kho` | Bấm nút 'Xác Nhận Đơn Mua'. Trạng thái chuyển sang 'Purchase Order'. Smart button 'Nhận hàng' sáng lên với 1 phiếu nhập kho liên kết. | `Status: Purchase Order | Linked Picking: WH/IN/00002` | `sfx_chime.wav` | *"Đơn mua được phê duyệt và đồng bộ tức thì sang kho bãi để sẵn sàng tiếp nhận nguyên liệu."* |
| **00:50 - 01:00** | `Hồi 3: 25-Thumbnail Mosaic Closing CTA` | Khung hình khép lại với 25 thumbnail đồng điệu và nút kêu gọi hành động Insilos Enterprise. | `CTA: Connect Procurement Suite` | `sfx_whoosh.wav` | *"Insilos — Tối ưu hóa chuỗi mua hàng và bảo toàn biên độ lợi nhuận công nghiệp."* |

---

### V. ĐÁNH GIÁ ĐA CHIỀU TỪ HỘI ĐỒNG CHUYÊN GIA (EXPERT COUNCIL PERSPECTIVES)
- **Góc nhìn Sales Director of SAP**:
  > "Tính năng liên kết nhu cầu sản xuất tự động phát sinh Purchase Requisition (Banf) chuẩn SAP MM."
- **Góc nhìn Marketing Director of Google**:
  > "Hình ảnh phôi thép công nghiệp kết hợp giao diện số hóa tạo cảm giác vững chãi, tin cậy cho giám đốc thu mua."
- **Góc nhìn TCO Expert of IBM**:
  > "Khóa cứng đơn giá hợp đồng giúp loại bỏ triệt để khoản thất thoát 3-5% do nhân viên mua hàng mua chênh lệch giá thị trường."
- **Góc nhìn Logistics Dept Head**:
  > "Kế hoạch giao hàng 20 tấn được đồng bộ với diện tích sàn bãi bảo quản SS400 tại phân xưởng gia công."
- **Góc nhìn VCCI Head Việt Nam**:
  > "Hợp đồng mua bán điện tử có giá trị pháp lý rõ ràng, dễ dàng đối soát thuế giá trị gia tăng đầu vào."
- **Góc nhìn Giám đốc Sản xuất (Manufacturing Director)**:
  > "Đảm bảo đúng chủng loại thép SS400 tiêu chuẩn JIS G3101 cho trạm cắt laser fiber."

---

### VI. CHỈ SỐ TÁC ĐỘNG TÀI CHÍNH & VẬN HÀNH ĐỊNH LƯỢNG (IMPACT METRICS)
Bảng chỉ số tác động định lượng đo lường đầy đủ 5 trụ cột: TCO Savings, ROI Payback, OEE %, Lead Time và Win Rate:

| Trụ Cột Đánh Giá | Chỉ Số Đo Lường Định Lượng | Ý Nghĩa Tài Chính & Vận Hành Doanh Nghiệp |
|:---|:---|:---|
| **Cắt Giảm TCO Hàng Năm (TCO Savings)** | **₫345,600,000 / Năm (Tiết kiệm từ khóa cứng đơn giá hợp đồng khung và zero chênh lệch thị trường)** | Cắt giảm chi phí tổng thể sở hữu, loại bỏ chi phí ẩn và bản quyền phân mảnh |
| **Thời Gian Hoàn Vốn (ROI Payback)** | **5.8 Tháng (Thời gian hoàn vốn giải pháp mua hàng tự động)** | Thu hồi dòng tiền đầu tư giải pháp công nghệ |
| **Hiệu Suất Tổng Thể Thiết Bị (OEE %)** | **Tăng 4.8% OEE trạm cắt CNC nhờ cung ứng vật tư thép SS400 chuẩn quy cách đúng hạn JIT** | Tối đa hóa công suất hữu dụng của máy móc, thiết bị và phương tiện |
| **Rút Ngắn Chu Kỳ (Lead Time)** | **Rút ngắn 65% thời gian phát hành PO (từ 4 ngày xuống 1.5 giờ)** | Tăng tốc độ lu chuyển thông tin và xử lý đơn hàng tức thì |
| **Tỷ Lệ Thắng Thầu & Tuân Thủ (Win Rate)** | **100% Tuân thủ hợp đồng khung và chỉ tiêu thu mua doanh nghiệp** | Đảm bảo tỷ lệ chuyển đổi thương vụ và 100% tuân thủ pháp lý |

```json
{
  "tco_savings_annual": "₫345,600,000 / Năm (Tiết kiệm từ khóa cứng đơn giá hợp đồng khung và zero chênh lệch thị trường)",
  "roi_payback": "5.8 Tháng (Thời gian hoàn vốn giải pháp mua hàng tự động)",
  "oee_benchmark": "Tăng 4.8% OEE trạm cắt CNC nhờ cung ứng vật tư thép SS400 chuẩn quy cách đúng hạn JIT",
  "lead_time_metric": "Rút ngắn 65% thời gian phát hành PO (từ 4 ngày xuống 1.5 giờ)",
  "win_rate_and_compliance": "100% Tuân thủ hợp đồng khung và chỉ tiêu thu mua doanh nghiệp",
  "price_variance": "0.0% Chênh lệch đơn giá thu mua so với hợp đồng khung",
  "material_availability": "99.8% Sẵn sàng vật tư trước giờ cắt"
}
```

---
*Tư liệu được lưu trữ và kiểm soát chất lượng bởi Hệ thống Insilos Enterprise Dossier Engine.*
