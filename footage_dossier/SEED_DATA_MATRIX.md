# INSILOS ENTERPRISE DOSSIER — SEED DATA MATRIX & ARCHITECTURE SPECIFICATION
**Hệ Thống Dữ Liệu Nền Tảng Doanh Nghiệp (Enterprise Master & Transactional Data Matrix)**  
*Mã tài liệu: INS-EDM-2026-V1*  
*Cơ sở dữ liệu mục tiêu: `odoo20_dev` (PostgreSQL 16/18 - Port 5434) | Nền tảng: Insilos Platform (Odoo 20 LTS)*  
*Hội đồng thẩm định: Hội đồng Chuyên gia Cấp cao Insilos (Senior Expert Council)*

---

## 1. TỔNG QUAN KIẾN TRÚC DỮ LIỆU SEED DATA (EXECUTIVE SUMMARY)

Tài liệu này xác lập ma trận dữ liệu mẫu chuẩn mực (Zero-Placeholder Master & Transactional Data Matrix) phục vụ toàn diện cho 3 trụ cột chiến lược của Insilos Enterprise:
1. **B2B Marketing & Live Interactive Demos**: Cung cấp dữ liệu nghiệp vụ chân thực, sống động cho các thước phim trình diễn B-Roll điện ảnh chuẩn 1920x1080 60FPS.
2. **Đấu Thầu Doanh Nghiệp & Hồ Sơ Năng Lực (Enterprise Tender Dossier)**: Minh chứng năng lực xử lý quy mô lớn từ Lead-to-Order-to-Cash, giải quyết bài toán chuỗi cung ứng logistics cảng biển và gia công cơ khí nặng.
3. **Đào Tạo Vận Hành & Khảo Sát Hệ Thống (Operations Training & Deep-Link Verification)**: Khóa cứng các định danh bản ghi chuẩn (`record_id`), bảo đảm 100% các liên kết sâu (Deep-Links) trên giao diện Owl WebClient mở trực tiếp vào đúng biểu mẫu tác nghiệp mà không phát sinh bất kỳ cảnh báo thiếu bản ghi (Missing Record) hay lỗi 500 nào.

---

## 2. MA TRẬN 13 KỊCH BẢN NGHIỆP VỤ ĐẶC TẢ CHI TIẾT (13-USECASE MASTER MATRIX)

| STT | Mã Usecase | Phân Hệ (ERP Module) | Model Kỹ Thuật (ORM) | Target ID | Mã Chứng Từ / Biển Số | Tên Đối Tác Doanh Nghiệp | Mã Số Thuế (VAT ID) | Hạng Mục / Đặc Tả Kỹ Thuật | Giá Trị Tài Chính (VNĐ) | Tài Khoản Hạch Toán (TT 200 / TT 78) | Chuyên Gia Chủ Trì |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **01** | `VID-01` | CRM & SD Bán Hàng Dự Án | `sale.order` | **1** | `#VN-SO2026-001` | Tổng Công ty Tân Cảng Sài Gòn (Saigon Newport - SNP) | `0300481234` | 05 Xe kéo điện V-LIFT 2500E (48V-400Ah) + 02 Trạm sạc DC 180kW (Pilot Tranche thuộc Gói thầu 18.675 Tỷ VNĐ) | **2.295.000.000** | TK 131, TK 5112, TK 33311 | Sales Director of SAP |
| **02** | `VID-02` | MM Mua Hàng & Cung Ứng | `purchase.order` | **1** | `#VN-PO2026-001` | Công ty CP Tập đoàn Hòa Phát / Thép Hòa Phát Dung Quất | `0900234567` / `4300793188` | 20 Tấn Thép tấm cán nóng SS400 12mm (@19.5k/kg) + 600m Thép hộp mạ kẽm 100x100x4.0mm (@245k/cây) | **537.000.000** | TK 152, TK 1331, TK 331 | TCO Expert of IBM |
| **03** | `VID-03` | Kho Vận & Quét Barcode | `stock.picking` | **2** | `WH/IN/00002` | Công ty CP Dây cáp điện Việt Nam (CADIVI) | `0300381567` | 3.500m Cáp điện đồng mềm hạ thế CADIVI 3 pha 3x16+1x10mm² (Quét mã GS1-128 truy vết lô xuất xưởng) | **647.500.000** *(Giá trị quy đổi lô kho)* | TK 152, TK 151, TK 331 | Logistics Dept Head |
| **04** | `VID-04` | Sản Xuất & BOM Đa Tầng | `mrp.production` | **10** | `WH/MO/00010` | Công ty CP Cơ Khí Chế Tạo V-LIFT | `0317654321` | Lệnh sản xuất 04 Cụm Khung gầm Chassis hàn gia công V-LIFT Frame (`SF-CHASSIS-25E`), BOM cấp 2 | **300.000.000** *(Giá thành định mức)* | TK 621, TK 622, TK 627 -> TK 154 | Giám đốc Sản xuất |
| **05** | `VID-05` | Kế Hoạch Điều Độ MPS | `mrp.production` | **10** | `WH/MO/00010` | Công ty CP Cơ Khí Chế Tạo V-LIFT | `0317654321` | Điều độ tiến độ sản xuất trên biểu đồ Gantt, phân bổ phụ tải 6 phân xưởng máy, chặn quá tải | **300.000.000** | TK 154, TK 155 | Giám đốc Sản xuất |
| **06** | `VID-06` | MES Shop Floor Tablet | `mrp.production` | **10** | `WH/MO/00010` | Công ty CP Cơ Khí Chế Tạo V-LIFT | `0317654321` | Giám sát trạm máy Shop Floor: Cắt Fiber Laser 12kW, Hàn Robot Yaskawa; đo lường OEE thời gian thực đạt 92.5% | **Chi phí vận hành trạm máy** | TK 622, TK 627 | Giám đốc Sản xuất |
| **07** | `VID-07` | Đội Xe & Nhiên Liệu | `fleet.vehicle` | **6** | `51C-982.45` | Tổng Công ty Dầu Việt Nam - CTCP (PVOIL) | `0305891234` | Xe đầu kéo Hyundai Xcient GT 440PS (ODO 142.500km), định mức tiêu thụ dầu DO 0.05S 34.5L/100km | **1.850.000.000** *(Nguyên giá TSCĐ)* | TK 211, TK 214, TK 641 | Logistics Dept Head |
| **08** | `VID-08` | Tuân Thủ An Toàn Đăng Kiểm | `fleet.vehicle` | **8** | `51R-089.34` | Trung tâm Đăng kiểm 50-02S / VCCI | N/A | Sơ mi rơ moóc xương 3 trục 40ft CIMC Trailers, tự động khóa chốt điều vận khi chưa hoàn tất kiểm định | **420.000.000** *(Nguyên giá TSCĐ)* | TK 211, TK 214, TK 242 | VCCI Head Việt Nam |
| **09** | `VID-09` | Vận Tải Drayage Liên Cảng | `sale.order` | **2** | `#VN-SO2026-002` | Công ty CP Gemadept Logistics / CMIT | `0303126789` / `3500806490` | 50 Chuyến kéo container 40ft Cát Lái - VSIP Bình Dương + 03 Rơ-moóc 40ft; Cảnh báo phí lưu bãi DET/DEM | **1.452.500.000** | TK 131, TK 5113, TK 33311 | Logistics Dept Head |
| **10** | `VID-10` | Hóa Đơn Điện Tử Thông Tư 78 | `account.move` | **12** | `INV/2026/00001` | Tổng Công ty Tân Cảng Sài Gòn (Saigon Newport - SNP) | `0300481234` | Hóa đơn GTGT điện tử (Ký số Viettel S-Invoice, CQT cấp mã, Nghị định 123/2020/NĐ-CP) | **1.050.500.000** | TK 131 (Nợ) / TK 5112, TK 33311 (Có) | VCCI Head Việt Nam |
| **11** | `VID-11` | Hạch Toán Giá Thành TT 200 | `account.move` | **15** | `BILL/2026/09/0001` | Công ty CP Tập đoàn Hòa Phát | `0900234567` | Hóa đơn mua nguyên vật liệu thép tấm & thép hộp kết cấu, đối soát 3 chiều PO-GRN-Bill | **429.550.000** | TK 152, TK 1331 (Nợ) / TK 331 (Có) | VCCI Head Việt Nam |
| **12** | `VID-12` | Báo Cáo Tài Chính C-Level | `account.move` | **12** | `INV/2026/00001` | Ban Giám Đốc Insilos / Tân Cảng SNP | `0300481234` | Bảng cân đối kế toán Mẫu B01-DN, Báo cáo KQKD Mẫu B02-DN, phân tích EBITDA & Tỷ suất lãi gộp | **1.050.500.000** *(Doanh thu ghi nhận)* | B01-DN, B02-DN, TK 911 | TCO Expert of IBM |
| **13** | `HSE-01` | AI Vision PPE & Giám Sát CCTV | `fleet.vehicle.log.services` | **6** | `DK-5002S-12389` | Trạm Kiểm Soát Cổng HSE Gate #03 / Tân Cảng | N/A | Camera AI quét nhận diện BHLĐ (Mũ bảo hộ Helmet, Áo phản quang Vest), cảnh báo xâm nhập vùng nguy hiểm | **560.000** *(Phí kiểm định & bảo trì)* | TK 642, TK 331, TK 112 | Marketing Director of Google |

---

## 3. DANH MỤC ĐỐI TÁC DOANH NGHIỆP TRỌNG ĐIỂM (ENTERPRISE PARTNERS)

Hệ thống seed data đảm bảo tính hiện diện của 7 đối tác công nghiệp đầu ngành tại Việt Nam:

1. **Tổng Công Ty Tân Cảng Sài Gòn (Saigon Newport - SNP)**:
   - **ID Hệ thống**: `58` | **Mã Số Thuế**: `0300481234`
   - **Địa chỉ**: Cảng Cát Lái, Đường Nguyễn Thị Định, Phường Cát Lái, TP Thủ Đức, TP Hồ Chí Minh.
   - **Vai trò**: Khách hàng chiến lược (Customer Rank: 1). Khách hàng trúng thầu dự án hiện đại hóa xe kéo điện cảng xanh.

2. **Công ty CP Thép Hòa Phát Dung Quất / Tập đoàn Hòa Phát**:
   - **ID Hệ thống**: `60` (Chi nhánh Hưng Yên) & Bản ghi Dung Quất (`4300793188`)
   - **Địa chỉ**: Khu Kinh Tế Dung Quất, Xã Bình Đông, Huyện Bình Sơn, Tỉnh Quảng Ngãi.
   - **Vai trò**: Nhà cung cấp thép chiến lược (Supplier Rank: 1). Cung ứng thép tấm SS400 cán nóng và thép hộp kết cấu.

3. **Công ty CP Cơ Khí Chế Tạo V-LIFT**:
   - **Mã Số Thuế**: `0317654321`
   - **Địa chỉ**: Lô B2-3, Đường D1, KCN Hiệp Phước, Xã Hiệp Phước, Huyện Nhà Bè, TP Hồ Chí Minh.
   - **Vai trò**: Đối tác gia công chế tạo cơ khí chính xác, đơn vị tổng thầu lắp ráp dòng xe kéo điện V-LIFT 2500E.

4. **Tổng Công Ty Dầu Việt Nam - CTCP (PVOIL / Petrolimex)**:
   - **ID Hệ thống**: `132` | **Mã Số Thuế**: `0305891234`
   - **Địa chỉ**: Số 1-5 Lê Duẩn, Phường Bến Nghé, Quận 1, TP Hồ Chí Minh.
   - **Vai trò**: Nhà cung cấp nhiên liệu dầu Diesel 0.05S cho đội xe vận tải container liên cảng.

5. **Công ty TNHH Cảng Quốc Tế Cái Mép (CMIT)**:
   - **Mã Số Thuế**: `3500806490`
   - **Địa chỉ**: Khu phố Phước Lộc, Phường Phước Hòa, Thị xã Phú Mỹ, Tỉnh Bà Rịa - Vũng Tàu.
   - **Vai trò**: Cảng đích trung chuyển trong mạng lưới tuyến vận chuyển container drayage.

6. **Công ty CP Gemadept Logistics**:
   - **ID Hệ thống**: `59` | **Mã Số Thuế**: `0303126789`
   - **Địa chỉ**: Số 6 Lê Thánh Tôn, Phường Bến Nghé, Quận 1, TP Hồ Chí Minh.
   - **Vai trò**: Khách hàng dịch vụ logistics và điều phối xe drayage liên tỉnh.

7. **Công ty CP Dây cáp điện Việt Nam (CADIVI)**:
   - **ID Hệ thống**: `61` | **Mã Số Thuế**: `0300381567`
   - **Địa chỉ**: 70-72 Nam Kỳ Khởi Nghĩa, Phường Nguyễn Thái Bình, Quận 1, TP Hồ Chí Minh.
   - **Vai trò**: Nhà cung cấp cáp điện đồng mềm công nghiệp hạ thế và trung thế.

---

## 4. DANH MỤC VẬT TƯ & SẢN PHẨM CÔNG NGHIỆP (MATERIALS & PRODUCTS)

1. **Thép tấm cán nóng kết cấu SS400 (Dày 12mm)**:
   - Mã sản phẩm: `RM-STEEL-SS400-12` (Template ID: `147`, Product ID: `136`)
   - Đơn vị tính: kg | Đơn giá mua: 19.500 VNĐ/kg | Giá bán: 26.500 VNĐ/kg
   - Quản lý kho: Theo số Lô (By Lots) | Quy cách: Khổ 1.500 x 6.000 x 12mm.

2. **Thép hộp mạ kẽm nhúng nóng 100x100x4.0mm (Cây 6m)**:
   - Mã sản phẩm: `RM-STEEL-BOX100` (Template ID: `148`, Product ID: `137`)
   - Đơn vị tính: Cây | Đơn giá mua: 245.000 VNĐ/cây | Giá bán: 310.000 VNĐ/cây.

3. **Dây cáp điện đồng mềm CADIVI 3 pha 3x16+1x10mm²**:
   - Mã sản phẩm: `RM-CABLE-CADIVI` (Template ID: `150`, Product ID: `139`)
   - Đơn vị tính: Mét | Đơn giá mua: 142.000 VNĐ/m | Giá bán: 185.000 VNĐ/m.

4. **Cụm Khung gầm Chassis hàn gia công (V-LIFT Frame)**:
   - Mã sản phẩm: `SF-CHASSIS-25E` (Template ID: `162`, Product ID: `151`)
   - Bán thành phẩm cấp 1 | Đơn giá thành định mức: 55.000.000 VNĐ | Giá niêm yết: 75.000.000 VNĐ.

5. **Cụm Bơm & Van Thủy Lực Bosch Rexroth Công Nghiệp (250 bar)**:
   - Mã sản phẩm: `RM-HYD-REXROTH` / `SF-HYD-MAST45` (Template ID: `165`, Product ID: `154`)
   - Nhập khẩu chính hãng Rexroth A10VSO | Giá mua định mức: 42.000.000 VNĐ | Giá niêm yết: 58.000.000 VNĐ.

6. **Động cơ điện xoay chiều công nghiệp AC 45kW / 48V-10kW**:
   - Mã sản phẩm: `RM-MTR-AC45KW` / `SF-DRIVE-AC48V` (Template ID: `163`, Product ID: `152`)
   - Động cơ không chổi than IP67 chịu tải nặng cảng biển | Giá mua: 35.000.000 VNĐ | Giá niêm yết: 48.000.000 VNĐ / 88.000.000 VNĐ.

7. **Xe kéo điện chuyên dụng cảng biển V-LIFT 2500E**:
   - Mã sản phẩm: `EQ-VLIFT-2500E` (Template ID: `159`, Product ID: `148`)
   - Thành phẩm cơ điện tử | Giá vốn định mức: 265.000.000 VNĐ | Giá bán thương mại: 385.000.000 VNĐ
   - Quản lý xuất xưởng: Quản lý Số Seri duy nhất (Unique Serial Tracking).

8. **Trạm sạc nhanh công nghiệp Dual-Gun DC 180kW (V-CHARGE 180)**:
   - Mã sản phẩm: `EV-CHG-180KW` / `EV-CHG-60KW` (Template ID: `161`, Product ID: `150`)
   - Công suất: 180kW (90kW x 2 súng sạc CCS2) | Giá vốn: 120.000.000 VNĐ | Giá bán: 185.000.000 VNĐ.

---

## 5. ĐẶC TẢ ĐỊNH MỨC VẬT TƯ (BOM) & 6 PHÂN XƯỞNG (WORKCENTERS)

### 5.1 Cấu trúc BOM Đa Tầng (Multi-Level BOM)
- **BOM Cấp 0 (Thành phẩm Xe kéo V-LIFT 2500E)**: `BOM-VLIFT-2500E-V1` (ID: `10`)
  * `SF-CHASSIS-25E`: 01 Cụm khung gầm hàn gia công
  * `SF-DRIVE-AC48V`: 01 Cụm cầu truyền động & động cơ xoay chiều
  * `SF-BATTPACK-400AH`: 01 Cụm Pin Lithium LiFePO4 Smart BMS
  * `SF-HYD-MAST45` / `RM-HYD-REXROTH`: 01 Cụm bơm van thủy lực Rexroth
  * `RM-PCB-CONTROLLER`: 01 Bo mạch điều khiển vi xử lý Cortex-M4
  * `RM-CABLE-CADIVI`: 15 mét Dây cáp điện lực đồng mềm CADIVI
- **BOM Cấp 1 (Bán thành phẩm Khung gầm Chassis)**: `BOM-CHASSIS-25E-V1` (ID: `11`)
  * `RM-STEEL-SS400-12`: 450 kg Thép tấm cán nóng SS400 12mm
  * `RM-STEEL-BOX100`: 24 mét Thép hộp kẽm 100x100x4.0mm
  * `RM-PAINT-JOTUN-EP`: 18 kg Sơn sấy tĩnh điện công nghiệp Epoxy Jotun

### 5.2 6 Phân Xưởng Máy & Mục Tiêu Hiệu Suất Thiết Bị OEE
1. **`WC-CUT-01` (ID: 13)**: Phân xưởng Cắt Fiber Laser 12kW & Đột dập CNC (OEE Target: 88.0%)
2. **`WC-BEND-01` (ID: 14)**: Phân xưởng Chấn gấp định hình CNC Yawei 300T (OEE Target: 85.0%)
3. **`WC-WELD-01` (ID: 15)**: Phân xưởng Hàn Robot tự động Yaskawa Motoman (OEE Target: 92.0%)
4. **`WC-PAINT-01` (ID: 16)**: Dây chuyền Xử lý bề mặt & Sơn sấy tĩnh điện tự động (OEE Target: 90.0%)
5. **`WC-ASM-01` (ID: 17)**: Dây chuyền Lắp ráp hoàn thiện Cơ điện & Thủy lực (OEE Target: 85.0%)
6. **`WC-TEST-01` (ID: 18)**: Trạm Kiểm chuẩn Chất lượng PDI & Thử tải động (OEE Target: 95.0%)

---

## 6. GÓC NHÌN & TIÊU CHUẨN ĐÁNH GIÁ TỪ HỘI ĐỒNG CHUYÊN GIA

### 6.1 Sales Director of SAP (Lead-to-Order-to-Cash & Bidding)
- Thiết kế luồng bán hàng dự án có tính pháp lý cao: Đơn bán hàng `#VN-SO2026-001` được liên kết chặt chẽ với Hợp đồng nguyên tắc gói thầu `SNP-TRACTOR-2026/HĐNT` có tổng trị giá **18.675 Tỷ VNĐ** với Tân Cảng Sài Gòn.
- Đợt 1 nghiệm thu bàn giao 5 xe kéo V-LIFT 2500E và 2 trạm sạc DC 180kW với giá trị thanh toán đợt 1 là **2.295.000.000 VNĐ**.
- Kiểm soát biên lãi gộp (Gross Margin Lock): Doanh thu 2.295B VNĐ ứng với giá vốn 1.565B VNĐ đạt tỷ suất lợi nhuận gộp **31.8%**, bảo vệ ngưỡng an toàn tài chính trước khi C-Level phê duyệt.

### 6.2 Marketing Director of Google (Cinematic Recording Standards)
- Chuẩn ghi hình màn hình 1080p 60FPS: Tuyệt đối không xuất hiện thanh địa chỉ trình duyệt (Zero Browser Chrome: no URL bar, no tabs, no bookmarks).
- Visual Effects (VFX): Con trỏ ảo Neon Cyan (`#00f0ff`) kích thước 28px, hiệu ứng sóng xung Click Ripple 40px, quầng sáng Spotlight Halo làm nổi bật nút bấm quan trọng, camera zoom cận cảnh 120%-145% vào các chỉ số KPI then chốt.
- Tiêu chuẩn chống Lazy Code: Chỉ số mật độ thao tác $IDS \ge 2.2$ hành động/giây, không có khoảng đứng hình tĩnh vượt quá 2.5 giây.

### 6.3 TCO Expert of IBM (Total Cost of Ownership & ROI Reduction)
- Lợi ích chuyển đổi số: Thay thế 5 phần mềm rời rạc bằng nền tảng hợp nhất Insilos Platform tiết kiệm **₫2.029.050.000 / Năm** chi phí vận hành và bản quyền phần mềm phân mảnh.
- Chuyển dịch CapEx sang OpEx, thời gian hoàn vốn đầu tư (ROI Payback Period) đạt từ **6 đến 9 tháng**.
- Báo cáo phân tích tài chính C-Level trên Hóa đơn `INV/2026/00001` làm nổi bật chỉ số EBITDA cải thiện +14.2% so với chu kỳ kế toán trước.

### 6.4 Logistics Dept Head (Port Operations & Fleet Dispatch)
- Mô hình điều xe drayage liên cảng: Điều phối đầu kéo Hyundai Xcient `51C-982.45` và rơ-moóc `51R-089.34` chạy tuyến Cát Lái - VSIP Bình Dương và Cái Mép.
- Tự động đối soát định mức tiêu thụ nhiên liệu PVOIL 34.5L/100km, tự động phát cảnh báo phí phạt lưu bãi/lưu vỏ container DET/DEM trước 12 giờ.
- Truy vết mã vạch GS1 Barcode lô cáp điện CADIVI tại chứng từ `WH/IN/00002` đảm bảo kiểm kê kho chính xác 100%.

### 6.5 VCCI Head Việt Nam (Legal Compliance & Statutory Accounting)
- Hóa đơn điện tử Thông tư 78/2021/TT-BTC & Nghị định 123/2020/NĐ-CP: Chứng từ `INV/2026/00001` hiển thị trạng thái cấp mã cơ quan thuế hợp lệ, kết nối API Viettel S-Invoice / VNPT.
- Chế độ kế toán doanh nghiệp Thông tư 200/2014/TT-BTC: Hạch toán chuẩn xác dòng chi phí sản xuất:
  * Chi phí nguyên vật liệu trực tiếp (TK 621)
  * Chi phí nhân công trực tiếp (TK 622)
  * Chi phí sản xuất chung (TK 627)
  * Kết chuyển chi phí sản xuất kinh doanh dở dang (TK 154) -> Nhập kho Thành phẩm (TK 155) -> Giá vốn hàng bán (TK 632).
- Khóa chốt an toàn đăng kiểm phương tiện tại phiếu dịch vụ `DK-5002S-12389`, ngăn ngừa rủi ro bị đình chỉ lưu hành trên đường cao tốc.

### 6.6 Giám đốc Sản xuất (Precision Mechanical Manufacturing)
- Cấu trúc BOM hai cấp khép kín giữa Lệnh sản xuất `WH/MO/00010` (Khung gầm) và Thành phẩm xe kéo điện V-LIFT 2500E.
- Hệ thống điều độ sản xuất Master Production Schedule (MPS) trên Gantt chart cân bằng phụ tải giữa các trạm máy CNC và robot hàn, giảm thời gian chết (Downtime) 45%.
- Màn hình Shop Floor Tablet hiển thị giao diện tác nghiệp cảm ứng công nghiệp với chỉ số OEE thực tế đạt **92.5%** (Availability 94.2%, Performance 98.5%, Quality 99.7%).

---

## 7. BẢNG ĐỐI CHIẾU TÀI KHOẢN KẾ TOÁN VIỆT NAM (TT 200 / TT 78)

| Mã Tài Khoản | Tên Tài Khoản Theo Thông Tư 200/2014/TT-BTC | Nghiệp Vụ Phát Sinh Trong Seed Data | Chứng Từ Liên Quan |
|:---:|:---|:---|:---:|
| **TK 112** | Tiền gửi ngân hàng (VND / USD) | Nhận tạm ứng hợp đồng, thanh toán tiền nhiên liệu & phí dịch vụ | `INV/2026/00001`, `BILL/2026/09/0001` |
| **TK 131** | Phải thu của khách hàng | Ghi nhận công nợ bán hàng dự án cho Tân Cảng Sài Gòn, Gemadept | `sale.order` 1, `account.move` 12 |
| **TK 1331** | Thuế GTGT được khấu trừ của hàng hóa, dịch vụ | Khấu trừ thuế GTGT 8-10% đầu vào mua thép Hòa Phát, cáp CADIVI | `purchase.order` 1, `account.move` 15 |
| **TK 151** | Hàng mua đang đi đường | Ghi nhận hàng đang vận chuyển từ cảng Hải Phòng về cảng Cát Lái | `stock.picking` 2 |
| **TK 152** | Nguyên liệu, vật liệu | Thép tấm SS400, thép hộp, sơn epoxy, cáp CADIVI lưu kho | `stock.picking` 2, `mrp.production` 10 |
| **TK 154** | Chi phí sản xuất, kinh doanh dở dang | Tập hợp chi phí gia công chế tạo khung gầm xe kéo tại xưởng | `mrp.production` 10 (Work Order 40-43) |
| **TK 155** | Thành phẩm | Nhập kho hoàn thiện xe kéo điện V-LIFT 2500E & cụm khung gầm | Lệnh hoàn tất MO/00010 |
| **TK 211** | Tài sản cố định hữu hình | Đầu kéo Hyundai Xcient `51C-982.45`, Sơ mi rơ moóc `51R-089.34` | `fleet.vehicle` 6, `fleet.vehicle` 8 |
| **TK 214** | Hao mòn tài sản cố định | Trích khấu hao thiết bị cơ giới vận tải hàng tháng | Báo cáo tài chính B01-DN |
| **TK 331** | Phải trả cho người bán | Ghi nhận nghĩa vụ trả nợ Tập đoàn Hòa Phát, CADIVI, PVOIL | `purchase.order` 1, `account.move` 15 |
| **TK 33311** | Thuế GTGT đầu ra phải nộp | Thuế GTGT phát hành trên Hóa đơn điện tử Viettel S-Invoice | `account.move` 12 (`INV/2026/00001`) |
| **TK 5112** | Doanh thu bán các thành phẩm | Doanh thu cung cấp lô xe kéo điện V-LIFT 2500E cho Tân Cảng | `sale.order` 1, `account.move` 12 |
| **TK 5113** | Doanh thu cung cấp dịch vụ | Doanh thu vận tải container drayage cho Gemadept Logistics | `sale.order` 2 |
| **TK 621** | Chi phí nguyên liệu, vật liệu trực tiếp | Xuất thép tấm SS400 và thép hộp vào lệnh cắt laser và chấn gấp | `mrp.production` 10 |
| **TK 622** | Chi phí nhân công trực tiếp | Tiền lương kỹ sư vận hành máy CNC, thợ hàn và kỹ thuật viên PDI | `mrp.production` 10 |
| **TK 627** | Chi phí sản xuất chung | Khấu hao máy cắt laser, điện năng tiêu thụ, bảo dưỡng định kỳ | `mrp.production` 10 |
| **TK 632** | Giá vốn hàng bán | Giá vốn xuất xưởng lô xe kéo điện bàn giao cho khách hàng | `account.move` 12 |
| **TK 641** | Chi phí bán hàng | Chi phí vận chuyển drayage bàn giao thiết bị tận bãi Tân Cảng | `sale.order` 1 |
| **TK 642** | Chi phí quản lý doanh nghiệp | Chi phí phần mềm quản trị ERP, kiểm định an toàn kỹ thuật | `fleet.vehicle.log.services` 6 |
| **TK 911** | Xác định kết quả kinh doanh | Tập hợp doanh thu, giá vốn, chi phí để lập Báo cáo KQKD B02-DN | `account.move` 12 (Báo cáo P&L) |

---

## 8. HƯỚNG DẪN KIỂM ĐỊNH & XÁC THỰC ĐỘC LẬP (VERIFICATION METHOD)

Để thẩm định độc lập tính chính xác và toàn vẹn của bộ dữ liệu seed data:
1. **Kiểm tra công cụ Seeding & Audit**:
   ```bash
   .venv/bin/python tools/seed_insilos_enterprise_dossier.py
   ```
   *Yêu cầu kết quả*: Mã thoát 0 (`exit code 0`), bảng tổng kết hiển thị `SEED DATA AUDIT SUMMARY: 13/13 PASS`, tệp `footage_dossier/seed_data_audit.json` được cập nhật với trạng thái hợp lệ.

2. **Kiểm tra liên kết sâu trực tiếp trên giao diện Owl WebClient**:
   ```bash
   .venv/bin/python tools/test_live_database_deeplinks.py
   ```
   *Yêu cầu kết quả*: 17/17 kịch bản deep-links mở thành công, mã thoát 0, không có cảnh báo thiếu bản ghi (Missing Record) hay lỗi 500 phát sinh.
