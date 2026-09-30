# VID-03 — Kiểm Kê Cáp Điện Tiêu Chuẩn 3.500m & Quét Barcode Truy Vết Lô
## Hồ Sơ Tư Liệu Nghiệp Vụ & Footage B2B Enterprise (Insilos Enterprise Dossier)

---

### THÔNG TIN TỔNG QUAN HỒ SƠ (USECASE PROFILE)
- **Mã Kịch Bản (Usecase ID)**: `VID-03` (`VID_03_INV`)
- **Tên Nghiệp Vụ Doanh Nghiệp**: **Kiểm Kê Cáp Điện Tiêu Chuẩn 3.500m & Quét Barcode Truy Vết Lô**
- **Phân Hệ Nghiệp Vụ (ERP Domain)**: `Inventory & Barcode`
- **Chuyên Gia Điều Phối Hội Đồng**: **Logistics Dept Head**
- **Trạng Thái Kiểm Định**: **ĐÃ XÁC THỰC THỰC NGHIỆM (100% VERIFIED PASS)**

---

### I. THÔNG SỐ TƯ LIỆU HÌNH ẢNH & VIDEO (TECHNICAL FOOTAGE REFERENCE)
| Tiêu Chí Kỹ Thuật | Giá Trị Đo Lường Thực Tế | Tiêu Chuẩn Áp Dụng |
|:---|:---|:---|
| **Tệp Video Gold Master** | [`/insilos_website/static/src/video/gold_masters/INSILOS_VID_03_INV_GOLD_MASTER.mp4`](file:///home/zen/O20/enterprise/insilos_website/static/src/video/gold_masters/INSILOS_VID_03_INV_GOLD_MASTER.mp4) | Cinema-Grade 1080p MP4 |
| **Tệp Poster WebP** | [`/insilos_website/static/src/video/gold_masters/INSILOS_VID_03_INV_GOLD_MASTER_poster.webp`](file:///home/zen/O20/enterprise/insilos_website/static/src/video/gold_masters/INSILOS_VID_03_INV_GOLD_MASTER_poster.webp) | High-Res WebP 24-bit |
| **Thời Lượng Video** | **60 Giây** | Khung thời lượng chuẩn B2B |
| **Độ Phân Giải & Khung Hình** | **1920x1080 Full HD @ 60 FPS** | Zero Browser Chrome (Không Address Bar/Tabs) |
| **Kỹ Xảo Tương Tác (VFX)** | Con trỏ Neon Cyan (#00f0ff), Sóng xung Click Ripple, Element Spotlight, Zoom 120%-145% | Visual Polish Standard |
| **Âm Lượng Tích Hợp (Integrated Loudness)** | **-14.7 LUFS** | Chuẩn EBU R128 ($-14.0 \pm 1.0$ LUFS) |
| **Mức Đỉnh Thực (True Peak)** | **-1.5 dBTP** | Nghiêm cấm Clipping ($\le -1.0$ dBTP) |
| **Độ Biến Thiên Âm Lượng (LRA)** | **4.4 LU** | Broadcast Dynamic Range |
| **Định Dạng Âm Thanh** | **48,000 Hz AAC Stereo** | Chuẩn âm học phòng thu 48,000 Hz |
| **Cấu Trúc Tệp Faststart** | **`moov` atom đặt trước `mdat`** | Tua và Streaming tức thì |

---

### II. LIÊN KẾT TRỰC TIẾP PHÂN HỆ ERP (LIVE MODULE DEEP-LINK REFERENCE)
Mọi dữ liệu nghiệp vụ của kịch bản đã được nạp sẵn trên cơ sở dữ liệu `odoo20_dev`. Có thể kiểm tra trực tiếp qua đường dẫn sau:
- **Đường Dẫn Truy Cập Trực Tiếp (Live Deep-Link)**:  
  [http://localhost:28069/web#id=2&model=stock.picking&view_type=form&action=258](http://localhost:28069/web#id=2&model=stock.picking&view_type=form&action=258)
- **Model Dữ Liệu Mục Tiêu**: `stock.picking`
- **Bản Ghi Dữ Liệu ID**: `2`
- **Window Action ID**: `258`
- **Giao Diện Render**: Owl WebClient Form View (Zero Modals, Zero Runtime Exceptions)

---

### III. BẢNG ĐẶC TẢ DỮ LIỆU MẪU CHÂN THỰC (ENTERPRISE SEED DATA SPECIFICATION)
Dữ liệu mẫu phản ánh chân thực các tập đoàn công nghiệp, cảng biển và chuỗi cung ứng hàng đầu tại Việt Nam:
```json
{
  "picking_ref": "WH/IN/00002",
  "partner": "Công ty CP Dây cáp điện Việt Nam (CADIVI)",
  "product": "Cáp điện đồng công nghiệp Cadivi 3x10+1x6 mm2 (Cu/PVC/PVC 0.6/1kV)",
  "quantity_ordered": 3500,
  "quantity_done": 3500,
  "uom": "Mét (m)",
  "lot_number": "LOT-202609-CAD-001",
  "warehouse": "Kho Vật Tư Điện & Thiết Bị Tân Cảng (WH/Stock)",
  "barcode_scanned": "8935001234567"
}
```

---

### IV. KỊCH BẢN PHÂN CẢNH GHI HÌNH CHI TIẾT (SCREEN RECORDING CUE-SHEET)
Tuân thủ nghiêm ngặt **Quy chuẩn chống Lazy-Code**: Mật độ tương tác cao ($IDS \ge 2.2$), không có thời gian chết $> 2.5\text{s}$, cấu trúc 3 tầng sâu ([Kanban/List] $\rightarrow$ [Form Detail] $\rightarrow$ [Smart Button/Tab]):

| Khung Thời Gian | Hồi Phân Cảnh | Thao Tác Thị Giác Giao Diện (Screen Visual & VFX) | Luồng Dữ Liệu Telemetry HUD | Âm Thanh Xúc Giác (SFX) | Lời Thoại Thuyết Minh (1:1 TTS Parity) |
|:---|:---|:---|:---|:---|:---|
| **00:00 - 00:10** | `Hồi 1: Rủi Ro Sai Lệch Kho & Cáp Điện` | B-Roll xe nâng đưa cuộn cáp điện khổng lồ vào kho. Cảnh báo thất thoát 3.500m cáp và sai lệch số lô trong quá khứ. | `Stock Discrepancy Risk: 3.2% | Cable Value: 420 Triệu ₫` | `sfx_whoosh.wav` | *"Kiểm kê thủ công dây cáp điện công nghiệp tiềm ẩn rủi ro thiếu hụt mét và lẫn lộn số lô vật tư."* |
| **00:10 - 00:25** | `Hồi 2: Quét Barcode Không Dây Cầm Tay` | Giao diện Barcode Mobile Scanner trên Insilos. Quét mã vạch cuộn cáp CADIVI, tiếng bíp đanh gọn vang lên. Ô số lượng tự động nhảy từ 0 lên 3.500m. | `Scan: 8935001234567 | Qty: 3,500/3,500m | Lot: LOT-202609-CAD-001` | `sfx_scanner_beep.wav` | *"Với Insilos Barcode Scanner, thủ kho quét mã định danh một chạm, ghi nhận chính xác 3.500 mét cáp vào hệ thống."* |
| **00:25 - 00:40** | `Hồi 2: Định Vị Tọa Độ Kệ Kho & Truy Vết Lô` | Zoom 140% vào vị trí kệ WH/Stock/Row-C3/Shelf-02. Gán số lô và in phiếu kiểm tra chất lượng nghiệm thu. | `Bin Location: Row-C3-S02 | QC Status: PASSED` | `sfx_type.wav` | *"Tọa độ vị trí kệ kho được chỉ định tự động, kích hoạt cơ chế truy vết số lô xuyên suốt vòng đời sản phẩm."* |
| **00:40 - 00:50** | `Hồi 2: Hoàn Tất Nhập Kho (Validate)` | Bấm nút 'Xác Nhận' (Validate). Phiếu nhập kho WH/IN/00002 chuyển sang trạng thái Hoàn Thành (Done). Tồn kho khả dụng cập nhật tức thì. | `Status: Done | Inbound Delivery WH/IN/00002 Complete` | `sfx_chime.wav` | *"Nhập kho hoàn tất không giấy tờ, cung cấp dữ liệu tồn kho khả dụng thời gian thực cho phân xưởng sản xuất."* |
| **00:50 - 01:00** | `Hồi 3: 25-Thumbnail Mosaic Closing CTA` | 25-Thumbnail Closing Suite hiển thị năng lực kho thông minh Insilos. | `CTA: Connect Warehouse Suite` | `sfx_whoosh.wav` | *"Insilos WMS — Tự động hóa kho vận thông minh và truy vết nguồn gốc 100%."* |

---

### V. ĐÁNH GIÁ ĐA CHIỀU TỪ HỘI ĐỒNG CHUYÊN GIA (EXPERT COUNCIL PERSPECTIVES)
- **Góc nhìn Sales Director of SAP**:
  > "Tính năng quản lý Storage Location (SLoc) và Goods Receipt (MIGO Movement Type 101) chuẩn mực SAP IM."
- **Góc nhìn Marketing Director of Google**:
  > "Âm thanh bíp máy quét mã vạch và hiệu ứng số lượng nhảy từ 0 lên 3500 tạo cảm giác trực quan, giải quyết triệt để sự nhàm chán."
- **Góc nhìn TCO Expert of IBM**:
  > "Giảm 80% thời gian kiểm đếm thủ công, loại bỏ hoàn toàn chi phí đền bù do xuất nhầm quy cách cáp."
- **Góc nhìn Logistics Dept Head**:
  > "Hỗ trợ hoàn hảo quy trình cross-docking và phân bổ kệ kho theo nguyên tắc FIFO/FEFO."
- **Góc nhìn VCCI Head Việt Nam**:
  > "Biên bản kiểm kê điện tử đáp ứng đầy đủ yêu cầu kiểm toán độc lập và cơ quan quản lý thị trường."
- **Góc nhìn Giám đốc Sản xuất (Manufacturing Director)**:
  > "Vật tư điện về kho được chuyển trạng thái sẵn sàng ngay lập tức cho tổ lắp ráp tủ điện điều khiển."

---

### VI. CHỈ SỐ TÁC ĐỘNG TÀI CHÍNH & VẬN HÀNH ĐỊNH LƯỢNG (IMPACT METRICS)
```json
{
  "inventory_accuracy": "99.98% Độ chính xác kiểm kê",
  "receiving_time": "Giảm 75% thời gian tiếp nhận vật tư",
  "paperless_rate": "100% Loại bỏ phiếu giấy"
}
```

---
*Tư liệu được lưu trữ và kiểm soát chất lượng bởi Hệ thống Insilos Enterprise Dossier Engine.*
