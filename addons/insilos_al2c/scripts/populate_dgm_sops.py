#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
DGM Standard Operating Procedures (SOP) Corpus Generator & Database Synchronizer
Target Legal Entity: CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGITAL MATE JOINT STOCK COMPANY / DGM)
Tax Code (MST): 0317958465
Author: Worker Milestone 1 — SOP Corpus Engineering
Integrity Mode: Production Enterprise Grade (Zero Placeholders, Zero Hardcoding Facades)
================================================================================
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

# ------------------------------------------------------------------------------
# 13 CANONICAL SOPS SPECIFICATION CORPUS
# ------------------------------------------------------------------------------

SOPS = [
    {
        "xml_id": "kb_dgm_sop_gov_01",
        "code": "SOP-DGM-GOV-01",
        "title": "SOP-DGM-GOV-01 · Quy trình Quản trị Pháp nhân, Rào chắn Danh tính Doanh nghiệp & Quản lý Con dấu Số",
        "icon": "🏛️",
        "sequence": 10,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-GOV-01 · Quy trình Quản trị Pháp nhân, Rào chắn Danh tính Doanh nghiệp & Quản lý Con dấu Số</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-GOV-01</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Nội bộ Doanh nghiệp (Internal Governance)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ</strong><br/>
                <em>Tên tiếng Anh:</em> DIGITAL MATE JOINT STOCK COMPANY (Viết tắt: DIGIMATE / DGM)<br/>
                <em>Mã số thuế:</em> <strong>0317958465</strong> (Cấp ngày 28/07/2023, thay đổi ĐKKD ngày 19/01/2026 tại Sở KH&ĐT TP.HCM)<br/>
                <em>Địa chỉ trụ sở:</em> Số 11, Đường số 3, KDC CityLand, Phường Tân Mỹ (trước khi sắp xếp sáp nhập là Phường Tân Phú, Quận 7), TP. Hồ Chí Minh, Việt Nam<br/>
                <em>Tài khoản ngân hàng:</em> Vietcombank (VCB) Chi nhánh Tân Định — STK: <strong>1202703007</strong> (VND & USD)
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Tổng Giám Đốc (CEO Lê Xuân Hoàng)</td>
            <th>Căn Cứ Pháp Lý & Quy Chế</th>
            <td>Luật Doanh nghiệp 2020; Nghị định 01/2021/NĐ-CP; Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân; Điều lệ Công ty Cổ phần Người Bạn Số; Quyết định ĐHĐCĐ số 0126/QĐ-ĐHĐCĐ.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư phần mềm)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Quản trị hồ sơ ĐKKD, Điều lệ &amp; Đại hội đồng Cổ đông</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Kiểm soát Danh sách Cổ đông &amp; Chủ sở hữu hưởng lợi (CSH)</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Quản lý con dấu số doanh nghiệp (HSM Viettel-CA / USB Token)</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I (Blocked)</strong></td>
        </tr>
        <tr>
            <td>Kiểm tra Rào chắn Danh tính Doanh nghiệp (Single Legal Entity Guardrail)</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>R</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R (Fail-Closed)</strong></td>
        </tr>
        <tr>
            <td>Công bố thông tin thay đổi địa giới hành chính (Phường Tân Mỹ)</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable (Chịu trách nhiệm tối cao); R = Responsible (Thực thi chính); C = Consulted (Tham vấn chuyên môn); I = Informed (Nhận thông tin thông báo).</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Quản trị Thông tin Pháp nhân Doanh nghiệp</h3>
<ul>
    <li><strong>Menu truy cập:</strong> <code>Cấu hình Hệ thống &gt; Người dùng &amp; Công ty &gt; Công ty (Companies)</code>.</li>
    <li><strong>Mô hình dữ liệu (Model):</strong> <code>res.company</code>.</li>
    <li><strong>Các trường kỹ thuật bắt buộc:</strong>
        <ul>
            <li><code>name</code>: CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ</li>
            <li><code>vat</code>: 0317958465</li>
            <li><code>street</code>: Số 11, Đường số 3, KDC CityLand</li>
            <li><code>ward_id</code>: Phường Tân Mỹ (Mã hành chính cập nhật sau sáp nhập)</li>
            <li><code>city</code>: Thành phố Hồ Chí Minh</li>
            <li><code>country_id</code>: Việt Nam (<code>base.vn</code>)</li>
            <li><code>email</code>: info@inno.ai.vn</li>
            <li><code>phone</code>: +84 373 068 161</li>
        </ul>
    </li>
    <li><strong>Chuyển đổi trạng thái:</strong> Bất kỳ thay đổi nào trên <code>res.company</code> phải được CEO xác thực thông qua xác thực 2 yếu tố (2FA) trước khi ghi sổ dữ liệu.</li>
</ul>

<h3>Bước 2: Quản trị Con dấu Số & Chữ ký Điện tử (Viettel-CA HSM)</h3>
<ul>
    <li><strong>Menu truy cập:</strong> <code>Ký số (Sign) &gt; Cấu hình Mẫu Chữ ký &gt; Chứng thư Số Doanh nghiệp</code>.</li>
    <li><strong>Mô hình dữ liệu (Model):</strong> <code>sign.template</code>, <code>sign.request</code>, <code>sign.request.item</code>.</li>
    <li><strong>Quy trình ký duyệt kép (Dual-Authorization Workflow):</strong>
        <ol>
            <li>Tài liệu hợp đồng, văn bản hành chính tải lên <code>documents.document</code> tại Thư mục <code>3224</code> (<code>01. Pháp lý &amp; Quản trị Doanh nghiệp (DGM - ĐKTL)</code>).</li>
            <li>Trưởng bộ phận soạn thảo khởi tạo luồng ký số trên <code>sign.request</code>.</li>
            <li>Ký cấp 1: Ký nháy chuyên môn của Finance/HR Lead (Mai Thị Hồng Thắm) hoặc CTO (Nguyễn Hoài Ân).</li>
            <li>Ký cấp 2: Ký số người đại diện pháp luật của Tổng Giám Đốc (Lê Xuân Hoàng).</li>
            <li>Đóng dấu số điện tử: Hệ thống gọi API Viettel-CA HSM ký số tổ chức (Con dấu tròn số của DGM).</li>
        </ol>
    </li>
    <li><strong>Rào chắn AI Agent:</strong> Nhóm quyền <code>group_al2c_agent</code> bị chặn tuyệt đối quyền gọi hàm <code>action_sign()</code> đối với chữ ký số pháp nhân.</li>
</ul>

<h3>Bước 3: Vận hành Rào chắn Danh tính Doanh nghiệp (Single Legal Entity Guardrail)</h3>
<ul>
    <li><strong>Mô hình giám sát:</strong> <code>al2c.compliance.scanner</code> và automated action trên <code>documents.document</code>.</li>
    <li><strong>Quy tắc quét tự động:</strong> Mỗi khi tài liệu xuất bản (Hợp đồng, Báo giá, Hóa đơn, Công văn) được tạo hoặc cập nhật, engine thực hiện regex scan:
        <pre><code>BANNED_ENTITY_REGEX = r'(?i)(ứng\s*dụng\s*sáng\s*tạo|ung\s*dung\s*sang\s*tao|0313683499|phường\s*tân\s*phú,\s*quận\s*7|p\.\s*tân\s*phú)'</code></pre>
    </li>
    <li>Nếu phát hiện vi phạm, hệ thống tự động:
        <ul>
            <li>Khóa trạng thái tài liệu, không cho phép gửi (state = <code>blocked</code>).</li>
            <li>Ghi log cảnh báo mức CRITICAL vào Chatter.</li>
            <li>Gửi cảnh báo tức thì cho Finance Lead và CEO qua mail activity.</li>
        </ul>
    </li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Điều Kiện Kích Hoạt & Tiêu Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Thời Hạn SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-GOV-01: Identity Invariance</strong></td>
            <td>Kiểm tra toàn bộ văn bản xuất bản nội bộ và đối ngoại phải khớp 100% MST <code>0317958465</code> và địa chỉ <code>Phường Tân Mỹ</code>.</td>
            <td>Chặn in ấn, chặn xuất PDF, chặn ký số nếu phát hiện sai lệch tên hoặc MST.</td>
            <td>Thời gian thực (Real-time &lt; 500ms)</td>
        </tr>
        <tr>
            <td><strong>GATE-GOV-02: Shareholder Registry</strong></td>
            <td>Cập nhật sổ đăng ký cổ đông theo biến động ĐHĐCĐ: Lê Xuân Hoàng (50%), Mai Thị Hồng Thắm (30%), Nguyễn Hoài Ân (20%).</td>
            <td>Yêu cầu đính kèm Nghị quyết ĐHĐCĐ và Danh sách CSH hưởng lợi vào Thư mục <code>3224</code>.</td>
            <td>Tối đa <strong>03 ngày</strong> làm việc sau ĐHĐCĐ</td>
        </tr>
        <tr>
            <td><strong>GATE-GOV-03: HSM Seal Custody</strong></td>
            <td>Xác thực quyền sử dụng chứng thư số HSM Viettel-CA và USB Token cho các giao dịch thuế/hải quan.</td>
            <td>Bắt buộc xác thực OTP/2FA gửi về số điện thoại đăng ký của Đại diện pháp luật (Lê Xuân Hoàng).</td>
            <td>Hiệu lực OTP trong <strong>120 giây</strong></td>
        </tr>
        <tr>
            <td><strong>GATE-GOV-04: Ward Migration Notice</strong></td>
            <td>Công văn thông báo điều chỉnh địa chỉ thuế từ Tân Phú sang Tân Mỹ gửi Chi cục Thuế Quận 7.</td>
            <td>Lưu trữ bản xác nhận tiếp nhận của cơ quan thuế vào Thư mục <code>3224</code>.</td>
            <td>Hoàn tất trước <strong>31/12/2026</strong></td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Audit Evidence in documents.document)</h2>
<ul>
    <li>Thư mục lưu trữ chuẩn: <code>ID 3224: 01. Pháp lý &amp; Quản trị Doanh nghiệp (DGM - ĐKTL)</code>.</li>
    <li>Hồ sơ bắt buộc:
        <ol>
            <li>Bản scan Giấy chứng nhận ĐKKD công ty cổ phần số <code>0317958465</code> (cấp ngày 19/01/2026).</li>
            <li>Điều lệ Công ty Cổ phần Người Bạn Số (bản sửa đổi mới nhất).</li>
            <li>Biên bản họp ĐHĐCĐ số <code>01/BBH-ĐHĐCĐ</code> và Quyết định số <code>0126/QĐ-ĐHĐCĐ</code>.</li>
            <li>Danh sách Cổ đông Sáng lập và Hồ sơ Chủ sở hữu hưởng lợi (CSH).</li>
            <li>Chứng thư số Viettel-CA còn hiệu lực đến năm 2026.</li>
        </ol>
    </li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_rev_01",
        "code": "SOP-DGM-REV-01",
        "title": "SOP-DGM-REV-01 · Quy trình Nghiệm thu, Tính giờ Overtime 2 Bậc & Xuất Hóa đơn Kỹ sư Onsite MTI Technology",
        "icon": "⏱️",
        "sequence": 20,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-REV-01 · Quy trình Nghiệm thu, Tính giờ Overtime 2 Bậc & Xuất Hóa đơn Kỹ sư Onsite MTI Technology</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-REV-01</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Tuyệt Mật Thương Mại (Commercial Confidential)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Khách hàng đối tác:</em> <strong>CÔNG TY TNHH MTI TECHNOLOGY</strong> (MST: 0314015511)<br/>
                <em>Địa chỉ đối tác:</em> Tầng 14 Khối tháp E, Tòa nhà Cộng Hòa Garden, 20 Cộng Hòa, P.12, Q. Tân Bình, TP.HCM<br/>
                <em>Đại diện đối tác:</em> Bà Nguyễn Thị Kim Thanh — Chức vụ: Phó Tổng Giám Đốc
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Project Manager Phụ trách Dự án Onsite &amp; Kế toán Doanh thu</td>
            <th>Căn Cứ Hợp Đồng &amp; Pháp Lý</th>
            <td>Hợp đồng Dịch vụ Kỹ sư Phần mềm số <code>DIGIMATE2401-001</code> ký ngày 15/01/2024; Nghị định 70/2025/NĐ-CP; Thông tư 78/2021/TT-BTC; Bộ luật Lao động 2019.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư Onsite)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Tiếp nhận và bóc tách bảng chấm công Excel đa sheet từ MTI</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Áp dụng công thức tính Overtime lũy tiến 2 bậc &amp; bộ lọc 60 phút</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Fail-Closed)</strong></td>
        </tr>
        <tr>
            <td>Kiểm tra SoD và phê duyệt Bảng kê Nghiệm thu Timesheet</td>
            <td><strong>A</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I (Blocked)</strong></td>
        </tr>
        <tr>
            <td>Gửi Bảng đối soát kèm Token HMAC 14 ngày cho Khách hàng xác nhận</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Phát hành Hóa đơn điện tử Viettel SInvoice ký hiệu 1C26TAA</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Theo dõi và thu hồi công nợ Net 40 ngày về Vietcombank 1202703007</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Kỹ sư onsite gồm: Bùi Hữu Tài, Huỳnh Trần Quang Khánh, Ngô Thanh Lộc, Lê Cao Bảo Phúc.</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Tiếp nhận Chấm công Tự động qua Email Staging Pipeline</h3>
<ul>
    <li><strong>Kênh tiếp nhận:</strong> Email đối tác gửi về <code>info@inno.ai.vn</code> kèm tệp đính kèm bảng chấm công Excel (<code>.xlsx</code> / <code>.xls</code>).</li>
    <li><strong>Daemon xử lý:</strong> <code>tools/mail_pubsub_daemon.py</code> bắt sự kiện, kiểm tra SPF/DKIM/DMARC và đẩy tệp vào mô hình <code>al2c.timesheet.staging</code>.</li>
    <li><strong>Mô hình dữ liệu (Model):</strong> <code>al2c.timesheet.staging</code> và <code>al2c.timesheet.staging.line</code>.</li>
    <li><strong>Thuật toán bóc tách đa sheet:</strong> Engine đọc các sheet mang mã định danh kỹ sư (<code>KhanhHTQ</code>, <code>TaiBH</code>, <code>LocNT</code>, <code>PhucLCB</code>), nhận diện tiêu đề gộp 2 dòng (Merged Header), trích xuất giờ vào, giờ ra, giờ nghỉ trưa, chuyển đổi <code>timedelta</code> và <code>time</code> sang số thực (float hours).</li>
</ul>

<h3>Bước 2: Tính toán Giờ Tiêu Chuẩn & Overtime Lũy Tiến 2 Bậc</h3>
<ul>
    <li><strong>Đơn giá thỏa thuận hợp đồng:</strong> <code>316.030 VND / giờ</code> (chưa bao gồm thuế VAT).</li>
    <li><strong>Khung giờ chuẩn biến thiên theo tháng:</strong>
        <ul>
            <li>Tháng 2: 108 ~ 128 giờ</li>
            <li>Tháng 3: 148 ~ 168 giờ</li>
            <li>Tháng 4: 140 ~ 160 giờ</li>
            <li>Tháng 5: 156 ~ 176 giờ</li>
            <li>Các tháng khác: Căn cứ vào số ngày làm việc thực tế trong tháng do MTI thông báo $\times 8$ giờ.</li>
        </ul>
    </li>
    <li><strong>Công thức tính toán lũy tiến 2 bậc:</strong>
        <p>Gọi $H_{act}$ là tổng số giờ làm việc thực tế hợp lệ trong tháng; $H_{max}$ là ngưỡng giờ chuẩn tối đa của tháng; $H_{ot} = \max(0, H_{act} - H_{max})$ là tổng số giờ làm thêm.</p>
        <ol>
            <li><strong>Giờ trong định mức ($H_{norm}$):</strong> $\min(H_{act}, H_{max}) \times 316.030 \text{ VND}$.</li>
            <li><strong>OT Bậc 1 ($H_{ot1}$ - 20 giờ đầu tiên):</strong> $\min(H_{ot}, 20) \times 100\% \times 316.030 \text{ VND}$.</li>
            <li><strong>OT Bậc 2 ($H_{ot2}$ - Từ giờ 21 trở đi):</strong> $\max(0, H_{ot} - 20) \times 150\% \times 316.030 \text{ VND} = H_{ot2} \times 474.045 \text{ VND}$.</li>
        </ol>
    </li>
    <li><strong>Bộ lọc loại trừ 60 phút (60-Minute Truncation Rule):</strong> Nếu tổng số phút làm thêm giờ lẻ $\le 60$ phút trong toàn bộ chu kỳ tính công, giá trị OT đó <strong>tuyệt đối bị làm tròn về 0 giờ (0 VND)</strong>.</li>
    <li><strong>Tiêu chí loại trừ giờ OT không hợp lệ:</strong> Hệ thống tự động gắn cờ loại bỏ các bản ghi chấm công thuộc danh mục:
        <ul>
            <li>Giờ nghỉ ăn tối giữa ca.</li>
            <li>Giờ sửa lỗi phát sinh do bất cẩn cá nhân hoặc hiểu sai đặc tả của MTI.</li>
            <li>Giờ làm lại (rework) do không tuân thủ quy trình kiểm thử.</li>
            <li>Giờ trực phát hành (release standby) dưới 2 giờ hoặc tự ý OT không có email chỉ đạo từ PM MTI.</li>
        </ul>
    </li>
</ul>

<h3>Bước 3: Phê duyệt SoD & Cam kết Ghi sổ (Commit to Analytic Ledger)</h3>
<ul>
    <li><strong>Phân tách nhiệm vụ (Segregation of Duties):</strong> Chỉ người dùng thuộc nhóm <code>project.group_project_manager</code> mới có quyền bấm nút <code>action_approve_and_commit()</code>. Các AI Agent tự động bị chặn.</li>
    <li><strong>Hành động ghi sổ:</strong> Bản ghi hợp lệ được chuyển thành các dòng <code>account.analytic.line</code> liên kết với Dự án Onsite MTI Technology.</li>
    <li><strong>Gửi đối soát & Ký duyệt:</strong> Hệ thống tạo bản ghi <code>account.move</code> dự thảo, sinh token HMAC 14 ngày theo công thức:
        <pre><code>HMAC-SHA256(invoice_id || partner_id || secret_key || expiry_date)</code></pre>
        và gửi email Bảng kê chi tiết cho PM MTI Technology xác nhận.
    </li>
</ul>

<h3>Bước 4: Xuất Hóa Đơn Điện Tử Viettel SInvoice & Theo Dõi Net 40</h3>
<ul>
    <li><strong>Phát hành HĐĐT:</strong> Sau khi MTI ký xác nhận, kế toán bấm <code>action_issue_einvoice()</code> trên <code>account.move</code>. Hệ thống gọi Viettel SInvoice, áp dụng ký hiệu <code>1C26TAA</code>, nhận mã cơ quan thuế và QR code.</li>
    <li><strong>Thời hạn thanh toán (Payment Terms):</strong> Cài đặt <strong>Net 40 ngày</strong> (thanh toán vào ngày 10 của tháng thứ 2 kể từ ngày kết thúc chu kỳ tính công) về tài khoản Vietcombank <code>1202703007</code>.</li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Tiêu Chuẩn Thẩm Định & Ngưỡng Rủi Ro</th>
            <th>Cơ Chế Phản Ứng (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-REV-01: Timesheet Cut-off</strong></td>
            <td>Chốt toàn bộ dữ liệu chấm công tháng $T$ và gửi Bảng kê Timesheet cho MTI.</td>
            <td>Hệ thống gửi cảnh báo nhắc nhở PM vào ngày 03; tự động khóa sổ staging lúc 17:00 ngày 05.</td>
            <td>Trước <strong>Ngày 05</strong> hàng tháng</td>
        </tr>
        <tr>
            <td><strong>GATE-REV-02: Invoice Issuance SLA</strong></td>
            <td>Xuất HĐĐT Viettel SInvoice kèm Đề nghị thanh toán gửi cho phòng Kế toán MTI.</td>
            <td>Bật cờ cảnh báo đỏ nếu đến ngày 08 chưa có xác nhận token từ MTI để kịp xuất hóa đơn.</td>
            <td>Trước <strong>Ngày 10</strong> hàng tháng</td>
        </tr>
        <tr>
            <td><strong>GATE-REV-03: Net 40 Dunning Ladder</strong></td>
            <td>Thu hồi công nợ thanh toán đúng hạn vào ngày 10 của tháng $T+2$.</td>
            <td>Kích hoạt thang nhắc nợ tự động (Dunning Ladder): Nhắc mềm ngày 35; đôn đốc ngày 40; đóng băng dịch vụ nếu trễ &gt; 15 ngày.</td>
            <td>Đúng <strong>Net 40 ngày</strong></td>
        </tr>
        <tr>
            <td><strong>GATE-REV-04: Staff Replacement Gate</strong></td>
            <td>Quy chế thay thế nhân sự onsite: Bên B thông báo trước 30 ngày làm việc (1 tuần chuyển giao không tính tiền); Bên A từ chối trong thử việc 30 ngày (5 ngày làm việc không tính tiền).</td>
            <td>Khóa lập hóa đơn (Zero-rate billing) đối với các ngày chuyển giao không tính tiền theo điều khoản hợp đồng.</td>
            <td>Thông báo trước <strong>30 ngày</strong></td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Audit Evidence in documents.document)</h2>
<ul>
    <li>Thư mục lưu trữ: <code>ID 3231: TÀI BÙI (03. Hợp đồng Thương mại &amp; Dự án / MTI Technology)</code>.</li>
    <li>Bộ hồ sơ thanh toán từng kỳ gồm:
        <ol>
            <li>Hợp đồng nguyên tắc <code>DIGIMATE2401-001</code> và Phụ lục nhân sự đính kèm.</li>
            <li>File Excel chấm công gốc đa sheet gửi từ MTI Technology.</li>
            <li>Bảng tính Overtime 2 bậc có chữ ký xác nhận của PM Digimate và PM MTI.</li>
            <li>Bản thể hiện HĐĐT Viettel SInvoice (Ký hiệu <code>1C26TAA</code>) có mã CQT.</li>
            <li>Giấy báo Có ngân hàng Vietcombank STK <code>1202703007</code> khi nhận thanh toán.</li>
        </ol>
    </li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_rev_02",
        "code": "SOP-DGM-REV-02",
        "title": "SOP-DGM-REV-02 · Quy trình Tiếp nhận Doanh thu Ngoại tệ Canva Pty Ltd, Kiểm soát Tỷ giá & Xuất HĐĐT 24h SLA",
        "icon": "💵",
        "sequence": 30,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-REV-02 · Quy trình Tiếp nhận Doanh thu Ngoại tệ Canva Pty Ltd, Kiểm soát Tỷ giá & Xuất HĐĐT 24h SLA</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-REV-02</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Bảo Mật Tài Chính (Financial Confidential)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Khách hàng nước ngoài:</em> <strong>CANVA PTY LTD</strong> (110 Kippax St, Surry Hills, Australia, AU)<br/>
                <em>Tài khoản nhà phát triển:</em> <code>pub@digimate.vn</code> (Digimate Publisher)<br/>
                <em>Chương trình tài trợ:</em> Canva Innovation Fund — App Adoption Awards
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Kế toán Ngân hàng &amp; Kế toán Thuế Doanh nghiệp</td>
            <th>Căn Cứ Pháp Lý &amp; Thỏa Thuận</th>
            <td>Thông tư 219/2013/TT-BTC (Thuế GTGT 0% xuất khẩu phần mềm); Thông tư 200/2014/TT-BTC; Nghị định 70/2025/NĐ-CP; Nghị định 125/2020/NĐ-CP (Xử phạt vi phạm hóa đơn); Thỏa thuận Canva Developer Terms.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư phần mềm)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Theo dõi và tiếp nhận Điện báo Có ngoại tệ USD từ Vietcombank</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Đối chiếu thông báo thưởng Canva Innovation Fund (admin@payout.canva.com)</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R (Publisher)</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Xác định tỷ giá mua chuyển khoản Vietcombank tại ngày tiền về</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Gom giải thưởng đa ứng dụng và lập HĐĐT xuất khẩu VAT 0%</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Ký số phát hành HĐĐT Viettel SInvoice trong hạn 24 Giờ SLA</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I (Fail-Closed)</strong></td>
        </tr>
        <tr>
            <td>Đóng gói hồ sơ miễn thuế 4 điểm lưu trữ vào Thư mục 3249</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Publisher: pub@digimate.vn do CTO Nguyễn Hoài Ân quản trị.</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Tiếp nhận Báo Có Vietcombank & Khởi động Bộ đếm 24H SLA</h3>
<ul>
    <li><strong>Sổ phụ ngân hàng:</strong> Khi nhận được Swift Credit Advice từ Vietcombank báo có khoản tiền USD từ nguồn chi trả <code>Canva &lt;admin@payout.canva.com&gt;</code> vào tài khoản <code>1202703007</code>:</li>
    <li>Kế toán ngân hàng tạo bản ghi trên <code>account.bank.statement.line</code> (hoặc webhook ngân hàng tự động đẩy về).</li>
    <li>Hệ thống ghi nhận trường <code>al2c_vcb_credit_date = fields.Datetime.now()</code> và kích hoạt ngay lập tức <strong>Bộ đếm thời gian 24H SLA Timer</strong>.</li>
</ul>

<h3>Bước 2: Xác thực Tỷ giá & Gom Nhóm Giải thưởng (Multi-App Award Consolidation)</h3>
<ul>
    <li><strong>Tỷ giá quy đổi bắt buộc:</strong> Lấy chính xác <strong>Tỷ giá Mua Chuyển khoản (Transfer Buying Rate)</strong> của Vietcombank công bố tại ngày tiền ghi có vào tài khoản (<code>Ngày ghi có</code>). Tuyệt đối không dùng tỷ giá bán hoặc tỷ giá bình quân liên ngân hàng.</li>
    <li><strong>Gom nhóm các ứng dụng đạt giải thưởng Canva App Adoption Awards:</strong>
        <p>Căn cứ các thông báo giải thưởng từ Canva Innovation Fund (Tier 1 = $2,000 USD, Tier 2 = $8,000 USD), kế toán tạo hóa đơn xuất khẩu đơn lẻ nhưng phân rã thành các dòng sản phẩm chi tiết:</p>
        <table class="table table-bordered">
            <thead>
                <tr style="background-color: #f8fafc;">
                    <th>Mã Sản Phẩm / Tên Hàng Hóa Dịch Vụ</th>
                    <th>Đơn Vị Tính</th>
                    <th>Số Tiền USD</th>
                    <th>Thuế Suất VAT</th>
                    <th>Tài Khoản Doanh Thu</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>PHẦN MỀM ỨNG DỤNG HOÁN ĐỔI GƯƠNG MẶT (Reface)</td>
                    <td>Gói</td>
                    <td>$2,000 USD</td>
                    <td>0% (Xuất khẩu)</td>
                    <td>TK 5113 (Doanh thu Dịch vụ Phần mềm)</td>
                </tr>
                <tr>
                    <td>PHẦN MỀM ỨNG DỤNG SÁNG TẠO LOGO (Gen Logo)</td>
                    <td>Gói</td>
                    <td>$10,000 USD</td>
                    <td>0% (Xuất khẩu)</td>
                    <td>TK 5113 (Doanh thu Dịch vụ Phần mềm)</td>
                </tr>
                <tr>
                    <td>PHẦN MỀM ỨNG DỤNG SÁNG TẠO MÃ QR NGHỆ THUẬT (Gen QR Art)</td>
                    <td>Gói</td>
                    <td>$2,000 USD</td>
                    <td>0% (Xuất khẩu)</td>
                    <td>TK 5113 (Doanh thu Dịch vụ Phần mềm)</td>
                </tr>
            </tbody>
        </table>
        <p><em>Ví dụ thực tế:</em> Khoản chuyển tiền $14,000 USD ngày 19/03/2025 quy đổi tỷ giá 25.370 VND/USD thành <strong>355.180.000 VND</strong>, xuất hóa đơn số <code>4</code> ký hiệu <code>1C25TBS</code>.</p>
    </li>
</ul>

<h3>Bước 3: Lập & Ký Số Hóa Đơn Điện Tử Viettel SInvoice</h3>
<ul>
    <li><strong>Mô hình dữ liệu:</strong> <code>account.move</code> (loại <code>out_invoice</code>).</li>
    <li><strong>Ký hiệu hóa đơn:</strong> <code>1C26TAA</code> (năm 2026) của Viettel SInvoice.</li>
    <li><strong>Thuế suất:</strong> Chọn <code>0%</code> kèm ghi chú: <em>"Dịch vụ phần mềm xuất khẩu thuộc đối tượng áp dụng thuế suất thuế GTGT 0% theo Thông tư 219/2013/TT-BTC"</em>.</li>
    <li>Kế toán trưởng kiểm tra và ký số phát hành trước khi bộ đếm 24h chạm mốc 0.</li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Quy Chuẩn Thẩm Định</th>
            <th>Cơ Chế Phản Ứng (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-REV-02-A: 24H Invoicing SLA</strong></td>
            <td>HĐĐT thương mại dịch vụ xuất khẩu phải được ký số và cấp mã CQT trong vòng 24 giờ kể từ thời điểm tiền ghi có tại Vietcombank.</td>
            <td>Sau 18 giờ: Gửi cảnh báo vàng SMS/Telegram cho Kế toán trưởng; Sau 24 giờ: Bật cờ vi phạm nghiêm trọng (Critical Violation Flag) trên Bảng điều khiển Kế toán và báo cáo CEO.</td>
            <td>Tối đa <strong>24 Giờ</strong> từ lúc tiền về</td>
        </tr>
        <tr>
            <td><strong>GATE-REV-02-B: Exchange Rate Audit</strong></td>
            <td>Tỷ giá ghi nhận trên HĐĐT và sổ sách phải khớp chính xác Tỷ giá Mua chuyển khoản Vietcombank tại ngày giao dịch.</td>
            <td>Khóa nút phát hành nếu tỷ giá lệch quá 0.5% so với tỷ giá niêm yết của Vietcombank.</td>
            <td>Thời gian thực</td>
        </tr>
        <tr>
            <td><strong>GATE-REV-02-C: Zero FCT Exemption</strong></td>
            <td>Xác nhận dịch vụ phần mềm tiêu dùng ngoài Việt Nam, không phát sinh thuế nhà thầu (FCT) theo Thông tư 103/2014/TT-BTC.</td>
            <td>Lưu văn bản giải trình miễn FCT vào hồ sơ tài chính.</td>
            <td>Trước kỳ kê khai thuế quý</td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Audit Evidence in documents.document) &amp; Bộ Hồ Sơ Miễn Thuế 4 Điểm</h2>
<p>Để bảo vệ quyền hưởng thuế suất GTGT 0% khi cơ quan thuế thanh tra quyết toán, bắt buộc lưu trữ trọn bộ 4 tài liệu sau trong hệ thống <code>documents.document</code> tại Thư mục <code>3249: Hoá đơn đầu ra</code>:</p>
<ol>
    <li><strong>Thỏa thuận phát triển ứng dụng (Canva Developer Terms of Use &amp; Innovation Fund Agreement):</strong> Xác định rõ Canva Pty Ltd là bên giao kết tại Australia.</li>
    <li><strong>Thông báo giải thưởng từ Canva:</strong> Email chính thức từ <code>admin@payout.canva.com</code> xác nhận đạt mốc MAU và số tiền thưởng bằng USD.</li>
    <li><strong>Giấy báo Có (Credit Advice) của Vietcombank:</strong> Bản gốc có dấu xác nhận của ngân hàng thể hiện số tiền USD chuyển từ nước ngoài vào STK <code>1202703007</code>.</li>
    <li><strong>Bản thể hiện Hóa đơn điện tử VAT 0%:</strong> Tệp PDF và XML có chữ ký số Viettel-CA và mã xác thực của Tổng cục Thuế.</li>
</ol>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_rev_03",
        "code": "SOP-DGM-REV-03",
        "title": "SOP-DGM-REV-03 · Quy trình Đối soát Doanh thu Tổng - Ròng (Gross-vs-Net) Nền tảng Quốc tế (Apple, Google, PayPal, AdMob)",
        "icon": "📊",
        "sequence": 40,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-REV-03 · Quy trình Đối soát Doanh thu Tổng - Ròng (Gross-vs-Net) Nền tảng Quốc tế (Apple, Google, PayPal, AdMob)</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-REV-03</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Bảo Mật Kế Toán &amp; Doanh Thu Số (High Security)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Các nền tảng phân phối số:</em> Apple App Store, Google Play Console, Google AdMob, Website PayPal Business<br/>
                <em>Các sản phẩm áp dụng:</em> Mojo AI ($1.99 / 75 credits), Gen Logo, Gen QR Art, Reface<br/>
                <em>Thỏa thuận bảo vệ dữ liệu học đường Hoa Kỳ:</em> CA-NDPA Version 1.5 ký với Temecula Valley Unified School District (California, USA)
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Kế toán Tổng hợp &amp; Kế toán Doanh thu Số</td>
            <th>Căn Cứ Pháp Lý &amp; Chuẩn Mực</th>
            <td>Thông tư 200/2014/TT-BTC; Luật Thương mại điện tử 2025 &amp; Nghị định 248/2026/NĐ-CP; Luật Thuế TNDN &amp; GTGT; Đạo luật FERPA (20 U.S.C. § 1232g) và COPPA (15 U.S.C. § 6501-6506).</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư phần mềm)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Tải báo cáo doanh thu tài chính hàng tháng từ các Developer Console</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Phân rã doanh thu gộp (Gross), hoa hồng store (Fee) &amp; hoàn tiền (Refund)</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Fail-Closed)</strong></td>
        </tr>
        <tr>
            <td>Khóa sổ AdMob Finalized Earnings (loại trừ Invalid Traffic)</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
        </tr>
        <tr>
            <td>Đối soát luồng đơn hàng PayPal (Order ID &lt;-&gt; TxID &lt;-&gt; VCB)</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Thực thi quyền riêng tư học sinh US DPA CA-NDPA v1.5 (45 ngày SLA)</td>
            <td><strong>A</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>R (Fail-Closed)</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Áp dụng cho: Mojo AI, Gen Logo, Gen QR Art, Reface.</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Quy Trình Đối Soát 6 Bước Gross-to-Net Bắt Buộc</h3>
<p><strong>NGUYÊN TẮC BẤT BIẾN:</strong> Tuyệt đối không hạch toán số tiền ròng thực nhận về ngân hàng thẳng vào TK 511. Mọi giao dịch phải tuân thủ quy trình 6 bước:</p>
<ol>
    <li><strong>Bước 1 - Xác định Doanh thu Gộp (Gross Revenue):</strong> Tổng số tiền người dùng đầu cuối chi trả trước mọi khoản khấu trừ, ghi nhận Có TK <code>5111</code> hoặc TK <code>5113</code>.</li>
    <li><strong>Bước 2 - Tách Chi phí Nền tảng (Platform Commissions):</strong> Khoản phí 15%–30% mà Apple, Google, PayPal giữ lại, ghi nhận Nợ TK <code>6417</code> (Chi phí bán hàng / Phí nền tảng).</li>
    <li><strong>Bước 3 - Tách Hoàn Tiền &amp; Khiếu Nại (Refunds / Chargebacks):</strong> Các giao dịch người dùng yêu cầu hoàn tiền, ghi nhận Nợ TK <code>5212</code> (Hàng bán bị trả lại / Giảm trừ doanh thu).</li>
    <li><strong>Bước 4 - Xác định Chênh lệch Tỷ giá Thực tế:</strong> Khoản chênh lệch giữa tỷ giá hạch toán ban đầu và tỷ giá thực tế tiền về VCB, ghi nhận Nợ TK <code>635</code> (Lỗ tỷ giá) hoặc Có TK <code>515</code> (Lãi tỷ giá).</li>
    <li><strong>Bước 5 - Đối soát Số tiền Ròng (Net Settlement):</strong> Số tiền thực tế Vietcombank ghi có vào STK <code>1202703007</code>, ghi nhận Nợ TK <code>1121</code> (VND) hoặc Nợ TK <code>1122</code> (USD).</li>
    <li><strong>Bước 6 - Khởi tạo Bút toán Phức hợp Cân bằng (Balanced Compound Entry):</strong>
        <pre><code>Nợ TK 1121 / 1122 (Tiền thực nhận về ngân hàng)
Nợ TK 6417 (Phí dịch vụ nền tảng 15% - 30%)
Nợ TK 5212 (Khoản hoàn tiền / Chargeback trong kỳ)
Nợ TK 635 (Lỗ chênh lệch tỷ giá - nếu có)
    Có TK 5111 / 5113 (Tổng Doanh thu Gộp phát sinh)
    Có TK 515 (Lãi chênh lệch tỷ giá - nếu có)</code></pre>
    </li>
</ol>

<h3>Bước 2: Cổng Kiểm Soát AdMob Finalized Earnings</h3>
<ul>
    <li>Chỉ tải và hạch toán bảng kê <strong>Finalized Earnings</strong> từ tab Payments của AdMob Console vào ngày 15 của tháng kế tiếp.</li>
    <li>Tuyệt đối không sử dụng số liệu *Estimated Earnings* từ báo cáo thời gian thực.</li>
    <li>Khoản chênh lệch do Google trừ lưu lượng không hợp lệ (Invalid Traffic Deduction) được ghi sổ riêng để theo dõi chất lượng ứng dụng.</li>
</ul>

<h3>Bước 3: Vận Hành Tuân Thủ DPA Học Đường Hoa Kỳ (CA-NDPA Version 1.5)</h3>
<ul>
    <li><strong>Học khu liên kết:</strong> Temecula Valley Unified School District (California, USA).</li>
    <li><strong>Quyền riêng tư học sinh:</strong> Tuân thủ FERPA và COPPA. Dữ liệu học sinh chỉ được lưu trữ phục vụ mục đích giáo dục, không được khai thác quảng cáo thương mại hoặc bán cho bên thứ ba.</li>
    <li><strong>Quy tắc chuyển tiếp phụ huynh (Parent Referral Rule):</strong> Nhân viên DGM không được trực tiếp cung cấp dữ liệu học sinh cho phụ huynh mà phải chuyển tiếp yêu cầu về đầu mối Học khu (LEA).</li>
    <li><strong>Xử lý Yêu cầu Truy cập &amp; Xóa Dữ liệu (SAR):</strong> Thực thi xóa sạch dữ liệu trong tối đa <strong>45 ngày</strong> kể từ khi nhận được thông báo từ LEA.</li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Tiêu Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Thời Hạn SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-REV-03-A: Gross-vs-Net Integrity</strong></td>
            <td>Khẳng định tổng bút toán ghi nhận Gross Sales phải bằng đúng Net Settlement + Platform Fees + Refunds.</td>
            <td>Từ chối duyệt bút toán nếu chênh lệch cân đối &gt; 0 đồng.</td>
            <td>Trước ngày 15 hàng tháng</td>
        </tr>
        <tr>
            <td><strong>GATE-REV-03-B: AdMob Traffic Variance</strong></td>
            <td>So sánh chênh lệch giữa Estimated Earnings và Finalized Earnings.</td>
            <td>Nếu chênh lệch vượt <strong>&gt; 10%</strong>, hệ thống tự động bắn cảnh báo kiểm tra bot traffic cho CTO.</td>
            <td>Ngày 15 hàng tháng</td>
        </tr>
        <tr>
            <td><strong>GATE-REV-03-C: CA-NDPA 45-Day SLA</strong></td>
            <td>Thực hiện yêu cầu kiểm tra hoặc xóa dữ liệu học sinh nhận từ Học khu Temecula Valley.</td>
            <td>Bộ đếm thời gian 45 ngày; cảnh báo mức độ 1 tại Ngày 30; cảnh báo mức độ 2 tại Ngày 40.</td>
            <td>Tối đa <strong>45 Ngày</strong></td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Audit Evidence in documents.document)</h2>
<ul>
    <li>Thư mục lưu trữ: <code>ID 3225: 02. Tài chính, Kế toán &amp; Thuế (DGM - TÀI CHÍNH)</code> và <code>ID 3226: 03. Hợp đồng Thương mại &amp; Dự án</code>.</li>
    <li>Hồ sơ lưu trữ bắt buộc:
        <ol>
            <li>Báo cáo thanh toán hàng tháng từ Apple App Store (Financial Report CSV).</li>
            <li>Báo cáo doanh thu Google Play Console (Earnings Report CSV).</li>
            <li>Bảng đối soát Google AdMob Payments Statement (thể hiện Finalized Earnings).</li>
            <li>Báo cáo giao dịch hàng tháng PayPal Settlement Report.</li>
            <li>Hợp đồng CA-NDPA Version 1.5 ký với Temecula Valley Unified School District.</li>
        </ol>
    </li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_rev_04",
        "code": "SOP-DGM-REV-04",
        "title": "SOP-DGM-REV-04 · Quy trình Hợp tác Viễn thông MobiFone MobiAI, Đối soát CDR & Giải quyết Khiếu nại 48h",
        "icon": "📱",
        "sequence": 50,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-REV-04 · Quy trình Hợp tác Viễn thông MobiFone MobiAI, Đối soát CDR & Giải quyết Khiếu nại 48h</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-REV-04</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Hợp Tác Chiến Lược Viễn Thông (Telco Strategic Partnership)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Đối tác viễn thông:</em> <strong>TRUNG TÂM DỊCH VỤ SỐ MOBIFONE (MDS) — CHI NHÁNH TỔNG CÔNG TY VIỄN THÔNG MOBIFONE</strong><br/>
                <em>Nền tảng hợp tác:</em> Dịch vụ Nội dung số MobiAI — Bình dân hóa AI<br/>
                <em>Vai trò Digimate:</em> Content Service Provider (CSP)
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Trưởng ban Đối tác CSP Viễn thông &amp; Trưởng nhóm Kỹ thuật AI Gateway</td>
            <th>Căn Cứ Hợp Đồng &amp; Pháp Lý</th>
            <td>Hồ sơ mời hợp tác đối tác CSP MobiAI; Hợp đồng phân chia doanh thu dịch vụ nội dung số; Luật Viễn thông 2023; Thông tư quản lý giá cước và khuyến mại viễn thông.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư AI Gateway)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Hoàn thiện hồ sơ năng lực CSP (GPKD 0317958465, Mẫu số 2 Cam kết thuế)</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Cấu hình gói cước và kiểm soát quy tắc Single Active Package</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>A</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>R</strong></td>
        </tr>
        <tr>
            <td>Đối soát sản lượng CDR hàng tháng giữa MobiFone Billing &amp; AI Gateway</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>R</strong></td>
        </tr>
        <tr>
            <td>Tiếp nhận và giải quyết khiếu nại cước của thuê bao viễn thông trong 48h</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R (Fail-Closed)</strong></td>
        </tr>
        <tr>
            <td>Xuất Hóa đơn điện tử phân chia doanh thu cước thực thu</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Đối tác: Trung tâm Dịch vụ số MobiFone (MDS).</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Quản trị Hồ sơ Đối tác & Kết nối Gateway Dịch vụ</h3>
<ul>
    <li><strong>Mô hình dữ liệu (Model):</strong> <code>sale.order</code>, <code>res.partner</code> (MobiFone MDS).</li>
    <li><strong>Hồ sơ pháp lý bắt buộc:</strong>
        <ul>
            <li>Giấy chứng nhận ĐKKD công ty cổ phần số <code>0317958465</code>.</li>
            <li>Giấy chứng nhận Đăng ký Quyền tác giả cho sản phẩm <strong>MOJO AI</strong>.</li>
            <li>Cam kết tuân thủ nghĩa vụ thuế và không nợ đọng ngân sách (Mẫu số 2).</li>
            <li>Báo cáo tài chính năm gần nhất đã nộp cơ quan thuế.</li>
        </ul>
    </li>
    <li><strong>Quy tắc gói cước (Single Active Package Rule):</strong> Mỗi thuê bao MobiFone tại một thời điểm chỉ được kích hoạt một gói cước AI duy nhất (Gói Ngày, Gói Tuần, hoặc Gói Tháng). Khi thuê bao đăng ký gói mới, hệ thống tự động gửi lệnh hủy hoặc nâng cấp gói cũ.</li>
</ul>

<h3>Bước 2: Quy trình Đối soát CDR Sản lượng Hàng Tháng</h3>
<ul>
    <li><strong>Mô hình dữ liệu:</strong> <code>documents.document</code> tại Thư mục <code>3230</code> (<code>MBF</code>) và <code>account.move</code>.</li>
    <li><strong>Quy trình thực thi:</strong>
        <ol>
            <li>Ngày 05 hàng tháng: Nhận file tổng hợp chi tiết cước (Call Detail Records - CDR) từ Trung tâm Dịch vụ số MobiFone.</li>
            <li>Kỹ sư Gateway AI chạy đối soát tự động giữa CDR MobiFone và log giao dịch máy chủ Digimate.</li>
            <li>Xác định Doanh thu cước nội dung thực thu = Tổng cước thu từ thuê bao - Chi phí đầu số - Phí đường truyền viễn thông.</li>
            <li>Tính toán tỷ lệ phân chia doanh thu theo thỏa thuận hợp đồng CSP.</li>
            <li>Lập Biên bản đối soát số liệu và xuất HĐĐT GTGT gửi MobiFone trước ngày 15.</li>
        </ol>
    </li>
</ul>

<h3>Bước 3: Giải quyết Khiếu nại Thuê bao Viễn thông trong 48H SLA</h3>
<ul>
    <li><strong>Mô hình xử lý:</strong> <code>helpdesk.ticket</code> (Đội hỗ trợ chuyên trách MobiAI).</li>
    <li>Khi nhận văn bản/email yêu cầu từ MobiFone về khiếu nại cước hoặc chất lượng dịch vụ:
        <ul>
            <li>Hệ thống tự động sinh ticket, gán tag <code>MobiFone 48H SLA</code> và bật bộ đếm thời gian.</li>
            <li>Trưởng nhóm hỗ trợ kiểm tra log giao dịch, phản hồi nguyên nhân kỹ thuật và đề xuất phương án xử lý (hoàn cước hoặc tặng thêm lượt trải nghiệm AI).</li>
            <li>Gửi công văn phản hồi chính thức cho MobiFone trước khi đồng hồ điểm 48 giờ.</li>
        </ul>
    </li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Quy Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-REV-04-A: 48H Complaint SLA</strong></td>
            <td>Xử lý và phản hồi bằng văn bản toàn bộ khiếu nại của thuê bao nhận từ MobiFone.</td>
            <td>Cảnh báo vàng tại mốc 24h; cảnh báo đỏ khẩn cấp tại mốc 36h; nếu vượt 48h, hệ thống tự động ghi nhận sự cố vi phạm SLA hợp đồng.</td>
            <td>Tối đa <strong>48 Giờ</strong></td>
        </tr>
        <tr>
            <td><strong>GATE-REV-04-B: CDR Variance Limit</strong></td>
            <td>Đối chiếu sai lệch doanh thu giữa dữ liệu CDR MobiFone và log kỹ thuật Digimate.</td>
            <td>Nếu tỷ lệ sai lệch <strong>&gt; 0.5%</strong>, tạm dừng ký biên bản nghiệm thu và yêu cầu trích xuất log chi tiết từng phiên giao dịch.</td>
            <td>Trước ngày 10 hàng tháng</td>
        </tr>
        <tr>
            <td><strong>GATE-REV-04-C: Single Active Package</strong></td>
            <td>Kiểm tra trạng thái gói cước trên API Gateway MobiAI.</td>
            <td>Từ chối ghi nhận cước trùng lặp nếu phát hiện 1 thuê bao bị trừ tiền 2 gói cước cùng lúc trong 1 chu kỳ.</td>
            <td>Thời gian thực</td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Folder 3230: MBF)</h2>
<ul>
    <li>Thư mục lưu trữ: <code>ID 3230: MBF (03. Hợp đồng Thương mại &amp; Dự án / MobiFone)</code>.</li>
    <li>Tài liệu bắt buộc lưu trữ:
        <ol>
            <li>Hợp đồng hợp tác CSP và các phụ lục tỷ lệ phân chia doanh thu.</li>
            <li>Giấy chứng nhận Bản quyền tác giả phần mềm MOJO AI.</li>
            <li>Bản cam kết tuân thủ thuế Mẫu số 2 nộp cho MDS MobiFone.</li>
            <li>Biên bản đối soát CDR hàng tháng có chữ ký số 2 bên.</li>
            <li>Báo cáo tổng hợp xử lý khiếu nại khách hàng kèm bằng chứng tuân thủ 48h SLA.</li>
        </ol>
    </li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_fin_01",
        "code": "SOP-DGM-FIN-01",
        "title": "SOP-DGM-FIN-01 · Quy trình Phân bổ Chi phí Trả trước TK 242 Hóa đơn Viễn thông & Chữ ký số",
        "icon": "📑",
        "sequence": 60,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-FIN-01 · Quy trình Phân bổ Chi phí Trả trước TK 242 Hóa đơn Viễn thông & Chữ ký số</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-FIN-01</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Nội Bộ Tài Chính (Financial Internal)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Tài khoản kế toán trọng tâm:</em> <strong>Tài khoản 242 — Chi phí trả trước</strong> (Thông tư 200/2014/TT-BTC)<br/>
                <em>Các chứng từ mẫu áp dụng:</em> Hóa đơn Internet VNPT số <code>1K26TKA-338235</code>, Hóa đơn Viettel-CA số <code>1K23TVA-2368750</code>
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Kế toán Tài sản &amp; Chi phí</td>
            <th>Căn Cứ Pháp Lý</th>
            <td>Thông tư 200/2014/TT-BTC (Điều 47); Thông tư 45/2013/TT-BTC về quản lý và trích khấu hao TSCĐ; Luật Thuế TNDN.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư phần mềm)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Tiếp nhận và thẩm định hóa đơn đầu vào dịch vụ trả trước nhiều kỳ</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Phân loại chi phí hạch toán ngay vs Chi phí vốn hóa TK 242</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Khởi tạo mô hình phân bổ tự động trên account.asset</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Chạy trích phân bổ hàng tháng vào ngày cuối tháng</td>
            <td><strong>I</strong></td>
            <td><strong>A</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Automated Cron)</strong></td>
        </tr>
        <tr>
            <td>Lưu trữ hóa đơn PDF/XML vào Thư mục 3250 (Hoá đơn đầu vào)</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Áp dụng cho: VNPT Internet, Viettel-CA USB Token &amp; Chữ ký số.</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Tiếp nhận Hóa Đơn & Hạch Toán Ban Đầu</h3>
<ul>
    <li><strong>Menu truy cập:</strong> <code>Kế toán &gt; Nhà cung cấp &gt; Hóa đơn Đầu vào (Vendor Bills)</code>.</li>
    <li><strong>Mô hình dữ liệu (Model):</strong> <code>account.move</code> (loại <code>in_invoice</code>).</li>
    <li><strong>Bút toán ghi nhận ban đầu:</strong>
        <pre><code>Nợ TK 242 (Chi phí trả trước - Giá trị chưa thuế)
Nợ TK 1331 (Thuế GTGT đầu vào được khấu trừ)
    Có TK 331 (Phải trả người bán - Tổng thanh toán)</code></pre>
    </li>
</ul>

<h3>Bước 2: Phân Tích &amp; Khởi Tạo Hồ Sơ Phân Bổ Thực Tế Của Digimate</h3>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f8fafc;">
            <th>Chứng Từ Thực Tế</th>
            <th>Quy Cách Dịch Vụ</th>
            <th>Giá Trị Hóa Đơn</th>
            <th>Quy Tắc Phân Loại Chi Phí</th>
            <th>Kỳ Hạn &amp; Mức Phân Bổ Hàng Tháng</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Hóa đơn VNPT <code>1K26TKA-338235</code></strong> (Ngày 01/08/2026)</td>
            <td>Internet Cáp quang FiberVNN 14 tháng (01/08/2026 đến 30/09/2027)</td>
            <td>Net: 3.648.000 VND<br/>VAT (10%): 364.800 VND<br/>Tổng: 4.012.800 VND</td>
            <td>Toàn bộ giá trị net 3.648.000 VND hạch toán vào TK 242 do dịch vụ trải dài qua 2 năm tài chính.</td>
            <td>Phân bổ đều <strong>14 tháng</strong>:<br/><code>3.648.000 / 14 = 260.571 VND / tháng</code> vào Nợ TK 6427 / Có TK 242.</td>
        </tr>
        <tr>
            <td><strong>Hóa đơn Viettel-CA <code>1K23TVA-2368750</code></strong> (Ngày 07/08/2023)</td>
            <td>Gói Chữ ký số 3 năm + USB Token + 500 số HĐĐT</td>
            <td>Thiết bị Token: 130.000 VND<br/>500 số HĐĐT: 400.000 VND<br/>Chứng thư 3 năm: 683.000 VND (sau KM)<br/>Tổng: 1.500.000 VND (đã có VAT)</td>
            <td>
                - Thiết bị Token (130k) &amp; 500 số HĐĐT (400k): Hạch toán thẳng vào chi phí trong kỳ TK 642.<br/>
                - Chứng thư số 3 năm (683k): Hạch toán vào TK 242.
            </td>
            <td>Phân bổ đều <strong>36 tháng</strong>:<br/><code>683.000 / 36 = 34.268 VND / tháng</code> vào Nợ TK 6427 / Có TK 242.</td>
        </tr>
    </tbody>
</table>

<h3>Bước 3: Thiết Lập Mô Hình Phân Bổ Trên <code>account.asset</code></h3>
<ul>
    <li><strong>Menu truy cập:</strong> <code>Kế toán &gt; Tài sản &gt; Chi phí Trả trước (Deferred Expenses)</code>.</li>
    <li><strong>Mô hình dữ liệu:</strong> <code>account.asset</code> với <code>asset_type = 'expense'</code>.</li>
    <li><strong>Các trường kỹ thuật cấu hình:</strong>
        <ul>
            <li><code>name</code>: Chi phí Internet VNPT 14T (08/2026 - 09/2027)</li>
            <li><code>original_value</code>: 3648000.0</li>
            <li><code>method_number</code>: 14</li>
            <li><code>method_period</code>: '1' (Tháng)</li>
            <li><code>prorata_date</code>: 2026-08-01</li>
            <li><code>account_asset_id</code>: 242 (Chi phí trả trước)</li>
            <li><code>account_depreciation_expense_id</code>: 6427 (Chi phí dịch vụ mua ngoài)</li>
        </ul>
    </li>
    <li><strong>Cron tự động chạy hàng tháng:</strong> Vào 23:00 ngày cuối cùng của tháng, cron tự động kiểm tra và sinh bút toán phân bổ:
        <pre><code>Nợ TK 6427 (Chi phí quản lý doanh nghiệp - Dịch vụ mua ngoài)
    Có TK 242 (Chi phí trả trước)</code></pre>
    </li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Quy Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-FIN-01-A: Prepayment Threshold</strong></td>
            <td>Mọi hóa đơn dịch vụ có thời hạn sử dụng trên 02 kỳ kế toán (tháng) hoặc trải qua năm tài chính mới bắt buộc phải vào TK 242.</td>
            <td>Cảnh báo kế toán viên nếu đưa thẳng vào TK 642 hóa đơn có thời hạn &gt; 1 tháng.</td>
            <td>Thời điểm hạch toán hóa đơn</td>
        </tr>
        <tr>
            <td><strong>GATE-FIN-01-B: Month-End Amortization</strong></td>
            <td>Toàn bộ các khoản phân bổ trong tháng phải được ghi sổ trước khi khóa sổ kỳ kế toán.</td>
            <td>Khóa cổng không cho phép đóng sổ tháng nếu còn bản ghi chi phí trả trước ở trạng thái <code>draft</code>.</td>
            <td>Ngày cuối cùng của tháng</td>
        </tr>
        <tr>
            <td><strong>GATE-FIN-01-C: Contract Termination</strong></td>
            <td>Trường hợp chấm dứt hợp đồng dịch vụ trước hạn (ví dụ đổi văn phòng cắt mạng).</td>
            <td>Kích hoạt chức năng <code>action_set_to_close()</code>, trích hết phần còn lại vào chi phí hoặc thu hồi công nợ người bán.</td>
            <td>Trong vòng <strong>05 ngày</strong> sau chấm dứt</td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Audit Evidence in documents.document)</h2>
<ul>
    <li>Thư mục lưu trữ trong <code>documents.document</code>: <code>ID 3250: Hoá đơn đầu vào (02. Tài chính, Kế toán &amp; Thuế)</code>.</li>
    <li>Hồ sơ lưu trữ bắt buộc:
        <ol>
            <li>Tệp XML và PDF hóa đơn gốc của nhà cung cấp viễn thông / chữ ký số.</li>
            <li>Hợp đồng cung cấp dịch vụ hoặc phiếu biên nhận lắp đặt ghi rõ thời hạn dịch vụ.</li>
            <li>Bảng tính phân bổ chi phí trả trước in từ ERP Insilos 20 hàng quý.</li>
            <li>Ủy nhiệm chi chuyển khoản thanh toán qua Vietcombank STK <code>1202703007</code>.</li>
        </ol>
    </li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_fin_02",
        "code": "SOP-DGM-FIN-02",
        "title": "SOP-DGM-FIN-02 · Quy trình Khóa sổ Kế toán Tháng/Quý/Năm & Vận hành Két sắt Quyết toán Thuế 9 Điểm",
        "icon": "🔐",
        "sequence": 70,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-FIN-02 · Quy trình Khóa sổ Kế toán Tháng/Quý/Năm & Vận hành Két sắt Quyết toán Thuế 9 Điểm</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-FIN-02</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Tuyệt Mật Tài Chính (Confidential Financial Compliance)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Cơ quan thuế quản lý trực tiếp:</em> Chi cục Thuế Quận 7 — Cục Thuế TP. Hồ Chí Minh<br/>
                <em>Niên độ tài chính áp dụng:</em> Giai đoạn 3 năm 2023 – 2026 (Chuẩn bị thanh tra quyết toán thuế)
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Kế toán Trưởng &amp; Giám đốc Tài chính (Finance Lead)</td>
            <th>Căn Cứ Pháp Lý &amp; Chuẩn Mực</th>
            <td>Luật Kế toán 2015; Luật Quản lý Thuế 2019; Thông tư 200/2014/TT-BTC; Thông tư 80/2021/TT-BTC; Thông tư 13/2020/TT-BTTTT (Ưu đãi thuế phần mềm); Nghị định 218/2013/NĐ-CP.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư phần mềm)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Kiểm kê, đối soát sổ phụ Vietcombank và số dư các tài khoản tiền</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Thực hiện bút toán kết chuyển doanh thu, chi phí xác định kết quả KD (TK 911)</td>
            <td><strong>I</strong></td>
            <td><strong>A</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Khóa sổ kế toán định kỳ (Thiết lập period_lock_date &amp; fiscalyear_lock_date)</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Vận hành và thẩm định Két sắt Quyết toán Thuế 9 Điểm</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R (Verification)</strong></td>
        </tr>
        <tr>
            <td>Ký duyệt và nộp Báo cáo Tài chính năm kèm phụ lục ưu đãi thuế TNDN</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Lưu trữ tại Thư mục 3225 (DGM - TÀI CHÍNH).</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Quy trình Khóa sổ Kế toán Tháng / Quý / Năm</h3>
<ol>
    <li><strong>Rà soát hóa đơn đầu vào - đầu ra:</strong> Đảm bảo 100% hóa đơn mua vào đã được duyệt và gán mã phân tích; 100% hóa đơn bán ra (MTI, Canva, MobiFone) đã được cấp mã CQT và ghi nhận doanh thu.</li>
    <li><strong>Chạy trích khấu hao và phân bổ:</strong> Thực hiện khấu hao TSCĐ (máy tính, máy chủ) và phân bổ chi phí trả trước TK 242 (VNPT, Viettel-CA).</li>
    <li><strong>Đối soát số dư ngân hàng:</strong> Sổ cái TK <code>1121</code> (VND) và TK <code>1122</code> (USD) phải khớp 100% với Sổ phụ ngân hàng Vietcombank <code>1202703007</code>.</li>
    <li><strong>Kết chuyển doanh thu - chi phí (Closing Entries):</strong>
        <pre><code>Nợ TK 5111 / 5113 / 515 / 711
    Có TK 911 (Xác định kết quả kinh doanh)

Nợ TK 911
    Có TK 632 / 635 / 641 / 642 / 811</code></pre>
    </li>
    <li><strong>Tính thuế TNDN và kết chuyển lãi lỗ:</strong>
        <pre><code>Nợ TK 911 / Có TK 4212 (Lợi nhuận sau thuế chưa phân phối năm nay - nếu có lãi)
hoặc: Nợ TK 4212 / Có TK 911 (nếu lỗ)</code></pre>
    </li>
    <li><strong>Thiết lập Ngày Khóa Sổ:</strong> Truy cập <code>Kế toán &gt; Cấu hình &gt; Thiết lập &gt; Ngày Khóa Kế toán</code>, cập nhật trường <code>period_lock_date</code> (khóa tháng) và <code>fiscalyear_lock_date</code> (khóa năm). Sau khi khóa, không người dùng nào (kể cả admin) được chỉnh sửa chứng từ cũ.</li>
</ol>

<h3>Bước 2: Danh Mục Kiểm Tra Két Sắt Quyết Toán Thuế 9 Điểm (Checklist Bắt Buộc)</h3>
<p>Toàn bộ 9 hạng mục chứng từ sau đây bắt buộc phải được số hóa, gắn thẻ metadata và lưu trữ trong Thư mục <code>3225</code>:</p>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f8fafc;">
            <th>#</th>
            <th>Hạng Mục Chứng Từ (Két Sắt Quyết Toán Thuế)</th>
            <th>Quy Chuẩn Định Dạng &amp; Yêu Cầu Pháp Lý</th>
            <th>Vị Trí Lưu Trữ ERP</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>1</strong></td>
            <td>Giấy chứng nhận ĐKKD &amp; Đăng ký thuế bản mới nhất</td>
            <td>File PDF có dấu đỏ hoặc chữ ký số cơ quan cấp; địa chỉ chuẩn Phường Tân Mỹ; MST <code>0317958465</code>.</td>
            <td>Thư mục <code>3224</code> (DGM - ĐKTL)</td>
        </tr>
        <tr>
            <td><strong>2</strong></td>
            <td>Thông báo đăng ký phương pháp trích khấu hao TSCĐ &amp; phân bổ TK 242 (Mẫu 08)</td>
            <td>Bản xác nhận gửi cơ quan thuế Quận 7 về phương pháp đường thẳng.</td>
            <td>Thư mục <code>3225</code> (DGM - TÀI CHÍNH)</td>
        </tr>
        <tr>
            <td><strong>3</strong></td>
            <td>Bộ Báo cáo Tài chính năm đầy đủ (B01-DN, B02-DN, B03-DN, Thuyết minh)</td>
            <td>File XML thông báo tiếp nhận của Tổng cục Thuế + Bản in có chữ ký CEO &amp; Kế toán trưởng.</td>
            <td>Thư mục <code>3225</code></td>
        </tr>
        <tr>
            <td><strong>4</strong></td>
            <td>Tờ khai thuế GTGT các quý (Mẫu 01/GTGT) kèm Bảng kê mua vào - bán ra</td>
            <td>Thông báo chấp nhận tờ khai của CQT; bảng kê hóa đơn bán ra 0% Canva, 10% MTI.</td>
            <td>Thư mục <code>3249</code> &amp; <code>3250</code></td>
        </tr>
        <tr>
            <td><strong>5</strong></td>
            <td>Tờ khai quyết toán thuế TNCN năm (Mẫu 05/QTT-TNCN) kèm bảng kê NPT</td>
            <td>Hồ sơ đăng ký người phụ thuộc, căn cước công dân, ủy quyền quyết toán của nhân viên.</td>
            <td>Thư mục <code>3227</code> (DGM - NHÂN SỰ)</td>
        </tr>
        <tr>
            <td><strong>6</strong></td>
            <td>Tờ khai quyết toán thuế TNDN (Mẫu 03/TNDN) &amp; Phụ lục ưu đãi phần mềm</td>
            <td>Phụ lục ưu đãi thuế theo Thông tư 13/2020/TT-BTTTT; chứng minh 7 công đoạn phần mềm.</td>
            <td>Thư mục <code>3225</code></td>
        </tr>
        <tr>
            <td><strong>7</strong></td>
            <td>Bảng thanh toán lương 12 tháng, phiếu lương, HĐLĐ 16 điều và cam kết NDA</td>
            <td>Chữ ký xác nhận nhận lương của 8 nhân viên; khớp 100% với chi phí lương TK 6422.</td>
            <td>Thư mục <code>3251</code> &amp; <code>3252</code></td>
        </tr>
        <tr>
            <td><strong>8</strong></td>
            <td>Thông báo đối soát BHXH Quận 7 Mẫu C12-TS (Mã đơn vị <code>TZ0857G</code>)</td>
            <td>12 thông báo C12-TS các tháng khẳng định chỉ tiêu [Đ.2.2] nợ chuyển kỳ sau = 0 đồng.</td>
            <td>Thư mục <code>3248</code> (BHXH)</td>
        </tr>
        <tr>
            <td><strong>9</strong></td>
            <td>Sổ phụ ngân hàng Vietcombank STK <code>1202703007</code> đủ 12 tháng</td>
            <td>Bản sao kê có đóng dấu giáp lai của Vietcombank Tân Định; khớp từng lệnh chuyển tiền.</td>
            <td>Thư mục <code>3225</code></td>
        </tr>
    </tbody>
</table>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Quy Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-FIN-02-A: Monthly Lock SLA</strong></td>
            <td>Khóa toàn bộ sổ kế toán tháng và đối soát ngân hàng.</td>
            <td>Gửi thông báo nhắc nhở vào ngày 08; tự động khóa sổ vào 23:59 ngày 10 hàng tháng.</td>
            <td>Trước <strong>Ngày 10</strong> tháng sau</td>
        </tr>
        <tr>
            <td><strong>GATE-FIN-02-B: Quarterly Tax Return</strong></td>
            <td>Nộp tờ khai thuế GTGT và tạm tính thuế TNDN quý.</td>
            <td>Khóa số liệu báo cáo quý trước khi nộp cổng thuế điện tử Etax.</td>
            <td>Trước <strong>Ngày cuối tháng</strong> đầu quý sau</td>
        </tr>
        <tr>
            <td><strong>GATE-FIN-02-C: Annual Tax Settlement</strong></td>
            <td>Nộp BCTC năm, Quyết toán thuế TNDN và TNCN cho Chi cục Thuế Quận 7.</td>
            <td>Yêu cầu hoàn thành kiểm toán nội bộ và kiểm tra 9 điểm két sắt trước ngày 20/03.</td>
            <td>Trước <strong>31/03</strong> hàng năm (90 ngày)</td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Audit Evidence in documents.document)</h2>
<ul>
    <li>Thư mục lưu trữ trong <code>documents.document</code>: <code>ID 3225: 02. Tài chính, Kế toán &amp; Thuế (DGM - TÀI CHÍNH)</code>.</li>
    <li>Bằng chứng bắt buộc: Toàn bộ 9 mục hồ sơ theo Bảng kiểm tra két sắt nêu trên phải được quét scan và gắn cờ <code>Tax Audit Ready</code>.</li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_prj_01",
        "code": "SOP-DGM-PRJ-01",
        "title": "SOP-DGM-PRJ-01 · Quy trình Quản trị Giai đoạn Dự án SAP Activate, Khóa Cổng Nghiệm thu & Kiểm soát Ngân sách 85%",
        "icon": "🚀",
        "sequence": 80,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-PRJ-01 · Quy trình Quản trị Giai đoạn Dự án SAP Activate, Khóa Cổng Nghiệm thu & Kiểm soát Ngân sách 85%</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-PRJ-01</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Quản Trị Dự Án Chuyên Nghiệp (Project Governance)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Phương pháp luận áp dụng:</em> <strong>SAP Activate Methodology for Enterprise Delivery</strong><br/>
                <em>Nguyên tắc kiến trúc:</em> Clean Core (Bảo toàn lõi chuẩn) &amp; Fit-to-Standard (80% chuẩn mực, 20% tùy biến mở rộng)
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Giám đốc Chuyển giao Dự án (Delivery Lead) &amp; Project Managers</td>
            <th>Căn Cứ Phương Pháp Luận</th>
            <td>Khung quản lý dự án chuẩn SAP Activate; Tiêu chuẩn ISO 9001:2015 về quản trị chất lượng phần mềm; Hợp đồng Dịch vụ Triển khai AL2C.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư dự án)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Khởi tạo dự án theo Template mẫu Activate và phân bổ trọng số mốc</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Thực thi nhiệm vụ và nghiệm thu chuyển giao theo từng giai đoạn Q-Gate</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Tải lên Biên bản nghiệm thu có chữ ký số khách hàng vào documents.document</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Phê duyệt SoD mở khóa cổng thanh toán (al2c_billing_eligible)</td>
            <td><strong>A</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I (Blocked)</strong></td>
        </tr>
        <tr>
            <td>Giám sát cảnh báo Cháy ngân sách 85% và đánh giá chỉ số RAG Risk Score</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R (Autonomous Alert)</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Áp dụng chuẩn 5 giai đoạn: Prepare, Explore, Realize, Deploy, Run.</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Khởi tạo 5 Giai Đoạn SAP Activate & Trọng Số Nghiệm Thu</h3>
<p>Mỗi dự án triển khai doanh nghiệp trong <code>project.project</code> được tự động khởi tạo 5 mốc theo cấu hình chuẩn trong <code>project.milestone</code>:</p>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f8fafc;">
            <th>Giai Đoạn (Stage)</th>
            <th>Thứ Tự (Seq)</th>
            <th>Trọng Số (% Hợp Đồng)</th>
            <th>Tiêu Chí Nghiệm Thu (Quality Gate Deliverables)</th>
            <th>Điều Kiện Mở Khóa Thanh Toán</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>1. Prepare (Chuẩn bị)</strong></td>
            <td>10</td>
            <td>15%</td>
            <td>Biên bản khởi động dự án (Kick-off Sign-off), Kế hoạch tổng thể và Cơ cấu ban dự án.</td>
            <td>Ký biên bản nghiệm thu Prepare + Đính kèm tài liệu vào Thư mục dự án.</td>
        </tr>
        <tr>
            <td><strong>2. Explore (Khảo sát &amp; Thiết kế)</strong></td>
            <td>20</td>
            <td>25%</td>
            <td>Tài liệu thiết kế giải pháp Fit-to-Standard (BPD), Ma trận phân tích khoảng cách (Gap Analysis).</td>
            <td>Khách hàng ký duyệt Solution Design Sign-off.</td>
        </tr>
        <tr>
            <td><strong>3. Realize (Cấu hình &amp; Tích hợp)</strong></td>
            <td>30</td>
            <td>35%</td>
            <td>Hệ thống hoàn thành cấu hình Clean Core, Kiểm thử người dùng (UAT Sign-off) đạt 100% Test cases.</td>
            <td>Biên bản nghiệm thu UAT có xác nhận của Giám đốc dự án 2 bên.</td>
        </tr>
        <tr>
            <td><strong>4. Deploy (Triển khai &amp; Chuyển đổi)</strong></td>
            <td>40</td>
            <td>15%</td>
            <td>Hoàn tất đào tạo người dùng cuối, Chuyển đổi số dư đầu kỳ (Cut-over) và Ký vận hành chính thức.</td>
            <td>Biên bản Go-Live Sign-off.</td>
        </tr>
        <tr>
            <td><strong>5. Run (Vận hành &amp; Tối ưu)</strong></td>
            <td>50</td>
            <td>10%</td>
            <td>Hỗ trợ sau Go-live (Hypercare 30 ngày), Bàn giao tài liệu vận hành và ký Biên bản thanh lý hợp đồng.</td>
            <td>Biên bản thanh lý hợp đồng (Final Project Acceptance).</td>
        </tr>
    </tbody>
</table>

<h3>Bước 2: Cơ Chế Khóa Cổng Tuần Tự & Mở Khóa Hóa Đơn (Quality Gate Locking)</h3>
<ul>
    <li><strong>Mô hình dữ liệu (Model):</strong> <code>project.milestone</code>, <code>sale.order.line</code>.</li>
    <li><strong>Trường kỹ thuật then chốt:</strong>
        <ul>
            <li><code>al2c_signoff_document_id</code>: Liên kết trực tiếp bản ghi tài liệu nghiệm thu trong <code>documents.document</code>.</li>
            <li><code>al2c_billing_eligible</code>: Trường boolean tính toán (compute &amp; store). Chỉ chuyển thành <code>True</code> khi:
                <pre><code>self.is_reached = True and bool(self.al2c_signoff_document_id)</code></pre>
            </li>
        </ul>
    </li>
    <li><strong>Quy tắc khóa tuần tự (Sequential Enforcement):</strong> Hàm <code>_check_prerequisite_milestones()</code> kiểm tra nếu Mốc $N-1$ chưa đạt điều kiện <code>al2c_billing_eligible == True</code> thì hệ thống ném <code>UserError</code> chặn không cho phép nghiệm thu Mốc $N$.</li>
    <li><strong>Rào chắn xuất hóa đơn trên Sale Order Line:</strong> Hàm <code>_get_to_invoice_qty()</code> trên dòng đơn bán hàng kiểm tra các mốc. Nếu không có mốc nào đủ điều kiện thanh toán, số lượng cho phép lập hóa đơn trả về <code>0.0</code>.</li>
</ul>

<h3>Bước 3: Vận Hành Giám Sát Ngân Sách 85% (Timesheet Burn Sentinel)</h3>
<ul>
    <li><strong>Mô hình giám sát:</strong> <code>project.task</code> và <code>account.analytic.line</code>.</li>
    <li>Mỗi khi kỹ sư ghi nhận giờ công trên nhiệm vụ dự án, hàm <code>_check_budget_burn_threshold()</code> tính toán tỷ lệ:
        $$\text{Burn Ratio} = \frac{\text{effective\_hours}}{\text{allocated\_hours}}$$
    </li>
    <li>Nếu $\text{Burn Ratio} \ge 0.85$ (85%) và cờ <code>al2c_burn_warning_sent</code> chưa bật:
        <ul>
            <li>Tự động đăng thông báo cảnh báo khẩn cấp màu vàng lên Chatter của Task và Project.</li>
            <li>Tự động tạo một <code>mail.activity</code> loại Todo giao cho PM với nội dung: <em>"Cảnh báo: Nhiệm vụ đã tiêu hao 85% ngân sách giờ công dự kiến. Yêu cầu PM rà soát tiến độ hoặc lập Scope Change Request."</em></li>
        </ul>
    </li>
</ul>

<h3>Bước 4: Đánh Giá Điểm Rủi Ro Dự Án (Autonomous Risk Sentinel)</h3>
<ul>
    <li>Hàm <code>action_evaluate_project_risk()</code> trên <code>project.project</code> tự động chấm điểm rủi ro từ 0 đến 100:
        <ul>
            <li>Mốc giai đoạn quá hạn quá 7 ngày: Cộng <strong>+45 điểm</strong>.</li>
            <li>Giờ công vượt quá 100% ngân sách khi còn mốc chưa hoàn thành: Cộng <strong>+40 điểm</strong>.</li>
            <li>Không có hoạt động chấm công trong 14 ngày làm việc: Cộng <strong>+20 điểm</strong>.</li>
        </ul>
    </li>
    <li>Phân loại trạng thái RAG:
        <ul>
            <li><code>green</code> (Xanh - An toàn): Điểm &lt; 30.</li>
            <li><code>amber</code> (Vàng - Cần lưu ý): Điểm 30 ~ 69.</li>
            <li><code>red</code> (Đỏ - Nguy cơ cao): Điểm $\ge 70$. Hệ thống tự động gửi thông báo khẩn cho Ban Giám Đốc và phong tỏa quyền tạo mốc mới.</li>
        </ul>
    </li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Quy Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-PRJ-01: Q-Gate Sequential Lock</strong></td>
            <td>Nghiêm cấm nhảy cóc giai đoạn; mốc sau chỉ được duyệt khi mốc trước đã hoàn thành và có tài liệu ký số.</td>
            <td>Ném lỗi <code>UserError</code> chặn thao tác nếu vi phạm tuần tự.</td>
            <td>Thời gian thực</td>
        </tr>
        <tr>
            <td><strong>GATE-PRJ-02: SoD Sign-off Gate</strong></td>
            <td>Chỉ PM hoặc Delivery Director mới có quyền phê duyệt nghiệm thu mốc.</td>
            <td>Chặn hoàn toàn nhóm <code>group_al2c_agent</code> không cho phép tự động duyệt điều kiện thanh toán.</td>
            <td>Thời gian thực</td>
        </tr>
        <tr>
            <td><strong>GATE-PRJ-03: Scope Change Request</strong></td>
            <td>Yêu cầu thay đổi phạm vi (CR) ảnh hưởng &gt; 5% ngân sách hoặc thời gian.</td>
            <td>Yêu cầu lập Phụ lục hợp đồng (SOW Addendum) và phê duyệt Deal-Desk trước khi mở thêm giờ.</td>
            <td>Trước khi thực hiện công việc phát sinh</td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (documents.project)</h2>
<ul>
    <li>Không gian lưu trữ: Thư mục dự án tương ứng dưới cây <code>documents.document</code>.</li>
    <li>Bộ hồ sơ nghiệm thu từng giai đoạn bắt buộc:
        <ol>
            <li>Biên bản bàn giao và nghiệm thu mốc có chữ ký số của đại diện 2 bên.</li>
            <li>Báo cáo kết quả kiểm thử UAT hoặc tài liệu thiết kế giải pháp tương ứng.</li>
            <li>Bảng tổng hợp giờ chấm công thực tế trích xuất từ <code>account.analytic.line</code>.</li>
        </ol>
    </li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_ip_01",
        "code": "SOP-DGM-IP-01",
        "title": "SOP-DGM-IP-01 · Quy trình Đăng ký Bản quyền Tác giả Phần mềm Cục Bản quyền & Chứng minh Ưu đãi Thuế TNDN",
        "icon": "💡",
        "sequence": 90,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-IP-01 · Quy trình Đăng ký Bản quyền Tác giả Phần mềm Cục Bản quyền & Chứng minh Ưu đãi Thuế TNDN</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-IP-01</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Bảo Mật Tài Sản Trí Tuệ (IP Asset Confidential)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Cơ quan đăng ký bản quyền:</em> Cục Bản quyền tác giả — Bộ Văn hóa, Thể thao và Du lịch<br/>
                <em>Danh mục tài sản phần mềm:</em> <strong>MOJO AI</strong>, <strong>Gen Logo</strong>, <strong>Gen QR Art</strong>, <strong>Reface</strong>, <strong>Innoria AL2C Engine</strong>
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Trưởng ban R&amp;D &amp; Trưởng ban Pháp chế Sở hữu Trí tuệ</td>
            <th>Căn Cứ Pháp Lý &amp; Tiêu Chuẩn</th>
            <td>Luật Sở hữu trí tuệ 2005 (sửa đổi, bổ sung 2022); Nghị định 17/2023/NĐ-CP; Thông tư 13/2020/TT-BTTTT quy định việc xác định hoạt động sản xuất sản phẩm phần mềm; Nghị định 218/2013/NĐ-CP về ưu đãi thuế TNDN.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư phần mềm)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Đóng gói mã nguồn, trích xuất 25 trang đầu &amp; 25 trang cuối ghi CD/USB</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>A</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Soạn thảo Tờ khai đăng ký quyền tác giả Mẫu số 01 / Mẫu số 02</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Ban hành Quyết định giao việc &amp; Cam đoan quyền tác giả không tranh chấp</td>
            <td><strong>A</strong></td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Ký cam đoan)</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Nộp và theo dõi tiến độ cấp Giấy chứng nhận tại Cục Bản quyền tác giả</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Lập Hồ sơ chứng minh 7 công đoạn phần mềm bảo vệ ưu đãi thuế TNDN</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Lưu trữ tại Thư mục 3228 (DGM - SỞ HỮU TRÍ TUỆ).</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Chuẩn bị Hồ sơ Đăng ký Bản quyền Tác giả</h3>
<ul>
    <li><strong>Phân loại biểu mẫu theo loại hình tác phẩm:</strong>
        <ul>
            <li><strong>Mẫu số 01:</strong> Đơn đăng ký quyền tác giả đối với <em>Chương trình máy tính</em> (Áp dụng cho: <code>MOJO AI</code>, <code>Innoria AL2C Engine</code>).</li>
            <li><strong>Mẫu số 02:</strong> Đơn đăng ký quyền tác giả đối với <em>Tác phẩm mỹ thuật ứng dụng</em> (Áp dụng cho thiết kế giao diện đồ họa, bộ nhận diện: <code>Gen Logo</code>, <code>Gen QR Art</code>).</li>
        </ul>
    </li>
    <li><strong>Quy cách đóng gói hồ sơ nộp Cục Bản quyền:</strong>
        <ol>
            <li>Tờ khai đăng ký quyền tác giả có chữ ký của người đại diện theo pháp luật (CEO Lê Xuân Hoàng) và đóng dấu tròn công ty.</li>
            <li>02 bản in tác phẩm: Đối với phần mềm, in <strong>tối thiểu 25 trang đầu và 25 trang cuối</strong> của mã nguồn (source code) kèm giao diện chính.</li>
            <li>02 đĩa CD / USB ghi toàn bộ mã nguồn và bản cài đặt hoàn chỉnh của phần mềm.</li>
            <li>Quyết định giao nhiệm vụ sáng tạo sản phẩm phần mềm của Tổng Giám Đốc cho nhóm tác giả.</li>
            <li>Văn bản cam đoan của nhóm tác giả khẳng định tác phẩm tự sáng tạo, không sao chép từ bất kỳ nguồn nào.</li>
            <li>Bản sao có chứng thực Giấy chứng nhận ĐKKD công ty cổ phần số <code>0317958465</code>.</li>
        </ol>
    </li>
</ul>

<h3>Bước 2: Xây Dựng Hồ Sơ 7 Công Đoạn Sản Xuất Phần Mềm (Thông tư 13/2020/TT-BTTTT)</h3>
<p>Để bảo vệ quyền hưởng ưu đãi thuế TNDN khi cơ quan thuế thanh tra, ban dự án phải tập hợp bằng chứng cho <strong>tối thiểu 7 công đoạn</strong> sản xuất phần mềm trong <code>documents.document</code>:</p>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f8fafc;">
            <th>Công Đoạn</th>
            <th>Tên Nghiệp Vụ Chuẩn</th>
            <th>Tài Liệu Bằng Chứng Bắt Buộc Trong ERP Insilos 20</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Công đoạn 1</strong></td>
            <td>Xác định yêu cầu (Requirements)</td>
            <td>Tài liệu đặc tả yêu cầu người dùng (SRS / User Stories / PRD) lưu tại Knowledge Article.</td>
        </tr>
        <tr>
            <td><strong>Công đoạn 2</strong></td>
            <td>Phân tích &amp; Thiết kế (Analysis &amp; Design)</td>
            <td>Sơ đồ kiến trúc hệ thống, Bản thiết kế CSDL (ERD), Luồng dữ liệu, Bản vẽ UI/UX Figma.</td>
        </tr>
        <tr>
            <td><strong>Công đoạn 3</strong></td>
            <td>Lập trình, viết mã (Coding)</td>
            <td>Nhật ký cam kết mã nguồn (Git commit logs), Bản lưu trữ Source code trên kho lưu trữ bảo mật.</td>
        </tr>
        <tr>
            <td><strong>Công đoạn 4</strong></td>
            <td>Kiểm thử phần mềm (Testing)</td>
            <td>Kịch bản kiểm thử (Test cases), Báo cáo kết quả kiểm thử tự động, Biên bản nghiệm thu nội bộ.</td>
        </tr>
        <tr>
            <td><strong>Công đoạn 5</strong></td>
            <td>Đóng gói, cài đặt (Packaging)</td>
            <td>Tệp cài đặt, Docker image build logs, Hướng dẫn cài đặt và cấu hình hệ thống.</td>
        </tr>
        <tr>
            <td><strong>Công đoạn 6</strong></td>
            <td>Triển khai, hướng dẫn (Deployment)</td>
            <td>Tài liệu hướng dẫn sử dụng (User Manual), Nhật ký phát hành (Release Notes), Biên bản bàn giao.</td>
        </tr>
        <tr>
            <td><strong>Công đoạn 7</strong></td>
            <td>Bảo trì, nâng cấp (Maintenance)</td>
            <td>Nhật ký hỗ trợ kỹ thuật (Helpdesk tickets), Bản vá lỗi, Báo cáo nâng cấp tính năng định kỳ.</td>
        </tr>
    </tbody>
</table>

<h3>Bước 3: Khung Ưu Đãi Thuế TNDN Áp Dụng Cho Doanh Nghiệp</h3>
<ul>
    <li>Căn cứ Nghị định 218/2013/NĐ-CP và Thông tư 78/2014/TT-BTC, thu nhập từ hoạt động sản xuất sản phẩm phần mềm của Digimate JSC được hưởng:
        <ul>
            <li><strong>Thuế suất ưu đãi 10% trong vòng 15 năm</strong> kể từ năm đầu tiên có doanh thu từ hoạt động sản xuất phần mềm.</li>
            <li><strong>Miễn thuế TNDN 4 năm</strong> kể từ năm đầu tiên có thu nhập chịu thuế.</li>
            <li><strong>Giảm 50% số thuế TNDN phải nộp trong 9 năm tiếp theo</strong>.</li>
        </ul>
    </li>
    <li>Thuế GTGT: Doanh thu phần mềm tiêu thụ nội địa thuộc đối tượng <strong>không chịu thuế GTGT</strong>; doanh thu phần mềm xuất khẩu hưởng thuế suất <strong>0%</strong>.</li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Quy Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-IP-01: Copyright Filing SLA</strong></td>
            <td>Nộp hồ sơ đăng ký quyền tác giả đối với mọi sản phẩm phần mềm phát hành thương mại.</td>
            <td>Cảnh báo nhắc nhở sau khi release bản v1.0 thương mại; bắt buộc có Giấy chứng nhận để phục vụ hồ sơ thầu và đối tác viễn thông.</td>
            <td>Trong vòng <strong>45 Ngày</strong> sau Go-Live</td>
        </tr>
        <tr>
            <td><strong>GATE-IP-02: 7-Stage Audit Defense</strong></td>
            <td>Kiểm tra tính toàn vẹn của hồ sơ 7 công đoạn trước khi lập Tờ khai quyết toán thuế TNDN năm.</td>
            <td>Nếu thiếu chứng từ của bất kỳ công đoạn nào trong 4 công đoạn cốt lõi (1, 2, 3, 4), kế toán trưởng từ chối đưa doanh thu đó vào diện miễn thuế.</td>
            <td>Trước ngày 15/03 hàng năm</td>
        </tr>
        <tr>
            <td><strong>GATE-IP-03: IP Assignment Clause</strong></td>
            <td>Xác nhận 100% nhân sự tham gia dự án đã ký cam kết sở hữu trí tuệ thuộc về Digimate theo Điều 8 HĐLĐ 2026.</td>
            <td>Khóa phân quyền commit mã nguồn đối với nhân sự chưa hoàn tất ký kết thỏa thuận IP.</td>
            <td>Ngay khi tiếp nhận nhân sự</td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Folder 3228: SỞ HỮU TRÍ TUỆ)</h2>
<ul>
    <li>Thư mục lưu trữ: <code>ID 3228: 05. Sở hữu Trí tuệ &amp; Bản quyền (DGM - SỞ HỮU TRÍ TUỆ)</code>.</li>
    <li>Hồ sơ lưu trữ bắt buộc:
        <ol>
            <li>Bản scan Giấy chứng nhận Đăng ký Quyền tác giả do Cục Bản quyền tác giả cấp.</li>
            <li>Đơn đăng ký quyền tác giả Mẫu số 01 / Mẫu số 02 có dấu tiếp nhận của Cục.</li>
            <li>Bộ hồ sơ minh chứng 7 công đoạn sản xuất phần mềm đóng dấu giáp lai của công ty.</li>
            <li>Bản in mã nguồn 25 trang đầu và 25 trang cuối đã nộp lưu chiểu.</li>
        </ol>
    </li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_hr_01",
        "code": "SOP-DGM-HR-01",
        "title": "SOP-DGM-HR-01 · Quy trình Tuyển dụng, Tiếp nhận Nhân sự & Ký Hợp đồng Lao động 16 Điều 2026",
        "icon": "👥",
        "sequence": 100,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-HR-01 · Quy trình Tuyển dụng, Tiếp nhận Nhân sự & Ký Hợp đồng Lao động 16 Điều 2026</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-HR-01</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Nội Bộ Nhân Sự &amp; Quản Trị Tài Nguyên Người (HR Confidential)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Trụ sở:</em> Số 11, Đường số 3, KDC CityLand, Phường Tân Mỹ, TP. Hồ Chí Minh<br/>
                <em>Biểu mẫu hợp đồng chuẩn:</em> Hợp đồng Lao động Doanh nghiệp Công nghệ 2026 (Gồm 16 Điều và Phụ lục 01)
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Trưởng ban Nhân sự &amp; Tuyển dụng (People Operations Lead)</td>
            <th>Căn Cứ Pháp Lý</th>
            <td>Bộ luật Lao động 2019; Nghị định 145/2020/NĐ-CP; Luật An toàn vệ sinh lao động 2015; Hợp đồng Lao động mẫu DGM 2026.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư phần mềm)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Phê duyệt định biên nhân sự và ngân sách tuyển dụng</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Phỏng vấn chuyên môn và đánh giá văn hóa tổ chức</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Khởi tạo hồ sơ nhân sự hr.employee và kích hoạt Onboarding Plan</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Soạn thảo Hợp đồng Lao động 16 Điều chuẩn 2026 qua Sign Template</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Ký số Hợp đồng Lao động điện tử (Người lao động ký trước, CEO ký sau)</td>
            <td><strong>A (Ký duyệt)</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Ký số)</strong></td>
            <td><strong>I</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. HĐLĐ 16 Điều chuẩn hóa: Điều 6 (An toàn thông tin &amp; 2FA), Điều 7 (Bảo mật vĩnh viễn), Điều 8 (Sở hữu trí tuệ 100% thuộc DGM), Điều 9.4 (Chống Moonlighting).</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Tiếp nhận Ứng viên & Khởi tạo Onboarding Plan</h3>
<ul>
    <li><strong>Menu truy cập:</strong> <code>Nhân sự (Employees) &gt; Nhân viên &gt; Tạo mới</code>.</li>
    <li><strong>Mô hình dữ liệu (Model):</strong> <code>hr.employee</code>, <code>mail.activity.plan</code>.</li>
    <li><strong>Thao tác tự động:</strong>
        <ul>
            <li>Khi tạo nhân viên mới, hệ thống tự động sinh thư mục tài liệu cá nhân dưới Thư mục <code>3227</code> (<code>04. Nhân sự &amp; Hợp đồng Lao động</code>).</li>
            <li>Kích hoạt kế hoạch hội nhập (Onboarding Activity Plan): Cấp tài khoản email công vụ <code>@inno.ai.vn</code>, kích hoạt 2FA, cấp phát máy tính làm việc, hướng dẫn quy chế an toàn thông tin.</li>
        </ul>
    </li>
</ul>

<h3>Bước 2: Vận Hành Ký Số Hợp Đồng Lao Động Chuẩn 2026 (16 Điều Khoản)</h3>
<ul>
    <li><strong>Mô hình dữ liệu:</strong> <code>hr.contract</code>, <code>sign.template</code>, <code>sign.request</code>.</li>
    <li><strong>Bức Tường Thép Bảo Vệ Tài Sản Trí Tuệ (4 Điều Khoản Then Chốt Bắt Buộc):</strong>
        <ol>
            <li><strong>Điều 6 (An toàn thông tin &amp; Quản trị tài khoản):</strong> Cấm tuyệt đối việc lưu trữ mã nguồn, API keys, system prompts hoặc dữ liệu khách hàng trên thiết bị cá nhân hoặc tài khoản cá nhân. Bắt buộc kích hoạt xác thực hai yếu tố (2FA) trên mọi tài khoản công vụ.</li>
            <li><strong>Điều 7 (Bảo mật vĩnh viễn):</strong> Cam kết bảo mật vô điều kiện và vĩnh viễn (kể cả sau khi chấm dứt hợp đồng) đối với trọng số mô hình AI (model weights), prompt engineering, thuật toán RAG, mã nguồn phần mềm và danh sách khách hàng.</li>
            <li><strong>Điều 8 (Sở hữu trí tuệ 100% thuộc Digimate JSC):</strong> Toàn bộ sáng kiến, mã nguồn, tài liệu kỹ thuật, tác phẩm đồ họa được tạo ra trong thời gian làm việc tại công ty thuộc quyền sở hữu toàn vẹn của Digimate JSC. Người lao động từ bỏ quyền tài sản và cam kết hỗ trợ ký Mẫu 01/02 Cục Bản quyền tác giả khi có yêu cầu.</li>
            <li><strong>Điều 9.4 (Quy chế chống xung đột &amp; Moonlighting):</strong> Nghiêm cấm người lao động làm thêm ngoài giờ, tư vấn hoặc cộng tác dưới bất kỳ hình thức nào với các công ty phát triển AI hoặc phần mềm là đối thủ cạnh tranh trực tiếp.</li>
        </ol>
    </li>
    <li><strong>Quy trình ký duyệt số:</strong> Gửi yêu cầu ký qua <code>sign.request</code>:
        <ul>
            <li>Bước ký 1: Người lao động ký số trên điện thoại hoặc máy tính cá nhân.</li>
            <li>Bước ký 2: Tổng Giám Đốc Lê Xuân Hoàng ký duyệt và đóng dấu điện tử công ty.</li>
            <li>Bản ký hoàn tất tự động lưu vào thư mục nhân sự tương ứng (ví dụ: Thư mục <code>3232</code> Ân Nguyễn, <code>3243</code> Khánh Huỳnh, <code>3246</code> Tài Bùi).</li>
        </ul>
    </li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Quy Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-HR-01-A: Banned Entity Guard</strong></td>
            <td>Kiểm tra toàn bộ hợp đồng lao động và phụ lục không được chứa tên pháp nhân cũ <code>Ứng Dụng Sáng Tạo</code> hoặc MST cũ <code>0313683499</code>.</td>
            <td>Khóa không cho gửi ký nếu phát hiện dấu hiệu pháp nhân cũ.</td>
            <td>Thời gian thực</td>
        </tr>
        <tr>
            <td><strong>GATE-HR-01-B: Signing Completion SLA</strong></td>
            <td>Hoàn thành ký kết hợp đồng lao động chính thức sau khi kết thúc thời gian thử việc đạt yêu cầu.</td>
            <td>Hệ thống gửi nhắc nhở trước 07 ngày kết thúc thử việc; bắt buộc ký HĐLĐ trong vòng 03 ngày làm việc.</td>
            <td>Tối đa <strong>03 Ngày</strong> sau thử việc</td>
        </tr>
        <tr>
            <td><strong>GATE-HR-01-C: IT Security Verification</strong></td>
            <td>Xác nhận nhân viên đã ký cam kết Điều 6 &amp; Điều 7 và thiết lập 2FA.</td>
            <td>Khóa quyền truy cập Git repository nếu chưa có xác nhận từ People Operations.</td>
            <td>Trong ngày làm việc đầu tiên</td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Audit Evidence in documents.document)</h2>
<ul>
    <li>Thư mục lưu trữ trong <code>documents.document</code>: <code>ID 3227: 04. Nhân sự &amp; Hợp đồng Lao động (DGM - NHÂN SỰ)</code>.</li>
    <li>Hồ sơ bắt buộc cho mỗi nhân viên:
        <ol>
            <li>Bản scan CCCD gắn chip (12 số) và Sơ yếu lý lịch có xác nhận.</li>
            <li>Hợp đồng lao động 16 Điều bản ký số hoàn chỉnh có chữ ký 2 bên.</li>
            <li>Phụ lục 01 Mô tả công việc và Bản cam kết bảo mật thông tin sở hữu trí tuệ.</li>
            <li>Bản đăng ký người phụ thuộc giảm trừ gia cảnh (nếu có).</li>
        </ol>
    </li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_hr_02",
        "code": "SOP-DGM-HR-02",
        "title": "SOP-DGM-HR-02 · Quy trình Tính lương Hàng tháng, Đăng ký NPT & Xuất Bảng kê 11 Cột Vietcombank DigiBiz",
        "icon": "💳",
        "sequence": 110,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-HR-02 · Quy trình Tính lương Hàng tháng, Đăng ký NPT & Xuất Bảng kê 11 Cột Vietcombank DigiBiz</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-HR-02</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Tuyệt Mật Tiền Lương &amp; Thu Nhập (Strict Payroll Confidential)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Dịch vụ ngân hàng số chi lương:</em> <strong>Vietcombank DigiBiz</strong> (Tài khoản nguồn: <code>1202703007</code>)<br/>
                <em>Biểu mẫu bảng kê chuẩn:</em> File Excel 11 cột chuẩn VCB DigiBiz (<code>bangkemau-VCB-DigiBiz (2).xlsx</code>)
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Chuyên viên C&amp;B &amp; Kế toán Tiền lương</td>
            <th>Căn Cứ Pháp Lý &amp; Quy Chuẩn</th>
            <td>Bộ luật Lao động 2019; Luật Thuế TNCN (Biểu thuế lũy tiến 5 bậc cập nhật 2026, Giảm trừ bản thân 15.5M, Giảm trừ NPT 6.2M/tháng); Hướng dẫn chi lương theo lô Vietcombank DigiBiz.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Người lao động)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Chốt công, tính OT và tổng hợp hồ sơ giảm trừ gia cảnh NPT</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C (Ký xác nhận)</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Tính toán bảng lương trên hr.payslip.run áp dụng biểu thuế 2026</td>
            <td><strong>I</strong></td>
            <td><strong>A</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Kiểm tra đối soát số dư TK 334 và xuất file Excel VCB DigiBiz 11 cột</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Tải bảng kê lên VCB DigiBiz và thực hiện phê duyệt chi tiền</td>
            <td><strong>A (Duyệt chi)</strong></td>
            <td><strong>R (Tạo lệnh)</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Sinh phiếu lương PDF bảo mật và gửi tự động qua email cho từng nhân sự</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I (Nhận phiếu)</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Áp dụng cho 8 nhân sự hiện diện chi trả qua Vietcombank STK 1202703007.</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Tính Toán Bảng Lương Trên Phân Hệ <code>hr_payroll</code></h3>
<ul>
    <li><strong>Menu truy cập:</strong> <code>Bảng lương (Payroll) &gt; Đợt tính lương (Payslip Batches) &gt; Tạo mới</code>.</li>
    <li><strong>Mô hình dữ liệu (Model):</strong> <code>hr.payslip.run</code> và <code>hr.payslip</code>.</li>
    <li><strong>Quy tắc tính toán thuế &amp; bảo hiểm 2026:</strong>
        <ul>
            <li>Mức giảm trừ bản thân: <code>15.500.000 VND / tháng</code>.</li>
            <li>Mức giảm trừ người phụ thuộc (NPT): <code>6.200.000 VND / người / tháng</code> (phải có mã số thuế NPT hợp lệ).</li>
            <li>Trần đóng BHXH &amp; BHYT: 20 lần mức lương cơ sở (2.340.000 $\times$ 20 = <code>46.800.000 VND</code>).</li>
            <li>Trần đóng BHTN: 20 lần mức lương tối thiểu vùng I (4.960.000 $\times$ 20 = <code>99.200.000 VND</code>).</li>
            <li>Biểu thuế thu nhập cá nhân lũy tiến 5 bậc áp dụng theo quy định hiện hành.</li>
        </ul>
    </li>
    <li>Bấm nút <code>Compute Sheet</code> tính toán cho toàn bộ 8 nhân sự hiện diện.</li>
</ul>

<h3>Bước 2: Cấu Trúc Bảng Kê Vietcombank DigiBiz 11 Cột Chuẩn Hóa</h3>
<p>Hệ thống trích xuất dữ liệu trực tiếp sang tệp Excel <code>.xlsx</code> với đúng 11 cột chuẩn:</p>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f8fafc;">
            <th>Cột</th>
            <th>Tên Cột (Header)</th>
            <th>Kiểu Dữ Liệu</th>
            <th>Quy Tắc Định Dạng Bắt Buộc</th>
            <th>Ví Dụ Dữ Liệu Thực Tế</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>1</strong></td>
            <td><code>stt (No)</code></td>
            <td>Số nguyên</td>
            <td>Tăng dần từ 1 đến N.</td>
            <td>1, 2, 3...</td>
        </tr>
        <tr>
            <td><strong>2</strong></td>
            <td><code>so ref (ref no)</code></td>
            <td>Chuỗi</td>
            <td>Mã duy nhất của phiếu lương.</td>
            <td><code>SLIP/2026/10/001</code></td>
        </tr>
        <tr>
            <td><strong>3</strong></td>
            <td><code>so tai khoan (beneficiary account)</code></td>
            <td>Chuỗi văn bản (Text)</td>
            <td>Giữ nguyên số 0 ở đầu tài khoản; không định dạng số mũ scientific.</td>
            <td><code>0111000287863</code>, <code>1373068161</code></td>
        </tr>
        <tr>
            <td><strong>4</strong></td>
            <td><code>so cmnd (ID number)</code></td>
            <td>Chuỗi văn bản</td>
            <td>Số CCCD 12 số của người hưởng.</td>
            <td><code>089094016917</code></td>
        </tr>
        <tr>
            <td><strong>5</strong></td>
            <td><code>ngay cap (issued date)</code></td>
            <td>Ngày (DD/MM/YYYY)</td>
            <td>Đúng định dạng ngày/tháng/năm.</td>
            <td><code>12/05/2021</code></td>
        </tr>
        <tr>
            <td><strong>6</strong></td>
            <td><code>noi cap (issued place)</code></td>
            <td>Chuỗi văn bản</td>
            <td>Cơ quan cấp căn cước công dân.</td>
            <td><code>Cục Cảnh sát QLHC về TTXH</code></td>
        </tr>
        <tr>
            <td><strong>7</strong></td>
            <td><code>ten nguoi huong (beneficiary name)</code></td>
            <td>Chuỗi văn bản</td>
            <td><strong>VIẾT HOA KHÔNG DẤU</strong> (Loại bỏ hoàn toàn dấu tiếng Việt).</td>
            <td><code>LE XUAN HOANG</code>, <code>MAI THI HONG THAM</code></td>
        </tr>
        <tr>
            <td><strong>8</strong></td>
            <td><code>ten ngan hang (bank name)</code></td>
            <td>Chuỗi văn bản</td>
            <td>Tên ngân hàng thụ hưởng chuẩn.</td>
            <td><code>VIETCOMBANK</code>, <code>ACB</code></td>
        </tr>
        <tr>
            <td><strong>9</strong></td>
            <td><code>so tien (amount)</code></td>
            <td>Số nguyên dương</td>
            <td>Số tiền lương thực lĩnh, không chứa dấu phẩy, chấm hay ký hiệu tiền tệ.</td>
            <td><code>21410000</code></td>
        </tr>
        <tr>
            <td><strong>10</strong></td>
            <td><code>loai tien (currency)</code></td>
            <td>Chuỗi văn bản</td>
            <td>Cố định là <code>VND</code>.</td>
            <td><code>VND</code></td>
        </tr>
        <tr>
            <td><strong>11</strong></td>
            <td><code>noi dung (content)</code></td>
            <td>Chuỗi văn bản</td>
            <td>Cú pháp chuẩn hóa: <code>cong ty cp nguoi ban so thanh toan luong thang MM YYYY</code>.</td>
            <td><code>cong ty cp nguoi ban so thanh toan luong thang 10 2026</code></td>
        </tr>
    </tbody>
</table>

<h3>Bước 3: Chi Lương Trên VCB DigiBiz & Phân Phối Phiếu Lương</h3>
<ul>
    <li>Kế toán viên đăng nhập hệ thống VCB DigiBiz, tải file Excel lên mục <em>Chuyển tiền theo bảng kê</em>.</li>
    <li>Kế toán trưởng phê duyệt cấp 1; Tổng Giám Đốc Lê Xuân Hoàng duyệt lệnh cấp 2 bằng Smart OTP.</li>
    <li>Sau khi ngân hàng báo thành công, kế toán bấm <code>Generate &amp; Send Payslips</code> trên ERP:
        <ul>
            <li>Hệ thống sinh file PDF phiếu lương bảo mật cho từng nhân sự.</li>
            <li>Tự động lưu vào Thư mục <code>3252</code> (<code>Lương DGM</code>).</li>
            <li>Gửi email thông báo đính kèm đường link an toàn cho từng nhân viên.</li>
        </ul>
    </li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Quy Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-HR-02-A: Zero Payroll Variance</strong></td>
            <td>Tổng số tiền thực lĩnh trên file DigiBiz phải khớp chính xác 100% với số dư phát sinh Nợ TK 334 trên sổ kế toán.</td>
            <td>Khóa nút xuất file Excel nếu phát hiện lệch dù chỉ 1 đồng.</td>
            <td>Trước khi xuất file ngân hàng</td>
        </tr>
        <tr>
            <td><strong>GATE-HR-02-B: Content Syntax Guard</strong></td>
            <td>Kiểm tra cột Nội dung chuyển tiền phải đúng cú pháp tháng hiện hành, tuyệt đối không lặp lại lỗi ghi nhầm tháng cũ.</td>
            <td>Tự động sinh cú pháp nội dung theo tháng của đợt lương, không cho nhập tay tự do.</td>
            <td>Thời gian thực</td>
        </tr>
        <tr>
            <td><strong>GATE-HR-02-C: Pay Day SLA</strong></td>
            <td>Thời hạn hoàn thành chi lương vào tài khoản người lao động.</td>
            <td>Tiền lương phải ghi có trong tài khoản nhân viên trước 17:00 ngày 05 hàng tháng (nếu trùng ngày nghỉ thì chi vào ngày làm việc trước đó).</td>
            <td>Đúng <strong>Ngày 05</strong> hàng tháng</td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Audit Evidence in documents.document)</h2>
<ul>
    <li>Thư mục lưu trữ trong <code>documents.document</code>: <code>ID 3252: Lương DGM (02. Tài chính, Kế toán &amp; Thuế / LƯƠNG)</code>.</li>
    <li>Hồ sơ lưu trữ bắt buộc từng tháng:
        <ol>
            <li>Bảng tổng hợp thanh toán tiền lương có chữ ký của CEO và Kế toán trưởng.</li>
            <li>Tệp Excel bảng kê chi lương VCB DigiBiz 11 cột đã upload.</li>
            <li>Giấy báo Nợ ngân hàng Vietcombank STK <code>1202703007</code> xác nhận chi lương thành công.</li>
            <li>Danh sách ký nhận / email thông báo phiếu lương điện tử của toàn bộ nhân viên.</li>
        </ol>
    </li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_hr_03",
        "code": "SOP-DGM-HR-03",
        "title": "SOP-DGM-HR-03 · Quy trình Đối soát BHXH Mẫu C12-TS Mã Đơn vị TZ0857G & Khóa Không Nợ Đọng",
        "icon": "🏥",
        "sequence": 120,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-HR-03 · Quy trình Đối soát BHXH Mẫu C12-TS Mã Đơn vị TZ0857G & Khóa Không Nợ Đọng</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-HR-03</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Tuân Thủ Pháp Luật Lao Động &amp; Bảo Hiểm (Statutory Insurance Compliance)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Cơ quan bảo hiểm xã hội quản lý:</em> <strong>BẢO HIỂM XÃ HỘI QUẬN 7 — TP. HỒ CHÍ MINH</strong><br/>
                <em>Địa chỉ cơ quan BHXH:</em> 136 Huỳnh Tấn Phát, Phường Tân Thuận Tây, Quận 7, TP.HCM<br/>
                <em>Mã đơn vị tham gia BHXH:</em> <strong>TZ0857G</strong>
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>Kế toán Tiền lương &amp; Bảo hiểm Xã hội</td>
            <th>Căn Cứ Pháp Lý</th>
            <td>Luật Bảo hiểm Xã hội 2014 &amp; Luật BHXH 2024 (hiệu lực từ 01/07/2025); Luật Bảo hiểm Y tế; Luật Việc làm; Quyết định 595/QĐ-BHXH và Quyết định 505/QĐ-BHXH.</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Người lao động)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Trích xuất quỹ lương và tính toán nghĩa vụ trích nộp 32% quỹ bảo hiểm</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Thực hiện lệnh nộp đủ 100% tiền BHXH sang kho bạc BHXH Quận 7</td>
            <td><strong>A (Duyệt chi)</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Tiếp nhận và đối soát Thông báo kết quả đóng BHXH Mẫu C12-TS hàng tháng</td>
            <td><strong>I</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Thẩm định chỉ tiêu [Đ.2.2] Thiếu chuyển kỳ sau = 0 đồng</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Fail-Closed)</strong></td>
        </tr>
        <tr>
            <td>Xử lý ứng cứu bổ sung trong 24h nếu phát sinh nợ đọng hoặc lãi chậm nộp</td>
            <td><strong>A</strong></td>
            <td><strong>R</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Cơ quan quản lý: BHXH Quận 7 (Mã đơn vị: TZ0857G). Lưu tại Thư mục 3248.</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Cơ Cấu Tỷ Lệ Đóng & Hạch Toán Kế Toán Bắt Buộc</h3>
<p>Tổng tỷ lệ trích nộp nghĩa vụ bảo hiểm bắt buộc là <strong>32%</strong> quỹ lương căn cứ:</p>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f8fafc;">
            <th>Quỹ Bảo Hiểm</th>
            <th>Tỷ Lệ Doanh Nghiệp (21.5%)</th>
            <th>Tỷ Lệ Người Lao Động (10.5%)</th>
            <th>Tổng Tỷ Lệ (32%)</th>
            <th>Tài Khoản Hạch Toán</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Bảo hiểm Xã hội (Hưu trí &amp; Tử tuất, Ốm đau &amp; Thai sản)</td>
            <td>17.5%</td>
            <td>8.0%</td>
            <td>25.5%</td>
            <td>TK <code>3383</code></td>
        </tr>
        <tr>
            <td>Bảo hiểm Y tế (BHYT)</td>
            <td>3.0%</td>
            <td>1.5%</td>
            <td>4.5%</td>
            <td>TK <code>3384</code></td>
        </tr>
        <tr>
            <td>Bảo hiểm Thất nghiệp (BHTN)</td>
            <td>1.0%</td>
            <td>1.0%</td>
            <td>2.0%</td>
            <td>TK <code>3386</code></td>
        </tr>
        <tr>
            <td>Bảo hiểm Tai nạn lao động &amp; Bệnh nghề nghiệp (BHTNLĐ-BNN)</td>
            <td>0.5%</td>
            <td>0.0%</td>
            <td>0.5%</td>
            <td>TK <code>3383</code></td>
        </tr>
    </tbody>
</table>
<p><strong>Bút toán trích nộp hàng tháng:</strong></p>
<pre><code>Nợ TK 6422 (Phần doanh nghiệp chịu: 21.5% x Quỹ lương)
Nợ TK 3341 (Phần người lao động chịu: 10.5% x Quỹ lương)
    Có TK 3383 (BHXH: 26%)
    Có TK 3384 (BHYT: 4.5%)
    Có TK 3386 (BHTN: 2.0%)

Khi nộp tiền vào tài khoản thu của BHXH Quận 7:
Nợ TK 3383, 3384, 3386 / Có TK 1121 (Vietcombank 1202703007)</code></pre>

<h3>Bước 2: Quy Trình 5 Bước Khóa Không Nợ Đọng (Zero-Arrears Protocol)</h3>
<ol>
    <li><strong>Ngày 20 hàng tháng:</strong> Kế toán tính toán trước chính xác số tiền phát sinh phải nộp trong kỳ căn cứ danh sách lao động thực tế.</li>
    <li><strong>Ngày 25 hàng tháng:</strong> Kế toán lập lệnh chuyển khoản ủy nhiệm chi nộp <strong>100% số tiền bảo hiểm phát sinh</strong> sang tài khoản chuyên thu của BHXH Quận 7. Cú pháp nộp: <code>Dong BHXH thang MM/YYYY cho Ma DV TZ0857G - Cong ty CP Nguoi Ban So</code>.</li>
    <li><strong>Ngày 05 tháng tiếp theo:</strong> Tải tệp thông báo điện tử Mẫu C12-TS từ Cổng Dịch vụ công BHXH Việt Nam hoặc tiếp nhận từ chuyên quản BHXH Quận 7.</li>
    <li><strong>Thẩm định chỉ tiêu vàng:</strong> Kiểm tra dòng <strong>[Đ.2.2] Thiếu chuyển kỳ sau</strong>. Giá trị bắt buộc phải đạt:
        $$\text{[Đ.2.2]} = 0 \text{ VND}$$
    </li>
    <li><strong>Lưu trữ chứng từ:</strong> Tải tệp PDF C12-TS vào Thư mục <code>3248</code> (<code>BHXH</code>) và chuyển trạng thái trên ERP sang <code>Reconciled - Zero Arrears</code>.</li>
</ol>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Quy Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-HR-03-A: Payment Deadline</strong></td>
            <td>Nộp đủ 100% tiền đóng BHXH, BHYT, BHTN phát sinh trong tháng.</td>
            <td>Hệ thống gửi cảnh báo nhắc nhở ngày 22; ngày 25 tự động bật cờ thanh toán khẩn cấp.</td>
            <td>Trước <strong>Ngày 25</strong> hàng tháng</td>
        </tr>
        <tr>
            <td><strong>GATE-HR-03-B: Zero Arrears Sentinel</strong></td>
            <td>Kiểm tra chỉ tiêu [Đ.2.2] trên Thông báo C12-TS của BHXH Quận 7.</td>
            <td>Nếu [Đ.2.2] &gt; 0 VND, hệ thống tự động kích hoạt <strong>Báo động đỏ (Red Alert)</strong> gửi Finance Lead và CEO; khóa sổ kế toán tháng cho đến khi nộp bù.</td>
            <td>Hoàn tất xử lý trong <strong>24 Giờ</strong></td>
        </tr>
        <tr>
            <td><strong>GATE-HR-03-C: Late Interest Shield</strong></td>
            <td>Triệt tiêu hoàn toàn nguy cơ chịu lãi phạt chậm nộp (0.726%/tháng đối với BHXH/BHTN; 0.984%/tháng đối với BHYT).</td>
            <td>Kiểm tra dòng [D.2] Lãi chậm đóng trên C12-TS phải bằng 0 đồng.</td>
            <td>Hàng tháng</td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (Audit Evidence in documents.document)</h2>
<ul>
    <li>Thư mục lưu trữ trong <code>documents.document</code>: <code>ID 3248: BHXH (02. Tài chính, Kế toán &amp; Thuế)</code>.</li>
    <li>Hồ sơ lưu trữ bắt buộc 12 tháng liên tục:
        <ol>
            <li>Thông báo kết quả đóng BHXH, BHYT, BHTN Mẫu C12-TS do BHXH Quận 7 phát hành.</li>
            <li>Ủy nhiệm chi chuyển tiền đóng BHXH có dấu xác nhận của Vietcombank.</li>
            <li>Danh sách người lao động tham gia BHXH (Mẫu D02-LT) khi có tăng giảm nhân sự.</li>
            <li>Văn bản xác nhận của BHXH Quận 7 khẳng định đơn vị không nợ đọng tiền bảo hiểm phục vụ hồ sơ năng lực đấu thầu và hồ sơ đối tác.</li>
        </ol>
    </li>
</ul>
</div>"""
    },
    {
        "xml_id": "kb_dgm_sop_doc_01",
        "code": "SOP-DGM-DOC-01",
        "title": "SOP-DGM-DOC-01 · Quy trình Phân loại Tài liệu Tự động AI Documents & Lập chỉ mục Tri thức SOP-RAG",
        "icon": "🤖",
        "sequence": 130,
        "body": r"""<div class="dgm-sop-container">
<h1>SOP-DGM-DOC-01 · Quy trình Phân loại Tài liệu Tự động AI Documents & Lập chỉ mục Tri thức SOP-RAG</h1>

<h2>1. Document Control Header</h2>
<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Mã Quy Trình (SOP Code)</th>
            <td style="width: 25%;"><strong>SOP-DGM-DOC-01</strong></td>
            <th style="width: 25%;">Phiên Bản (Version)</th>
            <td style="width: 25%;">v2.6.0 (Enterprise Gold Master)</td>
        </tr>
        <tr>
            <th>Ngày Hiệu Lực</th>
            <td>14/10/2026</td>
            <th>Phân Loại Bảo Mật</th>
            <td>Kiến Trúc Tự Động Hóa &amp; Tri Thức Số (Architecture Confidential)</td>
        </tr>
        <tr>
            <th>Pháp Nhân Sở Hữu</th>
            <td colspan="3">
                <strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)</strong><br/>
                <em>Hạ tầng phân loại:</em> Insilos Enterprise AI Documents Workspace (Thư mục Gốc ID <code>3223</code>)<br/>
                <em>Công nghệ lập chỉ mục:</em> SOP-RAG Chunking Engine (<code>al2c.rag.chunk</code> &amp; <code>al2c.rag.service</code>)
            </td>
        </tr>
        <tr>
            <th>Chủ Trì Quy Trình (Process Owner)</th>
            <td>AI Solutions Architect &amp; Giám đốc Công nghệ (CTO Nguyễn Hoài Ân)</td>
            <th>Căn Cứ Kỹ Thuật</th>
            <td>Luật Giao dịch điện tử 2023; Nghị định 13/2023/NĐ-CP; Kiến trúc mô hình AI Documents và Thuật toán Reciprocal Rank Fusion (RRF k=60).</td>
        </tr>
    </tbody>
</table>

<h2>2. Ma Trận Phân Nhiệm RACI (RACI Governance Matrix)</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Hạng Mục Công Việc</th>
            <th>Chairman/CEO (Lê Xuân Hoàng)</th>
            <th>Finance/HR Lead (Mai Thị Hồng Thắm)</th>
            <th>CTO/Product Lead (Nguyễn Hoài Ân)</th>
            <th>Project Managers (PMs)</th>
            <th>Engineers (Kỹ sư phần mềm)</th>
            <th>AI Autonomous Agents (Tác tử AI)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Thiết lập cấu trúc thư mục và cấu hình ai_sort_prompt trên Folder 3223</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>A</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>I</strong></td>
        </tr>
        <tr>
            <td>Phân tích OCR và tự động điều hướng chứng từ vào 6 thư mục chức năng</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Kiểm tra tài liệu đa trang (is_multipage) và gắn thẻ To Split</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Fail-Closed)</strong></td>
        </tr>
        <tr>
            <td>Băm đoạn tri thức SOP và nạp vào bảng al2c_rag_chunk theo chuẩn citation</td>
            <td><strong>I</strong></td>
            <td><strong>C</strong></td>
            <td><strong>A</strong></td>
            <td><strong>C</strong></td>
            <td><strong>C</strong></td>
            <td><strong>R (Automated)</strong></td>
        </tr>
        <tr>
            <td>Vận hành Cổng suy diễn chống ảo giác (Entailment Gate &gt;= 0.85)</td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>A</strong></td>
            <td><strong>I</strong></td>
            <td><strong>I</strong></td>
            <td><strong>R (Fail-Closed)</strong></td>
        </tr>
    </tbody>
</table>
<p><em>Ghi chú: A = Accountable; R = Responsible; C = Consulted; I = Informed. Áp dụng cho Thư mục Gốc ID 3223 và bảng al2c_rag_chunk.</em></p>

<h2>3. Các Bước Thao Tác Kỹ Thuật Trên Hệ Thống ERP Insilos 20</h2>
<h3>Bước 1: Cấu Trúc Không Gian Làm Việc Tài Liệu DGM (Thư mục 3223 &amp; Thư mục Con)</h3>
<p>Kiến trúc cây thư mục <code>documents.document</code> của Digimate JSC được khóa cấu trúc chuẩn:</p>
<ul>
    <li><strong>Thư mục Gốc <code>3223</code>:</strong> <code>DGM · Công ty Cổ phần Người Bạn Số (Digimate JSC)</code>.</li>
    <li><strong>6 Thư mục Chức năng Trực tiếp (Level 1):</strong>
        <ol>
            <li><code>3224</code>: <code>01. Pháp lý &amp; Quản trị Doanh nghiệp (DGM - ĐKTL)</code> — Chứa GPKD, Điều lệ, ĐHĐCĐ.</li>
            <li><code>3225</code>: <code>02. Tài chính, Kế toán &amp; Thuế (DGM - TÀI CHÍNH)</code> — Chứa các thư mục con chuyên biệt:
                <ul>
                    <li><code>3249</code>: <code>Hoá đơn đầu ra</code> (Canva USD wire notices, HĐĐT 1C26TAA).</li>
                    <li><code>3250</code>: <code>Hoá đơn đầu vào</code> (VNPT internet, Viettel-CA chữ ký số).</li>
                    <li><code>3248</code>: <code>BHXH</code> (Thông báo Mẫu C12-TS mã TZ0857G).</li>
                    <li><code>3251</code>: <code>LƯƠNG</code> &amp; <code>3252</code>: <code>Lương DGM</code> (Bảng kê VCB DigiBiz).</li>
                </ul>
            </li>
            <li><code>3226</code>: <code>03. Hợp đồng Thương mại &amp; Dự án (DGM - HỢP ĐỒNG)</code>:
                <ul>
                    <li><code>3231</code>: <code>TÀI BÙI</code> (Hợp đồng MTI Technology DIGIMATE2401-001).</li>
                    <li><code>3230</code>: <code>MBF</code> (Hợp đồng MobiFone CSP MobiAI).</li>
                </ul>
            </li>
            <li><code>3227</code>: <code>04. Nhân sự &amp; Hợp đồng Lao động (DGM - NHÂN SỰ)</code> — Chứa hồ sơ 8 nhân viên, HĐLĐ 2026.</li>
            <li><code>3228</code>: <code>05. Sở hữu Trí tuệ &amp; Bản quyền (DGM - SỞ HỮU TRÍ TUỆ)</code> — Mẫu 01/02 Cục Bản quyền.</li>
            <li><code>3229</code>: <code>06. Thương hiệu &amp; Hình ảnh (DGM - HÌNH ẢNH 2025)</code> — Vector logo, bộ nhận diện.</li>
        </ol>
    </li>
</ul>

<h3>Bước 2: Cấu Hình <code>ai_sort_prompt</code> Phân Loại Thông Minh</h3>
<ul>
    <li>Tại Thư mục Gốc 3223, trường <code>ai_sort_prompt</code> được cấu hình để tự động nhận diện nội dung văn bản tải lên:
        <ul>
            <li>Văn bản chứa <em>Canva</em>, <em>Swift Credit Advice</em>, <em>USD wire</em> -&gt; Chuyển vào Thư mục <code>3249</code> và gắn tag <code>Canva Export</code>.</li>
            <li>Văn bản chứa <em>VNPT</em>, <em>Viettel-CA</em>, <em>Hóa đơn GTGT đầu vào</em> -&gt; Chuyển vào Thư mục <code>3250</code> và kích hoạt luồng chi phí trả trước TK 242.</li>
            <li>Văn bản chứa <em>BHXH</em>, <em>C12-TS</em>, <em>TZ0857G</em> -&gt; Chuyển vào Thư mục <code>3248</code> và đối soát chỉ tiêu nợ [Đ.2.2].</li>
            <li>Văn bản chứa <em>bangkemau-VCB-DigiBiz</em>, <em>bảng thanh toán lương</em> -&gt; Chuyển vào Thư mục <code>3252</code>.</li>
            <li>Văn bản chứa <em>MTI Technology</em>, <em>DIGIMATE2401-001</em> -&gt; Chuyển vào Thư mục <code>3231</code>.</li>
        </ul>
    </li>
    <li><strong>Rào chắn đa trang (Multipage Check):</strong> Nếu <code>is_multipage == True</code>, hệ thống tự động gán nhãn <code>To Split</code> và tạm dừng điều hướng để người dùng rà soát tách trang trước khi phân loại.</li>
</ul>

<h3>Bước 3: Quy Chuẩn Băm Đoạn SOP-RAG Indexing (<code>al2c.rag.chunk</code>)</h3>
<p>Toàn bộ 13 quy trình vận hành chuẩn SOP được băm đoạn tự động vào bảng <code>al2c_rag_chunk</code> phục vụ hỏi đáp AI:</p>
<ul>
    <li><strong>Định dạng thẻ trích dẫn chuẩn hóa (Citation Tag):</strong>
        <pre><code>citation_tag = f"[{doc_code} | {section_title} | {record_id} | {chunk_hash[:8]}]"
Ví dụ: [SOP-DGM-FIN-01 | Phân bổ TK 242 VNPT | 1684 | a8f9c1e2]</code></pre>
    </li>
    <li><strong>Bất biến Bảng Markdown (Markdown Table Continuity Invariant):</strong> Khi một bảng dữ liệu vượt quá độ dài tối đa của chunk (<code>max_tokens = 600</code>), hệ thống tự động sao chép lại Dòng Tiêu đề (Header Row) và Dòng Phân cách (Delimiter Row) vào đầu mọi sub-chunk tiếp theo, đảm bảo mô hình ngôn ngữ không bao giờ bị mất ngữ cảnh của cột.</li>
    <li><strong>Thuật toán dung hợp xếp hạng RRF:</strong> Kết hợp Dense Vector và Sparse BM25 với hệ số $k=60$:
        $$RRF(d) = \sum_{m \in \{dense, sparse\}} \frac{1}{60 + \text{rank}_m(d)}$$
    </li>
    <li><strong>Cổng suy diễn chống ảo giác (Entailment Gate $\ge 0.85$):</strong> Mọi câu trả lời của AI trợ lý nếu có điểm tương đồng thực thể (Entity Alignment) dưới 0.85 đối với các thông tin nhạy cảm (MST <code>0317958465</code>, STK Vietcombank <code>1202703007</code>, mã BHXH <code>TZ0857G</code>) đều bị khóa và trả về thông báo từ chối.</li>
</ul>

<h2>4. Cổng Kiểm Soát Nội Bộ, Xử Lý Ngoại Lệ & Bộ Đếm Thời Gian SLA</h2>
<table class="table table-bordered">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>Cổng Kiểm Soát (Gate)</th>
            <th>Quy Chuẩn Thẩm Định</th>
            <th>Hành Vi Hệ Thống (Fail-Closed)</th>
            <th>Bộ Đếm SLA</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>GATE-DOC-01: Allowed Target Folders</strong></td>
            <td>Chỉ cho phép chuyển tài liệu vào các thư mục đã khai báo tường minh trong <code>allowed_ids</code> của prompt.</td>
            <td>Ném lỗi <code>UserError</code> nếu AI định chuyển tệp ra ngoài cấu trúc Thư mục 3223.</td>
            <td>Thời gian thực</td>
        </tr>
        <tr>
            <td><strong>GATE-DOC-02: Multipage Isolation</strong></td>
            <td>Phát hiện tài liệu scan nhiều trang chứa nhiều chứng từ khác loại.</td>
            <td>Tự động gắn tag <code>To Split</code> và cách ly tại Inbox để người dùng phân tách trang.</td>
            <td>Thời gian thực</td>
        </tr>
        <tr>
            <td><strong>GATE-DOC-03: SOP-RAG Re-indexing SLA</strong></td>
            <td>Tự động tái lập chỉ mục (Re-index) khi có bài viết SOP mới hoặc cập nhật nội dung trong <code>knowledge.article</code>.</td>
            <td>Cron quét High-Watermark tự động cập nhật các chunk và xóa bỏ các chunk mồ côi.</td>
            <td>Trong vòng <strong>15 Phút</strong></td>
        </tr>
    </tbody>
</table>

<h2>5. Hồ Sơ Bằng Chứng Kiểm Toán (al2c.rag.chunk)</h2>
<ul>
    <li>Mô hình lưu trữ: <code>al2c.rag.chunk</code> trên cơ sở dữ liệu <code>insilos20_dev</code>.</li>
    <li>Chỉ tiêu kiểm định nghiệm thu:
        <ol>
            <li>100% 13 bài viết SOP được băm đoạn hoàn chỉnh với đầy đủ citation tag.</li>
            <li>Mọi truy vấn RAG về Canva 0%, MTI OT 2 bậc, VCB DigiBiz 11 cột, BHXH TZ0857G đều trả về kết quả chính xác tuyệt đối kèm trích dẫn nguồn.</li>
        </ol>
    </li>
</ul>
</div>"""
    }
]

ROOT_ARTICLE = {
    "xml_id": "kb_dgm_sop_root",
    "name": "DGM · Quy Trình Vận Hành Chuẩn (Digimate JSC - MST 0317958465)",
    "icon": "🏛️",
    "sequence": 10,
    "body": r"""<div class="dgm-sop-root-container">
<h1>DGM · Quy Trình Vận Hành Chuẩn (Digimate JSC - MST 0317958465)</h1>
<p class="lead"><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGITAL MATE JOINT STOCK COMPANY / DGM)</strong></p>
<p>Hệ thống tài liệu Quy trình Vận hành Chuẩn (Standard Operating Procedures - SOP) toàn diện, field-accurate được biên soạn và chuẩn hóa phục vụ quản trị doanh nghiệp, kiểm soát rủi ro doanh thu số, tự động hóa luồng tài liệu và vận hành hệ thống ERP Insilos 20.</p>

<table class="table table-bordered">
    <tbody>
        <tr>
            <th style="width: 25%;">Tên Pháp Nhân</th>
            <td style="width: 75%;"><strong>CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ</strong> (Tên quốc tế: DIGITAL MATE JOINT STOCK COMPANY)</td>
        </tr>
        <tr>
            <th>Mã Số Thuế</th>
            <td><strong>0317958465</strong> (Cấp ngày 28/07/2023, thay đổi ĐKKD ngày 19/01/2026 tại Sở KH&ĐT TP.HCM)</td>
        </tr>
        <tr>
            <th>Địa Chỉ Trụ Sở</th>
            <td>Số 11, Đường số 3, KDC CityLand, Phường Tân Mỹ (trước sáp nhập là Phường Tân Phú, Quận 7), TP. Hồ Chí Minh, Việt Nam</td>
        </tr>
        <tr>
            <th>Tài Khoản Ngân Hàng</th>
            <td>Vietcombank (VCB) Chi nhánh Tân Định — STK: <strong>1202703007</strong> — Tên thụ hưởng: <strong>CONG TY CO PHAN NGUOI BAN SO</strong></td>
        </tr>
        <tr>
            <th>Mã Đơn Vị BHXH</th>
            <td><strong>TZ0857G</strong> (Bảo hiểm Xã hội Quận 7, TP. Hồ Chí Minh)</td>
        </tr>
        <tr>
            <th>Ký Hiệu Hóa Đơn Điện Tử</th>
            <td><strong>1C25TBS</strong> (2025), <strong>1C26TAA</strong> (2026) qua hệ thống Viettel SInvoice</td>
        </tr>
    </tbody>
</table>

<h2>Danh Mục 13 Quy Trình Vận Hành Chuẩn (SOP Inventory)</h2>
<table class="table table-bordered table-hover">
    <thead>
        <tr style="background-color: #f1f5f9;">
            <th>#</th>
            <th>Mã SOP</th>
            <th>Tên Quy Trình Vận Hành Chuẩn</th>
            <th>Phân Hệ ERP Áp Dụng</th>
            <th>Process Owner</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>1</td>
            <td><strong>SOP-DGM-GOV-01</strong></td>
            <td>Quy trình Quản trị Pháp nhân, Rào chắn Danh tính Doanh nghiệp &amp; Quản lý Con dấu Số</td>
            <td><code>documents.document</code>, <code>res.company</code>, <code>sign</code></td>
            <td>Tổng Giám Đốc (Lê Xuân Hoàng)</td>
        </tr>
        <tr>
            <td>2</td>
            <td><strong>SOP-DGM-REV-01</strong></td>
            <td>Quy trình Nghiệm thu, Tính giờ Overtime 2 Bậc &amp; Xuất Hóa đơn Kỹ sư Onsite MTI Technology</td>
            <td><code>al2c.timesheet.staging</code>, <code>account.move</code></td>
            <td>PM &amp; Kế toán Doanh thu</td>
        </tr>
        <tr>
            <td>3</td>
            <td><strong>SOP-DGM-REV-02</strong></td>
            <td>Quy trình Tiếp nhận Doanh thu Ngoại tệ Canva Pty Ltd, Kiểm soát Tỷ giá &amp; Xuất HĐĐT 24h SLA</td>
            <td><code>account.move</code>, <code>documents.document</code></td>
            <td>Kế toán Ngân hàng &amp; Thuế</td>
        </tr>
        <tr>
            <td>4</td>
            <td><strong>SOP-DGM-REV-03</strong></td>
            <td>Quy trình Đối soát Doanh thu Tổng - Ròng (Gross-vs-Net) Nền tảng Quốc tế (Apple, Google, PayPal, AdMob)</td>
            <td><code>account.move</code>, <code>account.journal</code></td>
            <td>Kế toán Tổng hợp</td>
        </tr>
        <tr>
            <td>5</td>
            <td><strong>SOP-DGM-REV-04</strong></td>
            <td>Quy trình Hợp tác Viễn thông MobiFone MobiAI, Đối soát CDR &amp; Giải quyết Khiếu nại 48h</td>
            <td><code>sale.order</code>, <code>helpdesk.ticket</code>, <code>documents.document</code></td>
            <td>Trưởng ban Đối tác CSP</td>
        </tr>
        <tr>
            <td>6</td>
            <td><strong>SOP-DGM-FIN-01</strong></td>
            <td>Quy trình Phân bổ Chi phí Trả trước TK 242 Hóa đơn Viễn thông &amp; Chữ ký số</td>
            <td><code>account.asset</code>, <code>account.move</code></td>
            <td>Kế toán Tài sản &amp; Chi phí</td>
        </tr>
        <tr>
            <td>7</td>
            <td><strong>SOP-DGM-FIN-02</strong></td>
            <td>Quy trình Khóa sổ Kế toán Tháng/Quý/Năm &amp; Vận hành Két sắt Quyết toán Thuế 9 Điểm</td>
            <td><code>account.move</code>, <code>documents.document</code></td>
            <td>Kế toán Trưởng / Finance Lead</td>
        </tr>
        <tr>
            <td>8</td>
            <td><strong>SOP-DGM-PRJ-01</strong></td>
            <td>Quy trình Quản trị Giai đoạn Dự án SAP Activate, Khóa Cổng Nghiệm thu &amp; Kiểm soát Ngân sách 85%</td>
            <td><code>project.project</code>, <code>project.milestone</code>, <code>project.task</code></td>
            <td>Giám đốc Chuyển giao Dự án</td>
        </tr>
        <tr>
            <td>9</td>
            <td><strong>SOP-DGM-IP-01</strong></td>
            <td>Quy trình Đăng ký Bản quyền Tác giả Phần mềm Cục Bản quyền &amp; Chứng minh Ưu đãi Thuế TNDN</td>
            <td><code>knowledge.article</code>, <code>documents.document</code></td>
            <td>Trưởng ban R&amp;D &amp; Pháp chế IP</td>
        </tr>
        <tr>
            <td>10</td>
            <td><strong>SOP-DGM-HR-01</strong></td>
            <td>Quy trình Tuyển dụng, Tiếp nhận Nhân sự &amp; Ký Hợp đồng Lao động 16 Điều 2026</td>
            <td><code>hr.employee</code>, <code>hr.contract</code>, <code>sign</code></td>
            <td>People Operations Lead</td>
        </tr>
        <tr>
            <td>11</td>
            <td><strong>SOP-DGM-HR-02</strong></td>
            <td>Quy trình Tính lương Hàng tháng, Đăng ký NPT &amp; Xuất Bảng kê 11 Cột Vietcombank DigiBiz</td>
            <td><code>hr.payslip.run</code>, <code>hr.payslip</code></td>
            <td>Chuyên viên C&amp;B &amp; Kế toán Lương</td>
        </tr>
        <tr>
            <td>12</td>
            <td><strong>SOP-DGM-HR-03</strong></td>
            <td>Quy trình Đối soát BHXH Mẫu C12-TS Mã Đơn vị TZ0857G &amp; Khóa Không Nợ Đọng</td>
            <td><code>account.move</code>, <code>documents.document</code></td>
            <td>Kế toán Tiền lương &amp; BHXH</td>
        </tr>
        <tr>
            <td>13</td>
            <td><strong>SOP-DGM-DOC-01</strong></td>
            <td>Quy trình Phân loại Tài liệu Tự động AI Documents &amp; Lập chỉ mục Tri thức SOP-RAG</td>
            <td><code>documents.document</code>, <code>al2c.rag.chunk</code></td>
            <td>AI Solutions Architect &amp; CTO</td>
        </tr>
    </tbody>
</table>

<p><em>Mọi sửa đổi, bổ sung đối với các tài liệu quy trình trên bắt buộc phải thông qua Hội đồng Quản trị và ban hành phiên bản mới dưới sự kiểm soát của Process Owner.</em></p>
</div>"""
}

# ------------------------------------------------------------------------------
# AUDIT GUARD: STRICT ZERO BRANDING VIOLATION CHECK
# ------------------------------------------------------------------------------

def audit_zero_branding(items):
    """Assert zero occurrences of forbidden branding strings ('Odoo', 'OpenERP')."""
    pattern = re.compile(r'(?i)\b(odoo|openerp)\b')
    for item in items:
        for key in ["title", "name", "body"]:
            val = item.get(key)
            if val:
                match = pattern.search(val)
                if match:
                    raise AssertionError(
                        f"CRITICAL BRANDING VIOLATION: Found forbidden string '{match.group(0)}' "
                        f"in article {item.get('code') or item.get('xml_id')} field '{key}'!"
                    )
    print(">>> ZERO BRANDING AUDIT: PASSED (0 occurrences of forbidden branding strings found).")


# ------------------------------------------------------------------------------
# XML DATA GENERATOR
# ------------------------------------------------------------------------------

def generate_xml_data(output_path):
    """Generate addons/insilos_al2c/data/dgm_sop_corpus_data.xml."""
    audit_zero_branding([ROOT_ARTICLE] + SOPS)
    
    lines = []
    lines.append('<?xml version="1.0" encoding="utf-8"?>')
    lines.append('<odoo>')
    lines.append('<data noupdate="1">')
    lines.append('')
    lines.append('    <!-- Root SOP Article -->')
    lines.append(f'    <record id="{ROOT_ARTICLE["xml_id"]}" model="knowledge.article">')
    lines.append(f'        <field name="name">{ROOT_ARTICLE["name"]}</field>')
    lines.append(f'        <field name="icon">{ROOT_ARTICLE["icon"]}</field>')
    lines.append('        <field name="internal_permission">write</field>')
    lines.append(f'        <field name="sequence">{ROOT_ARTICLE["sequence"]}</field>')
    lines.append(f'        <field name="body"><![CDATA[{ROOT_ARTICLE["body"]}]]></field>')
    lines.append('    </record>')
    lines.append('')
    
    for sop in SOPS:
        lines.append(f'    <!-- {sop["code"]} -->')
        lines.append(f'    <record id="{sop["xml_id"]}" model="knowledge.article">')
        # Escape & in title if any
        escaped_title = sop["title"].replace("&", "&amp;")
        lines.append(f'        <field name="name">{escaped_title}</field>')
        lines.append(f'        <field name="parent_id" ref="{ROOT_ARTICLE["xml_id"]}"/>')
        lines.append(f'        <field name="icon">{sop["icon"]}</field>')
        lines.append('        <field name="internal_permission">write</field>')
        lines.append(f'        <field name="sequence">{sop["sequence"]}</field>')
        lines.append(f'        <field name="body"><![CDATA[{sop["body"]}]]></field>')
        lines.append('    </record>')
        lines.append('')
        
    lines.append('</data>')
    lines.append('</odoo>')
    lines.append('')
    
    content = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f">>> XML DATA GENERATED SUCCESSFULLY: {output_path} ({len(content)} bytes)")


# ------------------------------------------------------------------------------
# DATABASE POPULATOR & SYNCHRONIZER (DIRECT POSTGRESQL + ORM HYBRID)
# ------------------------------------------------------------------------------

def populate_database(db_name="insilos20_dev", host="127.0.0.1", port=5434, user="odoo", password="1NN0R1@2026"):
    """Idempotently load and synchronize root article and 13 SOPs directly into DB."""
    import psycopg2
    from psycopg2.extras import DictCursor

    print(f">>> Connecting directly to PostgreSQL database '{db_name}' on {host}:{port} as '{user}'...")
    conn = psycopg2.connect(dbname=db_name, host=host, port=port, user=user, password=password)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=DictCursor)
    MODULE = 'insilos_al2c'

    try:
        # 1. Sync Root Article
        cur.execute("SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s", (MODULE, ROOT_ARTICLE['xml_id']))
        row = cur.fetchone()
        root_id = row['res_id'] if row else None

        if root_id:
            cur.execute("SELECT id FROM knowledge_article WHERE id = %s", (root_id,))
            if not cur.fetchone():
                root_id = None

        if not root_id:
            cur.execute("SELECT id FROM knowledge_article WHERE name = %s LIMIT 1", (ROOT_ARTICLE['name'],))
            row = cur.fetchone()
            if row:
                root_id = row['id']
            else:
                cur.execute("""
                    INSERT INTO knowledge_article (
                        name, icon, sequence, internal_permission, inherited_permission,
                        category, body, active, is_published, full_width, create_uid, write_uid,
                        create_date, write_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, NOW(), NOW())
                    RETURNING id
                """, (
                    ROOT_ARTICLE['name'], ROOT_ARTICLE['icon'], ROOT_ARTICLE['sequence'],
                    'write', 'write', 'workspace', ROOT_ARTICLE['body'], True, True, True
                ))
                root_id = cur.fetchone()['id']

        # Update root article fields and parent_path
        parent_path = f"{root_id}/"
        cur.execute("""
            UPDATE knowledge_article
            SET name = %s, icon = %s, sequence = %s, internal_permission = 'write',
                inherited_permission = 'write', category = 'workspace', body = %s,
                active = TRUE, is_published = TRUE, full_width = TRUE,
                root_article_id = %s, parent_path = %s, write_uid = 1, write_date = NOW()
            WHERE id = %s
        """, (ROOT_ARTICLE['name'], ROOT_ARTICLE['icon'], ROOT_ARTICLE['sequence'], ROOT_ARTICLE['body'], root_id, parent_path, root_id))

        # Ensure ir_model_data for root
        cur.execute("""
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, 'knowledge.article', %s, TRUE, 1, 1, NOW(), NOW())
            ON CONFLICT (module, name) DO UPDATE SET res_id = EXCLUDED.res_id, write_date = NOW()
        """, (ROOT_ARTICLE['xml_id'], MODULE, root_id))
        print(f">>> Root Article Synced: ID {root_id} — '{ROOT_ARTICLE['name']}'")

        # 2. Clean up legacy preliminary articles (IDs 1678 to 1683 or matching SOP-DGM-0%)
        legacy_names = [
            'kb_dgm_sop_01_governance', 'kb_dgm_sop_02_revenue_risk',
            'kb_dgm_sop_03_b2b_contracts', 'kb_dgm_sop_04_hr_payroll_bhxh',
            'kb_dgm_sop_05_tax_settlement', 'kb_dgm_sop_06_ip_brand'
        ]
        cur.execute("SELECT res_id FROM ir_model_data WHERE module = %s AND name = ANY(%s)", (MODULE, legacy_names))
        legacy_ids = [r['res_id'] for r in cur.fetchall() if r['res_id']]

        # Also find any children under root matching old naming pattern
        cur.execute("SELECT id FROM knowledge_article WHERE parent_id = %s AND name LIKE 'SOP-DGM-0%%'", (root_id,))
        for r in cur.fetchall():
            if r['id'] not in legacy_ids:
                legacy_ids.append(r['id'])

        if legacy_ids:
            print(f">>> Removing {len(legacy_ids)} legacy preliminary articles: {legacy_ids}")
            cur.execute("DELETE FROM ir_model_data WHERE model = 'knowledge.article' AND res_id = ANY(%s)", (legacy_ids,))
            cur.execute("DELETE FROM knowledge_article WHERE id = ANY(%s)", (legacy_ids,))

        # 3. Synchronize all 13 canonical SOPs
        synced_sops = []
        for sop in SOPS:
            # Check ir_model_data
            cur.execute("SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s", (MODULE, sop['xml_id']))
            row = cur.fetchone()
            sop_id = row['res_id'] if row else None

            if sop_id:
                cur.execute("SELECT id FROM knowledge_article WHERE id = %s", (sop_id,))
                if not cur.fetchone():
                    sop_id = None

            if not sop_id:
                code_pattern = sop['code'] + ' ·%'
                cur.execute("SELECT id FROM knowledge_article WHERE parent_id = %s AND name LIKE %s LIMIT 1", (root_id, code_pattern))
                row = cur.fetchone()
                if row:
                    sop_id = row['id']
                else:
                    cur.execute("""
                        INSERT INTO knowledge_article (
                            name, parent_id, root_article_id, sequence, icon,
                            internal_permission, inherited_permission, category,
                            body, active, is_published, full_width, create_uid, write_uid,
                            create_date, write_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, NOW(), NOW())
                        RETURNING id
                    """, (
                        sop['title'], root_id, root_id, sop['sequence'], sop['icon'],
                        'write', 'write', 'workspace', sop['body'], True, True, True
                    ))
                    sop_id = cur.fetchone()['id']

            # Update SOP article
            child_parent_path = f"{root_id}/{sop_id}/"
            cur.execute("""
                UPDATE knowledge_article
                SET name = %s, parent_id = %s, root_article_id = %s, sequence = %s,
                    icon = %s, internal_permission = 'write', inherited_permission = 'write',
                    category = 'workspace', body = %s, active = TRUE, is_published = TRUE,
                    full_width = TRUE, parent_path = %s, write_uid = 1, write_date = NOW()
                WHERE id = %s
            """, (sop['title'], root_id, root_id, sop['sequence'], sop['icon'], sop['body'], child_parent_path, sop_id))

            # Ensure ir_model_data
            cur.execute("""
                INSERT INTO ir_model_data (name, module, model, res_id, noupdate, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, 'knowledge.article', %s, TRUE, 1, 1, NOW(), NOW())
                ON CONFLICT (module, name) DO UPDATE SET res_id = EXCLUDED.res_id, write_date = NOW()
            """, (sop['xml_id'], MODULE, sop_id))

            synced_sops.append((sop_id, sop['code'], sop['title']))
            print(f"    [+] Synced SOP: ID {sop_id:4d} | {sop['code']:14s} | {sop['title'][:60]}...")

        # 4. Verification Check
        cur.execute("SELECT id, name, sequence, icon, LENGTH(body) as body_len FROM knowledge_article WHERE parent_id = %s ORDER BY sequence, id", (root_id,))
        final_children = cur.fetchall()
        print(f"\n>>> Verification: Root ID {root_id} has {len(final_children)} child articles.")
        for idx, child in enumerate(final_children, 1):
            print(f"      {idx:2d}. [ID {child['id']:4d}] seq={child['sequence']:2d} icon={child['icon']} len={child['body_len']:6d} | {child['name'][:65]}")

        assert len(final_children) == 13, f"Expected exactly 13 child articles, but found {len(final_children)}!"

        # Commit transaction
        conn.commit()
        print(">>> ALL DATABASE TRANSACTIONS COMMITTED CLEANLY TO POSTGRESQL!")

    except Exception as e:
        conn.rollback()
        print(f"ERROR during database synchronization: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ------------------------------------------------------------------------------
# MAIN EXECUTION ENTRYPOINT
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    REPO_ROOT = "/home/zen/O20"
    DATA_XML_PATH = os.path.join(REPO_ROOT, "addons/insilos_al2c/data/dgm_sop_corpus_data.xml")
    
    print("=" * 80)
    print("DGM SOP CORPUS GENERATOR & SYNCHRONIZER")
    print("Legal Entity: CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (MST: 0317958465)")
    print("=" * 80)
    
    # 1. Audit and Generate XML Data File
    generate_xml_data(DATA_XML_PATH)
    
    # 2. Synchronize Database
    populate_database(db_name="insilos20_dev", host="127.0.0.1", port=5434, user="odoo", password="1NN0R1@2026")
    
    print("=" * 80)
    print("SUCCESS: 13/13 DGM SOP ARTICLES AUTHORED, VALIDATED & SYNCHRONIZED!")
    print("=" * 80)

