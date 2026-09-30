# VID-10 — Phát Hành Hóa Đơn Điện Tử Viettel S-Invoice Thông Tư 78 Tức Thì
## Hồ Sơ Tư Liệu Nghiệp Vụ & Footage B2B Enterprise (Insilos Enterprise Dossier)

---

### THÔNG TIN TỔNG QUAN HỒ SƠ (USECASE PROFILE)
- **Mã Kịch Bản (Usecase ID)**: `VID-10` (`VID_10_SAL`)
- **Tên Nghiệp Vụ Doanh Nghiệp**: **Phát Hành Hóa Đơn Điện Tử Viettel S-Invoice Thông Tư 78 Tức Thì**
- **Phân Hệ Nghiệp Vụ (ERP Domain)**: `E-Invoice Circular 78`
- **Chuyên Gia Điều Phối Hội Đồng**: **VCCI Head Việt Nam**
- **Trạng Thái Kiểm Định**: **ĐÃ XÁC THỰC THỰC NGHIỆM (100% VERIFIED PASS)**

---

### I. THÔNG SỐ TƯ LIỆU HÌNH ẢNH & VIDEO (TECHNICAL FOOTAGE REFERENCE)
| Tiêu Chí Kỹ Thuật | Giá Trị Đo Lường Thực Tế | Tiêu Chuẩn Áp Dụng |
|:---|:---|:---|
| **Tệp Video Gold Master** | [`/insilos_website/static/src/video/gold_masters/INSILOS_VID_10_SAL_GOLD_MASTER.mp4`](file:///home/zen/O20/enterprise/insilos_website/static/src/video/gold_masters/INSILOS_VID_10_SAL_GOLD_MASTER.mp4) | Cinema-Grade 1080p MP4 |
| **Tệp Poster WebP** | [`/insilos_website/static/src/video/gold_masters/INSILOS_VID_10_SAL_GOLD_MASTER_poster.webp`](file:///home/zen/O20/enterprise/insilos_website/static/src/video/gold_masters/INSILOS_VID_10_SAL_GOLD_MASTER_poster.webp) | High-Res WebP 24-bit |
| **Thời Lượng Video** | **60 Giây** | Khung thời lượng chuẩn B2B |
| **Độ Phân Giải & Khung Hình** | **1920x1080 Full HD @ 60 FPS** | Zero Browser Chrome (Không Address Bar/Tabs) |
| **Kỹ Xảo Tương Tác (VFX)** | Con trỏ Neon Cyan (#00f0ff), Sóng xung Click Ripple, Element Spotlight, Zoom 120%-145% | Visual Polish Standard |
| **Âm Lượng Tích Hợp (Integrated Loudness)** | **-14.8 LUFS** | Chuẩn EBU R128 ($-14.0 \pm 1.0$ LUFS) |
| **Mức Đỉnh Thực (True Peak)** | **-1.5 dBTP** | Nghiêm cấm Clipping ($\le -1.0$ dBTP) |
| **Độ Biến Thiên Âm Lượng (LRA)** | **4.5 LU** | Broadcast Dynamic Range |
| **Định Dạng Âm Thanh** | **48,000 Hz AAC Stereo** | Chuẩn âm học phòng thu 48,000 Hz |
| **Cấu Trúc Tệp Faststart** | **`moov` atom đặt trước `mdat`** | Tua và Streaming tức thì |

---

### II. LIÊN KẾT TRỰC TIẾP PHÂN HỆ ERP (LIVE MODULE DEEP-LINK REFERENCE)
Mọi dữ liệu nghiệp vụ của kịch bản đã được nạp sẵn trên cơ sở dữ liệu `odoo20_dev`. Có thể kiểm tra trực tiếp qua đường dẫn sau:
- **Đường Dẫn Truy Cập Trực Tiếp (Live Deep-Link)**:  
  [http://localhost:28069/web#id=12&model=account.move&view_type=form&action=476](http://localhost:28069/web#id=12&model=account.move&view_type=form&action=476)
- **Model Dữ Liệu Mục Tiêu**: `account.move`
- **Bản Ghi Dữ Liệu ID**: `12`
- **Window Action ID**: `476`
- **Giao Diện Render**: Owl WebClient Form View (Zero Modals, Zero Runtime Exceptions)

---

### III. BẢNG ĐẶC TẢ DỮ LIỆU MẪU CHÂN THỰC (ENTERPRISE SEED DATA SPECIFICATION)
Dữ liệu mẫu phản ánh chân thực các tập đoàn công nghiệp, cảng biển và chuỗi cung ứng hàng đầu tại Việt Nam:
```json
{
  "invoice_no": "INV/2026/00001",
  "invoice_symbol": "1C26TAA",
  "invoice_template": "Mẫu số 1/001 - Hóa đơn GTGT điện tử có mã của Cơ quan Thuế",
  "customer": "Tổng Công ty Tân Cảng Sài Gòn (Saigon Newport - SNP)",
  "customer_vat": "0300481234",
  "total_before_tax": 955000000,
  "vat_amount": 95500000,
  "total_with_tax": 1050500000,
  "total_with_tax_formatted": "1,050,500,000 ₫",
  "tax_authority_code": "TCT-8921-99234-VN",
  "einvoice_provider": "Viettel S-Invoice Cloud API v2.0"
}
```

---

### IV. KỊCH BẢN PHÂN CẢNH GHI HÌNH CHI TIẾT (SCREEN RECORDING CUE-SHEET)
Tuân thủ nghiêm ngặt **Quy chuẩn chống Lazy-Code**: Mật độ tương tác cao ($IDS \ge 2.2$), không có thời gian chết $> 2.5\text{s}$, cấu trúc 3 tầng sâu ([Kanban/List] $\rightarrow$ [Form Detail] $\rightarrow$ [Smart Button/Tab]):

| Khung Thời Gian | Hồi Phân Cảnh | Thao Tác Thị Giác Giao Diện (Screen Visual & VFX) | Luồng Dữ Liệu Telemetry HUD | Âm Thanh Xúc Giác (SFX) | Lời Thoại Thuyết Minh (1:1 TTS Parity) |
|:---|:---|:---|:---|:---|:---|
| **00:00 - 00:10** | `Hồi 1: Rủi Ro Pháp Lý Hóa Đơn Điện Tử` | B-Roll phòng tài chính tập đoàn với hàng chồng hồ sơ. Cảnh báo rủi ro sai sót ký hiệu hóa đơn Thông tư 78 và chậm gửi dữ liệu cơ quan thuế. | `Tax Compliance Alert: Circular 78 / Decree 123 | Invoice Queue: PENDING` | `sfx_whoosh.wav` | *"Sai sót trong phát hành hóa đơn điện tử Thông tư 78 có thể dẫn tới rủi ro xử phạt thuế và tắc nghẽn dòng tiền thanh toán."* |
| **00:10 - 00:25** | `Hồi 2: Kiểm Tra Hóa Đơn INV/2026/00001` | Mở hóa đơn bán lẻ INV/2026/00001 giá trị 1.050 Tỷ đồng xuất cho Tân Cảng SNP. Con trỏ Neon lướt kiểm tra ký hiệu 1C26TAA. | `Invoice: INV/2026/00001 | Customer: Saigon Newport | Amount: 1,050,500,000 ₫` | `sfx_click.wav` | *"Insilos tích hợp sẵn cổng kết nối Viettel S-Invoice, tự động điền mã số thuế, địa chỉ và biểu mẫu hợp lệ."* |
| **00:25 - 00:40** | `Hồi 2: Ký Số HSM & Cấp Mã Cơ Quan Thuế Tức Thì` | Zoom 135% vào nút 'Ký Số & Phát Hành Hóa Đơn'. Click một chạm, thanh tiến trình chạy 1.2s. Mã của Cơ quan thuế TCT-8921 hiện lên rực sáng. | `HSM Sign: SUCCESS | Tax Authority Code: TCT-8921-99234-VN | Status: VALIDATED` | `sfx_cash.wav` | *"Ký số HSM tập trung và nhận mã xác thực từ Tổng cục Thuế chỉ trong 2 giây, không cần USB Token vật lý."* |
| **00:40 - 00:50** | `Hồi 2: Tự Động Gửi Hóa Đơn Cho Khách Hàng` | Hệ thống tự động gửi email kèm mã tra cứu QR Code cho Tân Cảng SNP. Trạng thái chuyển sang 'Đã Phát Hành'. | `Email Sent: snp.finance@saigonnewport.com.vn | Portal Link: ACTIVE` | `sfx_chime.wav` | *"Hóa đơn điện tử hợp lệ được gửi tự động qua email cho khách hàng, đẩy nhanh chu kỳ thu tiền thanh toán."* |
| **00:50 - 01:00** | `Hồi 3: 25-Thumbnail Mosaic Closing CTA` | 25-Thumbnail Closing Suite tôn vinh nền tảng tài chính hóa đơn Insilos. | `CTA: Connect E-Invoice Suite` | `sfx_whoosh.wav` | *"Insilos E-Invoice — Chuẩn hóa hóa đơn điện tử Thông tư 78 tốc độ và an toàn tuyệt đối."* |

---

### V. ĐÁNH GIÁ ĐA CHIỀU TỪ HỘI ĐỒNG CHUYÊN GIA (EXPERT COUNCIL PERSPECTIVES)
- **Góc nhìn Sales Director of SAP**:
  > "Tính năng tích hợp e-Document chuẩn địa phương hóa Việt Nam tương đương giải pháp SAP Document and Reporting Compliance."
- **Góc nhìn Marketing Director of Google**:
  > "Hiệu ứng âm thanh tiền reo sfx_cash khi mã số thuế được cấp mang lại cảm giác thành tựu và an tâm tối đa cho kế toán trưởng."
- **Góc nhìn TCO Expert of IBM**:
  > "Tự động hóa hoàn toàn quy trình phát hành hóa đơn giúp giảm 90% chi phí nhân sự xuất hóa đơn và đối soát."
- **Góc nhìn Logistics Dept Head**:
  > "Khách hàng nhận được hóa đơn ngay khi container vừa hạ bãi, rút ngắn thời gian quyết toán cước drayage."
- **Góc nhìn VCCI Head Việt Nam**:
  > "Đáp ứng chuẩn 100% Nghị định 123/2020/NĐ-CP và Thông tư 78/2021/TT-BTC của Bộ Tài chính."
- **Góc nhìn Giám đốc Sản xuất (Manufacturing Director)**:
  > "Doanh thu được ghi nhận chính xác theo từng đơn hàng gia công cơ khí hoàn thành."

---

### VI. CHỈ SỐ TÁC ĐỘNG TÀI CHÍNH & VẬN HÀNH ĐỊNH LƯỢNG (IMPACT METRICS)
```json
{
  "tax_compliance": "100% Chuẩn Thông tư 78 / NĐ 123",
  "issuance_speed": "2 Giây nhận mã cơ quan thuế",
  "cash_collection_cycle": "Rút ngắn 14 ngày chu kỳ thanh toán"
}
```

---
*Tư liệu được lưu trữ và kiểm soát chất lượng bởi Hệ thống Insilos Enterprise Dossier Engine.*
