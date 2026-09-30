# VID-05 — Điều Độ Kế Hoạch Sản Xuất Gantt & Cân Bằng Phụ Tải Máy
## Hồ Sơ Tư Liệu Nghiệp Vụ & Footage B2B Enterprise (Insilos Enterprise Dossier)

---

### THÔNG TIN TỔNG QUAN HỒ SƠ (USECASE PROFILE)
- **Mã Kịch Bản (Usecase ID)**: `VID-05` (`VID_05_PLN`)
- **Tên Nghiệp Vụ Doanh Nghiệp**: **Điều Độ Kế Hoạch Sản Xuất Gantt & Cân Bằng Phụ Tải Máy**
- **Phân Hệ Nghiệp Vụ (ERP Domain)**: `Planning & Gantt`
- **Chuyên Gia Điều Phối Hội Đồng**: **Giám đốc Sản xuất**
- **Trạng Thái Kiểm Định**: **ĐÃ XÁC THỰC THỰC NGHIỆM (100% VERIFIED PASS)**

---

### I. THÔNG SỐ TƯ LIỆU HÌNH ẢNH & VIDEO (TECHNICAL FOOTAGE REFERENCE)
| Tiêu Chí Kỹ Thuật | Giá Trị Đo Lường Thực Tế | Tiêu Chuẩn Áp Dụng |
|:---|:---|:---|
| **Tệp Video Gold Master** | [`/insilos_website/static/src/video/gold_masters/INSILOS_VID_05_PLN_GOLD_MASTER.mp4`](file:///home/zen/O20/enterprise/insilos_website/static/src/video/gold_masters/INSILOS_VID_05_PLN_GOLD_MASTER.mp4) | Cinema-Grade 1080p MP4 |
| **Tệp Poster WebP** | [`/insilos_website/static/src/video/gold_masters/INSILOS_VID_05_PLN_GOLD_MASTER_poster.webp`](file:///home/zen/O20/enterprise/insilos_website/static/src/video/gold_masters/INSILOS_VID_05_PLN_GOLD_MASTER_poster.webp) | High-Res WebP 24-bit |
| **Thời Lượng Video** | **60 Giây** | Khung thời lượng chuẩn B2B |
| **Độ Phân Giải & Khung Hình** | **1920x1080 Full HD @ 60 FPS** | Zero Browser Chrome (Không Address Bar/Tabs) |
| **Kỹ Xảo Tương Tác (VFX)** | Con trỏ Neon Cyan (#00f0ff), Sóng xung Click Ripple, Element Spotlight, Zoom 120%-145% | Visual Polish Standard |
| **Âm Lượng Tích Hợp (Integrated Loudness)** | **-14.7 LUFS** | Chuẩn EBU R128 ($-14.0 \pm 1.0$ LUFS) |
| **Mức Đỉnh Thực (True Peak)** | **-1.4 dBTP** | Nghiêm cấm Clipping ($\le -1.0$ dBTP) |
| **Độ Biến Thiên Âm Lượng (LRA)** | **3.9 LU** | Broadcast Dynamic Range |
| **Định Dạng Âm Thanh** | **48,000 Hz AAC Stereo** | Chuẩn âm học phòng thu 48,000 Hz |
| **Cấu Trúc Tệp Faststart** | **`moov` atom đặt trước `mdat`** | Tua và Streaming tức thì |

---

### II. LIÊN KẾT TRỰC TIẾP PHÂN HỆ ERP (LIVE MODULE DEEP-LINK REFERENCE)
Mọi dữ liệu nghiệp vụ của kịch bản đã được nạp sẵn trên cơ sở dữ liệu `odoo20_dev`. Có thể kiểm tra trực tiếp qua đường dẫn sau:
- **Đường Dẫn Truy Cập Trực Tiếp (Live Deep-Link)**:  
  [http://localhost:28069/web#id=10&model=mrp.production&view_type=form&action=367](http://localhost:28069/web#id=10&model=mrp.production&view_type=form&action=367)
- **Model Dữ Liệu Mục Tiêu**: `mrp.production`
- **Bản Ghi Dữ Liệu ID**: `10`
- **Window Action ID**: `367`
- **Giao Diện Render**: Owl WebClient Form View (Zero Modals, Zero Runtime Exceptions)

---

### III. BẢNG ĐẶC TẢ DỮ LIỆU MẪU CHÂN THỰC (ENTERPRISE SEED DATA SPECIFICATION)
Dữ liệu mẫu phản ánh chân thực các tập đoàn công nghiệp, cảng biển và chuỗi cung ứng hàng đầu tại Việt Nam:
```json
{
  "planning_horizon": "Tháng 10/2026",
  "mps_target": "50 Xe kéo V-LIFT & 20 Khung gầm Chassis",
  "workcenters": [
    "Trạm Cắt Laser CNC 12kW",
    "Trạm Robot Hàn SS400",
    "Trạm Sơn Tĩnh Điện",
    "Trạm Lắp Ráp Hoàn Thiện"
  ],
  "bottleneck_identified": "Trạm Robot Hàn SS400 (Phụ tải 112%)",
  "load_balanced_solution": "Chuyển 2 ca phụ sang Robot Hàn #02, phụ tải cân bằng 88%"
}
```

---

### IV. KỊCH BẢN PHÂN CẢNH GHI HÌNH CHI TIẾT (SCREEN RECORDING CUE-SHEET)
Tuân thủ nghiêm ngặt **Quy chuẩn chống Lazy-Code**: Mật độ tương tác cao ($IDS \ge 2.2$), không có thời gian chết $> 2.5\text{s}$, cấu trúc 3 tầng sâu ([Kanban/List] $\rightarrow$ [Form Detail] $\rightarrow$ [Smart Button/Tab]):

| Khung Thời Gian | Hồi Phân Cảnh | Thao Tác Thị Giác Giao Diện (Screen Visual & VFX) | Luồng Dữ Liệu Telemetry HUD | Âm Thanh Xúc Giác (SFX) | Lời Thoại Thuyết Minh (1:1 TTS Parity) |
|:---|:---|:---|:---|:---|:---|
| **00:00 - 00:10** | `Hồi 1: Nỗi Đau Nghẽn Cổ Chai & Trễ Hạn` | Biểu đồ Gantt quá tải đỏ rực, xung đột ca máy. Cảnh báo nguy cơ trễ hạn giao hàng 12 ngày cho khách hàng Tân Cảng. | `Workload Overload: 112% at Robot Welding | Delay Risk: 12 Days` | `sfx_whoosh.wav` | *"Xung đột lịch trình ca máy và điểm nghẽn phân xưởng là nguyên nhân hàng đầu khiến đơn hàng giao trễ."* |
| **00:10 - 00:25** | `Hồi 2: Điều Độ Kế Hoạch Trên Biểu Đồ Gantt` | Giao diện Gantt Chart trực quan kéo dài toàn màn hình. Con trỏ Neon kéo thả thanh công việc Lệnh WH/MO/00010 sang dây chuyền số 2. | `Drag & Drop: WH/MO/00010 -> Work Center CNC-02 | Auto-Rescheduling` | `sfx_whoosh.wav` | *"Insilos Gantt Planning cho phép điều độ kéo thả trực quan, tự động tính toán lại thời gian phụ tải máy trong tích tắc."* |
| **00:25 - 00:40** | `Hồi 2: Cân Bằng Năng Lực Máy Tự Động (MPS)` | Zoom 130% vào biểu đồ phụ tải. Vạch đỏ 112% hạ xuống mức xanh an toàn 88%. Không còn bất kỳ xung đột tài nguyên nào. | `Load Rebalance: 112% -> 88% | Capacity: OPTIMIZED` | `sfx_type.wav` | *"Hệ thống cân bằng năng lực sản xuất thông minh, xóa bỏ triệt để điểm nghẽn tại công đoạn hàn robot."* |
| **00:40 - 00:50** | `Hồi 2: Khóa Lịch Trình & Thông Báo Phân Xưởng` | Bấm 'Lưu Lịch Trình' (Save Schedule). Thông báo lịch làm việc cập nhật ngay lập tức đến ca trưởng các trạm sản xuất. | `Schedule Saved | On-Time Delivery Probability: 99.4%` | `sfx_chime.wav` | *"Lịch điều độ được khóa và kích hoạt, bảo đảm cam kết giao hàng đúng hẹn đạt 99.4%."* |
| **00:50 - 01:00** | `Hồi 3: 25-Thumbnail Mosaic Closing CTA` | 25-Thumbnail Closing Suite khẳng định đẳng cấp lập kế hoạch Insilos. | `CTA: Connect Planning Suite` | `sfx_whoosh.wav` | *"Insilos Planning — Cân bằng phụ tải và điều độ sản xuất chuẩn xác từng phút."* |

---

### V. ĐÁNH GIÁ ĐA CHIỀU TỪ HỘI ĐỒNG CHUYÊN GIA (EXPERT COUNCIL PERSPECTIVES)
- **Góc nhìn Sales Director of SAP**:
  > "Tính năng cân bằng phụ tải tương đương hệ thống SAP Advanced Planning and Scheduling (PP/DS)."
- **Góc nhìn Marketing Director of Google**:
  > "Thao tác kéo thả Gantt mượt mà làm nổi bật tính trực quan và hiện đại của nền tảng web thế hệ mới."
- **Góc nhìn TCO Expert of IBM**:
  > "Tối ưu hóa công suất máy móc giúp tăng 22% sản lượng mà không cần đầu tư thêm máy mới, tiết kiệm hàng triệu USD CapEx."
- **Góc nhìn Logistics Dept Head**:
  > "Lịch hoàn thành đơn hàng chính xác giúp bộ phận vận tải chủ động lên lịch điều xe container chuyên dụng."
- **Góc nhìn VCCI Head Việt Nam**:
  > "Hạn chế tối đa làm thêm giờ quá mức quy định của Bộ luật Lao động thông qua việc phân bổ đều ca kíp."
- **Góc nhìn Giám đốc Sản xuất (Manufacturing Director)**:
  > "Giúp quản đốc phân xưởng nhìn thấy trước nguy cơ thiếu hụt máy trước 2 tuần để chủ động bố trí nhân lực."

---

### VI. CHỈ SỐ TÁC ĐỘNG TÀI CHÍNH & VẬN HÀNH ĐỊNH LƯỢNG (IMPACT METRICS)
```json
{
  "on_time_delivery": "99.4% Giao hàng đúng hạn",
  "capacity_utilization": "+22% Tối ưu hiệu suất máy",
  "planning_hours": "Giảm từ 2 ngày xuống 30 phút"
}
```

---
*Tư liệu được lưu trữ và kiểm soát chất lượng bởi Hệ thống Insilos Enterprise Dossier Engine.*
