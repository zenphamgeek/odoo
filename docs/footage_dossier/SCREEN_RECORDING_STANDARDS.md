# QUY CHUẨN KỸ THUẬT SCREEN RECORDING & TỰ ĐỘNG HÓA GHI HÌNH FOOTAGE DOANH NGHIỆP INSILOS
## Architectural Standard & Automated Footage Production Engine (Deliverable D2)

---

### Executive Overview & Council Mandate

Tài liệu này xác lập **Quy chuẩn Kỹ thuật Quốc tế Toàn diện (Engineering Master Standard)** cho toàn bộ quy trình ghi hình màn hình tự động hóa (*Headless Automated Screen Recording*) và sản xuất tư liệu B-Roll / Walkthrough điện ảnh phục vụ Hệ điều hành Doanh nghiệp Insilos (`http://localhost:28069`). 

Được thẩm định và ban hành bởi **Hội đồng Chuyên gia Cấp cao Insilos (Senior Expert Council)**:
- **Marketing Director of Google**: Tiêu chuẩn điện ảnh B-Roll, Zero Browser Chrome (khử 100% thanh địa chỉ, tab, bookmark), hiệu ứng tương tác thị giác Neon Cursor / Click Ripple / Spotlight Halo, Dynamic Camera Zoom 120%-145%, nhịp điệu kích thích 3 giây đầu (Executive Hook), và Outro 25-Thumbnail Mosaic Closing CTA chuẩn 2K60.
- **Sales Director of SAP**: Trực quan hóa quy trình thầu quy mô lớn (Lead-to-Order-to-Cash), khóa biên lãi gộp, bảo mật phân quyền đa cấp, loại bỏ hoàn toàn các thao tác thừa hoặc độn thời gian.
- **TCO Expert of IBM**: Trực quan hóa các mốc định lượng Total Cost of Ownership (tiết kiệm ₫2,029,050,000 / Năm), luồng dịch chuyển CapEx sang OpEx, và hoàn vốn ROI trong 6–9 tháng.
- **Logistics Dept Head**: Ghi hình điều vận xe container drayage, giám sát DET/DEM bãi Depot Tân Cảng SNP, mức tiêu hao nhiên liệu PVOIL và quét mã vạch Barcode/QR không độ trễ.
- **VCCI Head Việt Nam**: Tính xác thực pháp lý Việt Nam: Hóa đơn điện tử Thông tư 78/2021/TT-BTC, Nghị định 123/2020/NĐ-CP, chế độ kế toán Thông tư 200/2014/TT-BTC, và e-PTW an toàn lao động.
- **Giám đốc Sản xuất**: Chuẩn mực Shop Floor Tablet (MES), trạm cắt Laser CNC SS400, robot hàn Yaskawa, cấu trúc BOM xe kéo điện V-LIFT 2500E, và chỉ số OEE $\ge 92\%$.

---

## 1. Kiến Trúc Playwright Headless 1920x1080 Zero Browser Chrome

```
+----------------------------------------------------------------------------------------------------+
|                KIẾN TRÚC GHI HÌNH ĐỘC LẬP: ZERO BROWSER CHROME (CANVAS VIEWPORT ISOLATION)         |
+------------------------------------+---------------------------------------------------------------+
| 1. VIEWPORT CANVAS ISOLATION       | Playwright Browser Context cô lập tuyệt đối 1920x1080 @ 60fps |
|                                    | 0% Address Bar | 0% Tabs | 0% Bookmarks | 0% OS Desktop Chrome |
+------------------------------------+---------------------------------------------------------------+
| 2. SESSION COOKIE PRE-INJECTION    | Tiêm Cookie / LocalStorage trước khi mở trang qua JSON-RPC     |
|                                    | Khử 100% màn hình đăng nhập, chuyển trực tiếp vào Business UI |
+------------------------------------+---------------------------------------------------------------+
| 3. OCR 120PX TOP BANNER VALIDATION | Bộ quét Tesseract OCR kiểm định dải 120px đỉnh khung hình      |
|                                    | Ngưỡng vi phạm = 0 (CẤM: localhost, 127.0.0.1, http://, chrome)|
+------------------------------------+---------------------------------------------------------------+
```

### 1.1. Nguyên Lý Khử Thanh Địa Chỉ (Zero Browser Chrome)
Trong sản xuất video B2B Enterprise chuẩn phát sóng quốc tế, việc để lộ thanh URL trình duyệt (`http://localhost:28069`), nút Reload, bookmark bar cá nhân, tiện ích mở rộng (extensions) hay avatar tài khoản người dùng là **lỗi kỹ xảo nghiêm trọng** làm mất đi tính nguyên bản của phần mềm doanh nghiệp độc lập.

Hệ thống ghi hình Insilos sử dụng kiến trúc **Viewport Canvas Isolation** thông qua Chromium Headless:
1. **Khởi chạy Chromium với cờ cách ly**:
   ```python
   browser = playwright.chromium.launch(
       executable_path="/usr/bin/google-chrome",
       headless=True,
       args=[
           "--no-sandbox",
           "--disable-setuid-sandbox",
           "--hide-scrollbars",
           "--disable-infobars",
           "--force-device-scale-factor=1",
           "--disable-background-timer-throttling",
           "--disable-renderer-backgrounding",
           "--font-render-hinting=max"
       ]
   )
   ```
2. **Khởi tạo Browser Context chuẩn Full HD 1080p**:
   ```python
   context = browser.new_context(
       viewport={"width": 1920, "height": 1080},
       device_scale_factor=1,
       record_video_dir=temp_video_dir,
       record_video_size={"width": 1920, "height": 1080},
       ignore_https_errors=True
   )
   ```
3. Toàn bộ luồng video MP4 xuất ra từ Playwright thu nhận trực tiếp bề mặt render đồ họa bên trong Canvas DOM. Tuyệt đối không chứa bất kỳ pixel nào của khung viền hệ điều hành (Window borders), tiêu đề tab hay thanh điều hướng web.

### 1.2. Tiêm Trạng Thái Xác Thực Trước Khi Ghi Hình (Session Cookie Pre-Injection)
Để video mở màn ngay lập tức bằng giao diện nghiệp vụ hoành tráng thay vì màn hình đăng nhập (`/web/login`), bộ điều khiển Playwright nạp trạng thái phiên xác thực trước khi điều hướng:
```python
# Tiêm session_id hợp lệ của quản trị viên Insilos
context.add_cookies([{
    "name": "session_id",
    "value": admin_session_token,
    "domain": "localhost",
    "path": "/",
    "httpOnly": True,
    "sameSite": "Lax"
}])
```
Kết quả: Lệnh `page.goto("http://localhost:28069/web#action=...")` đưa người xem trực tiếp vào giao diện Kanban/Form của phân hệ mục tiêu với độ trễ 0 giây.

### 1.3. Cơ Chế Kiểm Định OCR 120px Đỉnh Màn Hình (OCR Top Banner Gate)
Mọi video trước khi được cấp chứng nhận Gold Master bắt buộc phải vượt qua bài kiểm tra quang học tự động:
1. Trích xuất frame hình ngẫu nhiên tại 7 thời điểm phân cảnh trong video.
2. Cắt dải ảnh chữ nhật kích thước $1920 \times 120$ pixel tại đỉnh màn hình ($y \in [0, 120]$).
3. Sử dụng công cụ Tesseract OCR (`--psm 6`) nhận dạng văn bản tiếng Anh và tiếng Việt.
4. Đối soát với danh mục từ khóa cấm (*Forbidden Tokens*):
   `["localhost", "127.0.0.1", "http://", "https://", "chrome://", "new tab", "bookmarks", "search or enter"]`
5. **Tiêu chuẩn nghiệm thu**: Số lượng phát hiện = 0. Nếu phát hiện bất kỳ token nào, video bị từ chối phát hành ngay lập tức.

---

## 2. Kỹ Xảo Thị Giác Tương Tác Điện Ảnh (Cinematic VFX Suite)

Nhằm định hướng ánh nhìn của các giám đốc điều hành (C-Level Executives) vào các số liệu tài chính và thao tác nghiệp vụ then chốt, hệ thống tích hợp bộ mã VFX JavaScript chuyên sâu tiêm trực tiếp vào cây DOM của trình duyệt.

```
+----------------------------------------------------------------------------------------------------+
|                         BỘ TỨ KỸ XẢO THỊ GIÁC DOANH NGHIỆP (INSILOS VFX SUITE)                     |
+----------------------------------+-----------------------------------------------------------------+
| 1. VIRTUAL NEON CURSOR           | Con trỏ 28px, viền Cyan #00f0ff, lõi trắng 6px, nội suy lerp   |
| 2. CLICK RIPPLE WAVE             | Sóng xung kích 300ms cubic-bezier nở rộng từ 10px -> 75px      |
| 3. ELEMENT SPOTLIGHT HALO        | Vầng sáng neon kép 35px, tối mờ hậu cảnh, viền xung kích cyan  |
| 4. DYNAMIC CAMERA ZOOM           | Phóng đại quang học 120% - 145% vào trường trọng tâm nghiệp vụ  |
+----------------------------------+-----------------------------------------------------------------+
```

### 2.1. Con Trỏ Ảo Công Nghệ Cao (Virtual Neon Cursor)
- **Đặc tính vật lý**: Đường kính outer ring 28px, đường kính inner dot 6px màu trắng tinh khiết (`#ffffff`), viền ngoài 2px màu Cyan công nghệ (`#00f0ff`).
- **Hiệu ứng tỏa sáng (Glow Bloom)**: 
  `box-shadow: 0 0 16px #00d2ff, 0 0 30px rgba(0, 210, 255, 0.60);`
- **Giải thuật nội suy chuyển động (0.12s Lerp / Cubic Smoothing)**:
  Khi di chuyển giữa 2 điểm $(x_1, y_1)$ và $(x_2, y_2)$, con trỏ không nhảy bước tức thời mà trượt dọc theo đường cong Bezier tham số hóa với độ trễ nội suy $0.12$ giây (`transition: transform 0.12s cubic-bezier(0.25, 1, 0.5, 1)`), tái hiện cảm giác di chuột mượt mà của một chuyên gia vận hành hệ thống cấp cao.

### 2.2. Sóng Xung Kích Click Chuột (Click Ripple Shockwave)
- Khi phát sinh sự kiện click chuột tại tọa độ $(X, Y)$, một thẻ DOM phần tử xung kích được kích hoạt tức thời.
- **Thời lượng sóng xung**: 300ms (0.3s).
- **Hàm gia tốc (Timing Function)**: `cubic-bezier(0.1, 0.8, 0.3, 1.0)`.
- **Hành vi biến thiên**: Kích thước nở nhanh từ đường kính $10\text{px}$ lên $75\text{px}$ với viền Cyan `#00ffcc`, đồng thời độ mờ đục (opacity) giảm dần từ $1.0$ về $0.0$.
- Tự động dọn dẹp (DOM unmount) sau khi kết thúc chu trình sóng xung để đảm bảo tải CPU luôn ở mức tối ưu.

### 2.3. Vầng Hào Quang Điểm Nhấn (Element Spotlight Halo)
- Khi kịch bản nhắc đến một chỉ số cốt lõi (ví dụ: Tổng giá trị hợp đồng `18.675.000.000 VNĐ`, hoặc chỉ số `OEE 92.5%`):
  1. Thẻ mục tiêu được gán class `.insilos-spotlight-active`.
  2. Viền ngoài phát sáng với vầng hào quang kép màu Cyan:
     `outline: 3px solid #00d2ff;`
     `box-shadow: 0 0 35px #00d2ff, inset 0 0 15px rgba(0, 210, 255, 0.25);`
  3. Màn mờ hậu cảnh (Backdrop Overlay) phủ một lớp bóng bán trong suốt `rgba(5, 16, 30, 0.45)` lên các khu vực xung quanh trong thời gian 1.5–2.0 giây, thu hút 100% thị giác người xem vào trường số liệu.

### 2.4. Phóng Đại Khung Hình Động (Dynamic Camera Zoom-In Framing)
- **Tỷ lệ phóng to**: Tự động phóng đại quang học từ **120% đến 145%** (`scale(1.20)` đến `scale(1.45)`).
- **Tâm phóng đại (Transform Origin)**: Tính toán chính xác theo tọa độ tâm bounding rect của trường mục tiêu:
  $$\text{Origin}_X = \frac{X_{\text{rect}} + W_{\text{rect}} / 2}{W_{\text{viewport}}} \times 100\%, \quad \text{Origin}_Y = \frac{Y_{\text{rect}} + H_{\text{rect}} / 2}{H_{\text{viewport}}} \times 100\%$$
- **Hành trình Camera**: Thời gian zoom-in $0.4\text{s}$, duy trì khung hình đặc tả trong $2.5\text{s}$, và zoom-out trả về toàn cảnh ($100\%$) trong $0.35\text{s}$, tạo nhịp điệu điện ảnh liền mạch.

### 2.5. Quy Chuẩn Bounding Box & Dữ Liệu Computer Vision Thời Gian Thực
- Tuyệt đối nghiêm cấm việc gắn nhãn CSS tĩnh giả lập AI (`top: 25%; left: 40%`).
- Trong các phân cảnh nhận diện AI Vision (HSE PPE, giám sát bãi xe container):
  * Tọa độ bounding box được nội suy $60\text{ FPS}$ liên tục qua `requestAnimationFrame` dựa trên dữ liệu temporal keyframes.
  * Nhãn nhận diện tuân thủ tuyệt đối tính chân thực thị giác (*Visual Semantic Truth*): Công nhân không đội mũ bảo hộ chuyển tức thì sang viền đỏ nhấp nháy `[VIOLATION: NO HELMET]`. Công nhân đầy đủ trang bị mang viền xanh lá `[HELMET // 99.4%]`.
  * Bảng điều khiển HUD hiển thị tọa độ thời gian thực, Timecode mili-giây và micro-jitter độ trễ suy luận AI ($11.5\text{ms} - 13.8\text{ms}$).

---

## 3. Kỹ Thuật Âm Thanh Xúc Giác Phòng Thu (Tactile SFX 48kHz Stereo)

Âm thanh trong video doanh nghiệp Insilos không chỉ là nhạc nền đơn điệu, mà là **hệ sinh thái âm thanh xúc giác (Tactile SFX Ecosystem)** kích hoạt phản hồi thần kinh của người xem qua từng cú click chuột, gõ phím, quét barcode và duyệt chứng từ.

```
+----------------------------------------------------------------------------------------------------+
|                         BỘ 6 ÂM THANH XÚC GIÁC CÔNG NGHIỆP (INSILOS SFX KIT)                       |
+----------------------+-----------+-------------------------+---------------------------------------+
| Tên Âm Thanh         | Thời Lượng| Dạng Sóng Âm Học        | Ý Nghĩa Nghiệp Vụ                     |
+----------------------+-----------+-------------------------+---------------------------------------+
| 1. sfx_click.wav     | 35 ms     | 3.2kHz transient pulse  | Click chuột cơ học dứt khoát          |
| 2. sfx_type.wav      | 45 ms     | Cherry MX pink noise    | Gõ phím cơ nhập liệu biểu mẫu         |
| 3. sfx_scanner_beep  | 85 ms     | 1760Hz pure sine (A6)   | Tiếng bíp súng quét mã vạch kho/cảng  |
| 4. sfx_whoosh.wav    | 350 ms    | 400Hz->150Hz FM sweep   | Lướt kéo thả thẻ Kanban / trượt modal |
| 5. sfx_chime.wav     | 1.20 s    | C6 - E6 - G6 triad      | Chuông pha lê duyệt hợp đồng / PO     |
| 6. sfx_cash.wav      | 1.00 s    | 2489Hz + 3322Hz bells   | Keng chuông phát hành e-Invoice TT78  |
+----------------------+-----------+-------------------------+---------------------------------------+
```

### 3.1. Nguyên Lý Tổng Hợp Toán Học Thuần Túy (Zero External Sample Dependency)
Toàn bộ thư viện SFX được sinh trực tiếp bằng thuật toán toán học (NumPy / SciPy) ở tần số lấy mẫu **48,000 Hz Stereo**, đảm bảo không phụ thuộc vào bất kỳ thư viện âm thanh thương mại bên ngoài nào và 100% sạch bản quyền:

```python
# Tần số mẫu chuẩn phát sóng quốc tế
SAMPLE_RATE = 48000
target_peak = 10 ** (-1.5 / 20)  # Ceiling -1.5 dBFS (~0.841)
```

### 3.2. Đặc Tả Chi Tiết 6 Tệp Âm Thanh Xúc Giác
1. **`sfx_click.wav` (35ms)**:
   - Cấu trúc: Xung kích khởi tạo nhanh với hàm suy giảm $e^{-220t}$ trên sóng sin 3200Hz, kết hợp dội phụ thứ cấp ở 8ms trên tần số 2400Hz. Tái hiện hoàn hảo tiếng microswitch Omron của chuột cơ cao cấp.
2. **`sfx_type.wav` (45ms)**:
   - Cấu trúc: Burst nhiễu hồng (Pink Noise) có kiểm soát hạt giống ngẫu nhiên kết hợp xung trầm 420Hz mô phỏng đáy phím gõ vào plate nhôm và âm cao 4800Hz tạo độ đanh của switch Cherry MX Blue.
3. **`sfx_scanner_beep.wav` (85ms)**:
   - Cấu trúc: Sóng sin thuần khiết nốt La quãng 6 ($A_6 = 1760\text{Hz}$) với envelope công nghiệp gồm 5ms tấn công (attack), duy trì phẳng 60ms và 20ms tắt dần (decay). Chuẩn âm thanh máy quét Zebra Symbol trong kho vận.
4. **`sfx_whoosh.wav` (350ms)**:
   - Cấu trúc: Nhiễu Gaussian điều biến qua đường bao hình chuông kết hợp quét biến tần FM từ 400Hz xuống 150Hz. Bố trí độ trễ 8ms giữa kênh trái và kênh phải tạo không gian âm thanh nổi (Stereo Stereo Width).
5. **`sfx_chime.wav` (1.20s)**:
   - Cấu trúc: Hợp âm ba Đô trưởng ngân vang gồm 3 nốt: $C_6 (1046.5\text{Hz})$, $E_6 (1318.5\text{Hz})$, $G_6 (1568.0\text{Hz})$ với hệ số tắt dần lũy thừa $e^{-3.5t}, e^{-4.0t}, e^{-4.5t}$. Tạo cảm giác tin cậy, thành công tuyệt đối khi phê duyệt lệnh sản xuất hoặc đơn bán.
6. **`sfx_cash.wav` (1.00s)**:
   - Cấu trúc: Hai chuông kim khí tần số cao ($2489.0\text{Hz}$ và $3322.4\text{Hz}$) cộng hưởng cùng xung kim loại ma sát $6500\text{Hz}$ ở 40ms đầu tiên, tạo âm sắc keng rền dứt khoát khi phát hành hóa đơn tài chính thành công.

### 3.3. Tự Động Hóa Đồng Bộ Đa Kênh (Multi-Track SFX Sync Pipeline)
Trong tệp nhật ký `events.json`, mọi hành vi của Playwright được ghi nhận mốc thời gian mili-giây. Bộ xử lý FFmpeg sử dụng bộ lọc `adelay` và `amix` để ghép nối chính xác các âm thanh xúc giác vào đúng khung hình:
```bash
ffmpeg -i video_raw.mp4 -i sfx_click.wav -i sfx_cash.wav ... \
  -filter_complex "[1:a]adelay=4250|4250,volume=0.85[s1];[2:a]adelay=18700|18700,volume=0.90[s2];[s1][s2]amix=inputs=2[a_sfx];[a_sfx]loudnorm=I=-16.0:TP=-1.5:LRA=7.0[a_out]" \
  -map 0:v -map "[a_out]" -c:v copy -c:a aac -b:a 256k -ar 48000 output_master.mp4
```

---

## 4. Chuẩn Âm Học Phát Sóng Quốc Tế (EBU R128 Broadcast Standard)

Nhằm đảm bảo âm lượng đồng đều trên toàn bộ hệ thống trình chiếu hội trường, website, YouTube B2B và thiết bị di động, mọi tệp âm thanh trong video Gold Master phải tuân thủ nghiêm ngặt chuẩn **EBU R128**:

```
+----------------------------------------------------------------------------------------------------+
|                         CHỈ TIÊU ÂM HỌC QUỐC TẾ EBU R128 (INSILOS AUDIO GATE)                       |
+--------------------------+------------------------------+------------------------------------------+
| Thông Số Đo Đạc          | Ngưỡng Tiêu Chuẩn            | Ngưỡng Dung Sai Cho Phép                 |
+--------------------------+------------------------------+------------------------------------------+
| 1. Integrated Loudness   | -14.0 LUFS                   | [-15.0, -13.0] LUFS (Tối ưu -14.5 ± 0.5) |
| 2. Maximum True Peak     | <= -1.0 dBTP                 | Tuyệt đối không vượt quá -1.0 dBTP       |
| 3. Loudness Range (LRA)  | <= 8.0 LU                    | Dao động từ 2.0 LU đến 6.5 LU            |
| 4. Silence Gate (>3.5s)  | 0 phát hiện tại -50 dBFS     | Không chứa khoảng câm chết > 3.5 giây    |
+--------------------------+------------------------------+------------------------------------------+
```

### 4.1. Giải Thuật Cân Bằng Độ Lớn Hai Lượt (Two-Pass Loudnorm Algorithm)
1. **Lượt 1 (Measurement Pass)**: FFmpeg quét toàn bộ dải âm thanh để đo đạc chỉ số tích hợp thực tế:
   ```bash
   ffmpeg -nostats -vn -i input.mp4 -af loudnorm=print_format=json -f null -
   ```
2. **Lượt 2 (Normalization Pass)**: Nạp các tham số đo được (`measured_I`, `measured_TP`, `measured_LRA`, `measured_thresh`) vào bộ lọc để chuẩn hóa tuyến tính với chất lượng cao nhất, tránh méo tiếng cục bộ do nén động lực quá mức:
   ```bash
   ffmpeg -i input.mp4 -af loudnorm=I=-14.0:TP=-1.0:LRA=7.0:measured_I=...:linear=true -c:a aac -b:a 320k -ar 48000 output.mp4
   ```

### 4.2. Cổng Kiểm Soát Khoảng Câm (Silence Gate)
- Khoảng lặng giữa các câu thoại thông thường kéo dài từ $0.35\text{s}$ đến $2.5\text{s}$ để người xem kịp thẩm thấu thông tin.
- **Lỗi chí mạng (Acoustic Defect)**: Bất kỳ khoảng im lặng nào kéo dài $> 3.5\text{s}$ ở ngưỡng $-50\text{ dBFS}$ (thường do video render dài hơn audio voiceover) bị coi là "khoảng câm chết" và tự động bị đánh trượt trong khâu nghiệm thu.

---

## 5. Kỹ Thuật Chống "Lazy Code" & Chuẩn Hóa Nhịp Điệu (Anti-Lazy Code Engineering)

### 5.1. Hội Chứng Suy Giảm Chất Lượng Lũy Tiến (Fatigue Decay Syndrome)
Trong sản xuất chuỗi $N$ video nghiệp vụ (như 12 kịch bản ERP hoặc loạt bài học Masterclass), hiện tượng phổ biến là:
- **Tập 1**: Đầu tư kỹ lưỡng, nhiều thao tác tương tác, phân cảnh phong phú.
- **Từ tập 2 đến $N$ (Lazy Code)**: Kỹ sư hoặc Agent có xu hướng cắt xén thao tác, chỉ mở giao diện rồi chèn lệnh `time.sleep(25)` bị động, khiến video bị đóng băng (freeze) suốt hàng chục giây trong khi giọng đọc vẫn tiếp tục.

### 5.2. Bốn Nguyên Tắc Bất Biến Chống Lazy Code (4 Anti-Lazy Invariants)

```
+----------------------------------------------------------------------------------------------------+
|                         4 NGUYÊN TẮC BẤT BIẾN CHỐNG LAZY CODE TRONG SCREEN RECORDING               |
+------------------------------------+---------------------------------------------------------------+
| 1. ZERO PASSIVE SLEEP              | Nghiêm cấm time.sleep() thụ động > 2.5s. Mọi giây hình ảnh     |
|                                    | đều phải thể hiện thao tác có chủ đích.                       |
+------------------------------------+---------------------------------------------------------------+
| 2. INTERACTION DENSITY SCORE (IDS) | Điểm số mật độ thao tác bắt buộc đạt IDS >= 2.2               |
|                                    | Công thức: IDS = (Tổng số thao tác / Thời lượng s) * 10       |
+------------------------------------+---------------------------------------------------------------+
| 3. CUE-SHEET PARITY (1:1 MAPPING)  | Từng câu thoại TTS thuyết minh phải ánh xạ 1:1 với thao tác   |
|                                    | (Nói đến PO -> Mở PO; nói đến Kho -> Bấm smart button Kho)    |
+------------------------------------+---------------------------------------------------------------+
| 4. THREE-LEVEL VIEW DEPTH          | Bắt buộc đào sâu qua 3 tầng giao diện cấu trúc:               |
|                                    | [1. Kanban/List] -> [2. Form Detail] -> [3. Smart Button/Tab] |
+------------------------------------+---------------------------------------------------------------+
```

### 5.3. Thang Điểm Đánh Giá Mật Độ Thao Tác (Interaction Density Score - IDS)
Điểm số $IDS$ được tính toán tự động từ tệp nhật ký sự kiện `events.json`:
$$IDS = \frac{\text{Tổng số thao tác (Clicks + Fills + Highlights + TabSwitches + CardDrags)}}{\text{Thời lượng video (giây)}} \times 10$$
- **Gold Master Certified**: $IDS \ge 2.2$ (Trung bình cứ $\le 4.5\text{s}$ có ít nhất một thao tác chuyển động mới).
- **Warning Threshold**: $1.5 \le IDS < 2.2$.
- **Rejected (Lazy Code Detected)**: $IDS < 1.5$ hoặc xuất hiện bất kỳ khoảng rảnh rỗi (Idle Gap) nào $> 4.0\text{s}$.

---

## 6. Kiến Trúc 25-Thumbnail Mosaic Closing CTA & Cấu Trúc Thứ Tự Vàng

```
+----------------------------------------------------------------------------------------------------+
|                CẤU TRÚC 5 GIAI ĐOẠN ĐIỆN ẢNH VÀNG (ZENPHAM STRUCTURAL SEQUENCE)                     |
+----------------------------------------------------------------------------------------------------+
| [1. Cold Open Hook] -> [2. Logo Opener] -> [3. Technical Scenes] -> [4. Mosaic CTA] -> [5. Bridge]|
|       (0 - 3s)               (5.80s)             (Cốt lõi nghiệp vụ)       (8.00s 2K60)       (Outro)      |
+----------------------------------------------------------------------------------------------------+
```

### 6.1. Trật Tự Phân Cảnh Bất Biến (Structural Sequence Contract)
1. **Giai đoạn 1: Cold Open Hook ($t = 0.00\text{s} - 3.00\text{s}$)**: Bắt đầu ngay lập tức bằng một phát biểu sắc sảo về rủi ro chi phí, thảm họa an toàn hoặc nghịch lý thị trường nhằm giữ chân người xem trong 3 giây vàng đầu tiên. **TUYỆT ĐỐI CẤM đặt Logo Opener ở giây $00:00$**.
2. **Giai đoạn 2: Logo Opener ($5.80\text{s}$)**: Clip nhận diện thương hiệu Insilos 3D Sonic Brand Ident kèm tiếng mở màn hoành tráng, đặt tại vị trí thứ 2.
3. **Giai đoạn 3: Core Technical Scenes**: Trực quan hóa chi tiết các bước nghiệp vụ ERP/GRC theo quy tắc 3 tầng chiều sâu.
4. **Giai đoạn 4: 25-Thumbnail Mosaic Closing CTA ($8.00\text{s}$)**: Khung hình Outro đồng nhất thể hiện quy mô đồ sộ của toàn bộ hệ sinh thái giải pháp.
5. **Giai đoạn 5: Script Bridge Closing**: Câu chốt định hướng chuyển đổi số hoặc lời mời trải nghiệm thực tế.

### 6.2. Đặc Tả Khung Hình Outro 25-Thumbnail Mosaic
- **Độ phân giải chuẩn**: $2560 \times 1440$ (2K QHD) @ 60fps.
- **Thời lượng**: Đúng $8.00$ giây.
- **Bố cục Ma trận**: 5 cột $\times$ 5 hàng (Tổng cộng 25 thẻ video).
  * Kích thước mỗi card: $320 \times 180\text{ px}$, bo góc bán kính $10\text{px}$, khoảng cách đệm $14\text{px}$.
  * Huy hiệu tập: `T.01` đến `T.24` mang viền phát sáng Cyan Tech (`#38bdf8`), riêng tập kết thúc `FINALE` (Ep 25) mang viền Vàng Amber danh dự (`#fbbf24`).
- **Tính đồng nhất toàn diện**: Tất cả các tập trong chuỗi xuất bản bắt buộc sử dụng chung một chuẩn Closing CTA này, tạo nhận diện thương hiệu đẳng cấp xuyên suốt.

### 6.3. Tối Ưu Hóa Nguyên Tử Faststart Cho Trình Duyệt Web (`moov` Atom)
Để video có thể phát ngay lập tức trên Website Odoo và hạ tầng CDN mà không cần chờ tải hết toàn bộ tệp:
- Bắt buộc kích hoạt cờ dịch chuyển nguyên tử `moov` lên đầu tệp video:
  `ffmpeg -i input.mp4 -movflags +faststart output.mp4`
- Kiểm tra bằng cấu trúc byte: Vị trí của chuỗi byte `b'moov'` phải xuất hiện trước `b'mdat'` trong 10KB đầu tiên của tệp tin.

---

## 7. Ma Trận Kiểm Định Tự Động Hóa & Lệnh Thực Thi (Automated Verification)

Mọi video Gold Master và tệp nhật ký ghi hình phải được kiểm tra qua công cụ tự động `tools/audit_recording_standards_d2.py`:

```bash
python3 tools/audit_recording_standards_d2.py
```

### Tiêu Chuẩn Nghiệm Thu Của Script:
1. **Video Visual Quality**: Độ phân giải $1920 \times 1080$, Codec H.264, Faststart = YES.
2. **Audio Fidelity**: Tần số lấy mẫu $48,000\text{ Hz}$, Codec AAC Stereo (2 channels).
3. **Loudness Compliance**: Integrated Loudness $I \in [-15.0, -13.0]\text{ LUFS}$, True Peak $TP \le -1.0\text{ dBTP}$.
4. **Anti-Lazy Telemetry**: Điểm $IDS \ge 2.2$, không có idle gap nào vượt quá ngưỡng cho phép trên toàn bộ 12 kịch bản nghiệp vụ và phim HSE 75s.
5. **Exit Code**: Trả về `0` khi 100% các tiêu chí đạt chuẩn; trả về `1` nếu có bất kỳ vi phạm nào.
