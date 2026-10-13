# Standard Operating Procedure (SOP): Lead-to-Cash (AL2C) & Deal-Desk Governance
## Quy Trình Vận Hành Chuẩn Từ Tiếp Cận Cơ Hội Đến Thu Hồi Công Nợ & Quản Trị Hợp Đồng

> **SOP Code:** SOP-AL2C-001 • **Version:** 2.0 (Master Council Compliant)  
> **Applicable Regulations:** Nghị định 13/2023/NĐ-CP (PDPD) • Nghị định 70/2025/NĐ-CP (E-Invoice) • Luật Thuế GTGT 48/2024  
> **Key Models:** `crm.lead` • `sale.order` • `al2c.value.case` • `al2c.dispute` • `account.move`  

---

## 1. Sơ Đồ Quy Trình Tổng Thể 13 Giai Đoạn (13-Stage AL2C Architecture)

Quy trình Lead-to-Cash của công ty kết hợp phương pháp luận tiếp cận khách hàng **MCEM (Microsoft Customer Engagement Methodology)** ở pha Bán hàng và phương pháp luận **SAP Activate** ở pha Triển khai:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   GIAI ĐOẠN TIỀN DỰ ÁN & BÁN HÀNG (PRE-SALES & MCEM)                   │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────┬──────────────┤
│ 1. GEO &     │ 2. Thu Thập  │ 3. Đánh Giá  │ 4. Khảo Sát  │ 5. Lập Báo  │ 6. Phê Duyệt │
│    Thị Trường│    & Làm Giàu│    Cơ Hội    │    & Kiến Trúc│    Giá, SOW │    Hợp Đồng  │
│    (Inbound) │    Dữ Liệu   │ (BANT/MEDDIC)│    Giá Trị   │ & Deal Desk │    & Ký Số   │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴─────┬───────┴──────┬───────┘
       │              │              │              │             │              │
       ▼              ▼              ▼              ▼             ▼              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               GIAI ĐOẠN TRIỂN KHAI & THU HỒI DÒNG TIỀN (DELIVERY & CASH)               │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────┬──────────────┤
│ 7. Khởi Động │ 8. Thực Hiện │ 9. Nghiệm Thu│ 10. Xuất Hóa │ 11. Đôn Đốc │ 12. Tái Ký & │
│    & Cung Cấp│    & Ghi Nhận│    & Phê Duyệt│     Đơn Điện │     Công Nợ │     Gia Hạn  │
│    Tài Nguyên│    Thời Gian │    Từng Mốc  │     Tử NĐ 70 │  & Đối Soát │   Thuê Bao   │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────┴──────────────┘
```

---

## 2. Chi Tiết Các Giai Đoạn Vận Hành & Hàng Rào Kiểm Soát (Governance Gates)

### Giai đoạn 1 & 2: Tiếp Cận Khách Hàng & Làm Giàu Dữ Liệu (Capture & Enrich)
- **Kênh Tiếp Nhận:** Website công ty, cổng thông tin `/llms.txt` (Generative Engine Optimization), sự kiện ngành hoặc email gửi tới `info@inno.ai.vn`.
- **Hàng Rào Kiểm Soát Nghị Định 13/2023/NĐ-CP (PDPD Guard):**
  - Mọi biểu mẫu đăng ký trực tuyến phải có checkbox xác nhận đồng thuận xử lý dữ liệu cá nhân (`consent_pdpd = True`).
  - Hệ thống tự động ghi nhật ký (Audit Log) thời điểm, địa chỉ IP và nội dung đồng thuận.
  - Tự động tra cứu mã số thuế (MST) qua Cổng thông tin Tổng cục Thuế để làm giàu thông tin: Tên pháp nhân chuẩn, người đại diện pháp luật, địa chỉ trụ sở chính và tình trạng đóng/mở mã số thuế.

### Giai đoạn 3: Đánh Giá Chất Lượng Cơ Hội (Lead Qualification)
- Áp dụng thang điểm **MEDDIC / BANT**:
  - **Budget (Ngân sách):** Dự kiến $\ge 150,000,000$ VND cho dự án triển khai hoặc $\ge 15,000,000$ VND/tháng cho dịch vụ thuê bao SaaS.
  - **Authority (Thẩm quyền):** Người tiếp cận có quyền ra quyết định (C-Level, Giám đốc CNTT, Kế toán trưởng) hoặc có quyền giới thiệu trực tiếp.
  - **Need (Nhu cầu thực tế):** Hệ thống cũ quá tải, chuẩn bị thanh kiểm tra thuế, yêu cầu chứng nhận an toàn hóa chất/ESG, hoặc hiện đại hóa quản trị.
  - **Timeline (Kế hoạch):** Kế hoạch golive cụ thể trong vòng 3 đến 6 tháng tới.

### Giai đoạn 4: Khảo Sát Nghiệp Vụ & Hồ Sơ Giá Trị (Value Architecture)
- Thiết lập tài liệu **Value Case (`al2c.value.case`)**:
  - Ghi nhận hiện trạng thất thoát, thời gian đối soát thủ công và rủi ro tuân thủ của khách hàng.
  - Định lượng chỉ số ROI dự kiến (ví dụ: giảm 80% thời gian đóng sổ kế toán tháng, tiết kiệm 1,2 tỷ VND chi phí nhân sự đối soát).
  - Bản thảo Kiến trúc Giải pháp Tổng thể (Solution Blueprint) tích hợp giữa Insilos ERP, Vertical Resilience và Mojo AI.

---

## 3. Cổng Phê Duyệt Deal-Desk & Phân Quyền Nhiệm Vụ (Deal-Desk SoD Guardrails)

Tại **Giai đoạn 5 (Lập Báo Giá, SOW & Deal-Desk)**, hệ thống áp dụng cơ chế phân quyền kiểm soát tự động tại tầng ORM nhằm bảo vệ biên lợi nhuận của doanh nghiệp:

### 3.1. Bộ Ba Hàng Rào Kiểm Soát Bắt Buộc (The Triple Guardrails):
Hệ thống **TỰ ĐỘNG KHÓA (BLOCK)** hành động gửi báo giá (`action_quotation_send`) hoặc xác nhận đơn hàng (`action_confirm`) nếu phát hiện bất kỳ vi phạm nào sau đây:

1. **Hàng Rào Chiết Khấu (Discount Cap):**
   $$\text{Chiết Khấu Thực Tế} = 1 - \frac{\text{Tổng Tiền Dòng}}{\text{Giá Niêm Yết} \times \text{Số Lượng}} > 10\%$$
2. **Hàng Rào Quy Mô Hợp Đồng (TCV Threshold):**
   $$\text{Giá Trị Hợp Đồng Trước Thuế (Untaxed TCV)} > 500,000,000 \text{ VND}$$
3. **Hàng Rào Biên Lợi Nhuận Gộp Tối Thiểu (Gross Margin Floor):**
   $$\text{Biên Lợi Nhuận Gộp} = \frac{\text{Untaxed TCV} - \text{Chi Phí Nhân Lực & Hạ Tầng Dự Kiến}}{\text{Untaxed TCV}} < 35\%$$
4. **Hàng Rào Lịch Sử Công Nợ Khách Hàng:**
   Khách hàng hiện có bất kỳ hóa đơn nào quá hạn quá 30 ngày ($D+30$) chưa thanh toán.

### 3.2. Quy Trình Mở Khóa Phê Duyệt (Approval Workflow):
- Nhân viên kinh doanh thuộc nhóm `insilos_al2c.group_al2c_agent` **KHÔNG THỂ TỰ PHÊ DUYỆT**.
- Đơn hàng vi phạm sẽ chuyển sang trạng thái chờ duyệt `al2c_state = 'pending_approval'`.
- Chỉ người dùng thuộc nhóm **Giám Đốc Bán Hàng (`sales_team.group_sale_manager`)** hoặc **Ban Giám Đốc (Board of Directors)** mới có quyền tích chọn trường `al2c_approved = True` kèm theo lý do giải trình kinh doanh hợp lệ được ghi nhận vào Chatter.

---

## 4. Quản Trị Nghiệm Thu, Xuất Hóa Đơn & Đôn Đốc Công Nợ (Billing & Collections)

### 4.1. Quy Chuẩn Xuất Hóa Đơn Điện Tử Theo Nghị Định 70/2025/NĐ-CP:
- **Nguyên tắc cốt lõi:** Tuyệt đối không xuất hóa đơn khống hoặc xuất hóa đơn sai thời điểm. Hóa đơn điện tử chỉ được phát hành khi thỏa mãn một trong hai điều kiện:
  1. *Tiền tạm ứng dịch vụ (Advance Payment):* Xuất hóa đơn trong vòng 24 giờ kể từ thời điểm nhận được tiền vào tài khoản ngân hàng.
  2. *Nghiệm thu theo mốc (Milestone Acceptance):* Phải có **Biên bản nghiệm thu bàn giao có chữ ký số hai bên** được đính kèm vào hồ sơ `documents.document` liên kết với mốc dự án.
- **Tỷ Trọng Thanh Toán Mẫu Cho Dự Án Triển Khai (`ERP-STARTER` / `ERP-GROWTH`):**
  - Mốc 1 (Prepare - Tạm ứng khởi động): **15%** giá trị hợp đồng.
  - Mốc 2 (Explore - Ký duyệt thiết kế chi tiết SDD): **25%** giá trị hợp đồng.
  - Mốc 3 (Realize - Hoàn thành kiểm thử chấp nhận UAT): **35%** giá trị hợp đồng.
  - Mốc 4 (Deploy - Golive chính thức đưa vào sử dụng): **15%** giá trị hợp đồng.
  - Mốc 5 (Run - Hết thời gian bảo hành/Hypercare 30 ngày): **10%** giá trị hợp đồng.

### 4.2. Thang Đôn Đốc Công Nợ & Cơ Chế Đóng Băng Tranh Chấp (`al2c.dispute`):
Hệ thống tự động kích hoạt tiến trình đôn đốc thanh toán (Dunning Ladder):
- **Ngày $D-3$ (Trước hạn 3 ngày):** Email tự động gửi bảng kê hóa đơn và mã QR VietQR / Napas247 chuyển khoản chính xác nội dung.
- **Ngày $D+1$ (Quá hạn 1 ngày):** Thông báo nhắc nhở lịch sự qua Email và Zalo ZNS cho Kế toán thanh toán của khách hàng.
- **Ngày $D+7$ (Quá hạn 7 ngày):** Thông báo đôn đốc chính thức lần 1; hệ thống tự động giao nhiệm vụ nhắc nợ cho Quản lý khách hàng (Account Executive).
- **Ngày $D+15$ (Quá hạn 15 ngày):** Thư cảnh báo ngừng cung cấp dịch vụ kỹ thuật và hỗ trợ AMS nếu không hoàn tất thanh toán.
- **Ngày $D+30$ (Quá hạn 30 ngày):** Tự động chuyển tài khoản sang trạng thái đóng băng tín dụng, khóa quyền nâng cấp hoặc mở rộng user; chuyển hồ sơ sang bộ phận Pháp chế xử lý.

> **CƠ CHẾ ĐÓNG BĂNG KHIẾU NẠI (`AL2C-INV-103`):**  
> Khi khách hàng mở phiếu khiếu nại thương mại hoặc kỹ thuật (`al2c.dispute`), toàn bộ tiến trình đôn đốc nhắc nợ và tính lãi phạt chậm trả **TỰ ĐỘNG TẠM DỪNG (FREEZE)** cho đến khi Giám đốc Tài chính hoặc Trưởng Ban Dự án xác nhận giải quyết xong khiếu nại.
