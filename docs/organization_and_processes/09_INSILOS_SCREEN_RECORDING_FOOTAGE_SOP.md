# SOP-MEDIA-009: Quy Trình Vận Hành Chuẩn & Hướng Dẫn Sử Dụng Động Cơ Ghi Hình Màn Hình Tự Động Cấp Độ Điện Ảnh (`/insilos-screen-recording-footage`)

> **Mã quy trình (SOP Code):** `SOP-MEDIA-009` (`SOP-DGM-MEDIA-09`)  
> **Tên kỹ năng (Skill Identifier):** `/insilos-screen-recording-footage`  
> **Phiên bản (Version):** `2.0` (Tháng 10/2026 — Chuẩn hóa Cinema-Grade Headless Capture, 48kHz EBU R128 & Anti-Lazy-Code IDS Gate)  
> **Pháp nhân chủ quản (Legal Entity):** **CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGITAL MATE JOINT STOCK COMPANY — DIGIMATE JSC / DGM)** • **MST:** `0317958465` • **Mã ĐV BHXH:** `TZ0857G` • **Ký hiệu HĐĐT:** `1C26TAA`  
> **Địa chỉ trụ sở:** Số 11, Đường số 3, Khu dân cư CityLand, Phường Tân Mỹ, TP. Hồ Chí Minh, Việt Nam  
> **Phạm vi áp dụng (Scope):** Toàn bộ hoạt động sản xuất tư liệu ghi hình màn hình (*Screen Recording Walkthrough & B-Roll Footage*) trên **Hệ điều hành Doanh nghiệp Insilos** (`http://localhost:28069`), cổng thông tin `innoria.com`, `insilos.com`, chuỗi 12 Video Nghiệp vụ Công nghiệp B2B, và tài liệu hướng dẫn đào tạo khách hàng.  
> **Chủ quản quy trình (Process Owners):** Giám đốc Công nghệ (CTO), Giám đốc Sản phẩm (CPO), Trưởng bộ phận Truyền thông & Kỹ xảo Kỹ thuật số (Head of Digital Media & Brand Engineering).

---

## 1. Mục Đích & Tổng Quan Kiến Trúc (Executive Overview & System Architecture)

### 1.1. Mục Đích Vận Hành (Operational Purpose)
Kỹ năng **`/insilos-screen-recording-footage`** là hệ thống ghi hình màn hình tự động hóa cấp độ điện ảnh (*Cinema-Grade Automated Screen Recording Engine*) được thiết kế chuyên biệt cho **Nền tảng Doanh nghiệp Insilos (`http://localhost:28069`)**. Công cụ giải quyết triệt để 4 bài toán chất lượng khi sản xuất video giới thiệu phần mềm B2B:
1. **Loại bỏ hoàn toàn giao diện trình duyệt cá nhân (Zero Browser Chrome):** Ghi hình trực tiếp khung nhìn DOM nội bộ (`1920x1080` Full HD hoặc `2560x1440` 2K QHD) thông qua Playwright Headless Chromium — tuyệt đối không xuất hiện thanh địa chỉ URL, thanh tab, dấu trang (bookmarks), tiện ích mở rộng (extensions) hay thông tin tài khoản cá nhân.
2. **Tiêm kỹ xảo thị giác thời gian thực (Real-Time DOM VFX Injection):** Tự động hiển thị con trỏ ảo công nghệ cao (*Virtual Luxury Cursor* `24px` Cyan `#00f0ff`), sóng xung kích khi click chuột (*Click Ripple Shockwave* `0.6s`), và hào quang tiêu điểm (*Element Spotlight Halo* `35px`) làm nổi bật các chỉ số tài chính/vận hành trọng yếu.
3. **Đồng bộ âm thanh xúc giác phòng thu (Tactile 48kHz Stereo SFX & EBU R128 Mastering):** Tự động tổng hợp 6 hiệu ứng âm thanh xúc giác bằng toán học thuần túy (`48,000 Hz` Stereo PCM 16-bit) và ghép nối chính xác đến từng mili-giây theo nhật ký sự kiện tương tác (`*_events.json`), chuẩn hóa âm lượng đầu ra theo tiêu chuẩn truyền hình **EBU R128** (`-16.0 LUFS`, True Peak $\le -1.5\text{ dBTP}$).
4. **Kiểm soát mật độ tương tác chống "Lazy Code" (Anti-Lazy-Code Interaction Density Gate):** Ngăn chặn triệt để hiện tượng đứng hình thụ động (`time.sleep` kéo dài) trong các chuỗi video nghiệp vụ thông qua bộ kiểm định tự động `audit_screen_recording_density.py`.

### 1.2. Sơ Đồ Kiến Trúc Luồng Sản Xuất 4 Tầng (4-Stage Production Pipeline)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                KIẾN TRÚC ĐỘNG CƠ /insilos-screen-recording-footage (SOP-MEDIA-009)                │
├────────────────────────┬─────────────────────────┬────────────────────────┬───────────────────────┤
│ TẦNG 1: SFX SYNTHESIS  │ TẦNG 2: HEADLESS CAPTURE│ TẦNG 3: VFX/SFX MASTER │ TẦNG 4: QUALITY GATE  │
│ generate_sfx_library.py│ recorder.py             │ vfx_sfx_composer.py    │ audit_screen_         │
│                        │ recorder_business_...py │                        │ recording_density.py  │
├────────────────────────┼─────────────────────────┼────────────────────────┼───────────────────────┤
│ • Tổng hợp toán học    │ • Chromium Headless     │ • Đọc *_events.json    │ • Kiểm tra >= 8 events│
│   NumPy + SciPy WAV    │ • Session Cookie Bypass │ • Ghép adelay mili-giây│ • Max Idle Gap <= 4.0s│
│ • 48kHz Stereo 16-bit  │ • Inject Cursor/Ripple/ │ • Hòa âm amix 6 kênh   │ • Điểm mật độ tương   │
│ • Chuẩn đỉnh -1.5 dBFS │   Spotlight Halo DOM JS │ • Chuẩn hóa EBU R128   │   tác IDS >= 2.0      │
│ • 6 tệp SFX chuẩn hóa  │ • Xuất MP4 H.264 CRF 18 │   (-16 LUFS / -1.5dBTP)│ • Chặn xuất bản (Exit │
│   tại assets/sfx/*.wav │   + *_events.json       │ • Xuất *_mastered.mp4  │   Code 1) nếu vi phạm │
└────────────────────────┴─────────────────────────┴────────────────────────┴───────────────────────┘
```

---

## 2. Năm Quy Chuẩn Kỹ Thuật Bất Biến (Five Sovereign Core Invariants)

### 2.1. Quy Chuẩn 1 — Khử Hoàn Toàn Khung Trình Duyệt (Zero Browser Chrome & Pure Viewport Isolation)
- Khởi chạy Chromium ở chế độ Headless với bộ cờ cô lập khung hình:
  - `--no-sandbox`, `--disable-setuid-sandbox`, `--hide-scrollbars`, `--disable-infobars`
  - `--force-device-scale-factor=1`, `--disable-background-timer-throttling`, `--disable-renderer-backgrounding`
- Khung hình ghi nhận 100% là bề mặt giao diện phẳng, sắc nét của hệ điều hành **Insilos** ở độ phân giải chuẩn `1920x1080` (hoặc `2560x1440`), định dạng màu `yuv420p`, codec `libx264`, hệ số chất lượng `CRF 18`.
- Tự động xác thực phiên làm việc (`session_id`) qua JSON-RPC `/web/session/authenticate` và nạp thẳng vào cookie trình duyệt để bỏ qua màn hình đăng nhập thủ công khi quay các phân cảnh nghiệp vụ nội bộ.

### 2.2. Quy Chuẩn 2 — Kỹ Xảo Thị Giác Tương Tác (Injected DOM VFX Layer)
Ngay sau khi tải trang (`domcontentloaded` / `networkidle`), động cơ tiêm gói JavaScript `INJECTED_CURSOR_VFX_JS` vào DOM để cung cấp 4 cơ chế thị giác:

| Thành phần VFX | Hàm / Phần tử DOM | Đặc tả Kỹ thuật & Hiệu ứng Thị giác |
| :--- | :--- | :--- |
| **1. Con trỏ Ảo Cao cấp** (*Virtual Luxury Cursor*) | `#insilos-virtual-cursor` | Đường kính `24px`, tâm trắng `6px`, viền `#00f0ff` dày `2px`, quầng sáng `radial-gradient` và `box-shadow: 0 0 16px #00d2ff`, nội suy chuyển động mượt theo hàm `cubic-bezier(0.25, 1, 0.5, 1)`. |
| **2. Sóng Xung Kích Click** (*Click Ripple Shockwave*) | `window.__insilos_trigger_ripple(x, y)` | Sinh vòng tròn xung kích `10px` tại tọa độ `(x, y)` với viền `#00ffcc`, phóng đại `scale(1) -> scale(7.5)` và mờ dần trong `0.6s` (`cubic-bezier(0.1, 0.8, 0.3, 1)`). |
| **3. Hào Quang Tiêu Điểm** (*Element Spotlight Halo*) | `window.__insilos_highlight_element(selector, glowColor)` | Gắn lớp `.insilos-spotlight-active`, tạo viền `3px solid <glowColor>` và quầng sáng kép `0 0 35px <glowColor>`, đồng thời trả về tọa độ tâm `{x, y, width, height, top, left}` để phục vụ đóng khung. |
| **4. Xóa Hào Quang** (*Clear Highlight*) | `window.__insilos_clear_highlight()` | Gỡ bỏ toàn bộ trạng thái `.insilos-spotlight-active` trước khi chuyển sang bước nghiệp vụ tiếp theo. |

### 2.3. Quy Chuẩn 3 — Thư Viện Âm Thanh Xúc Giác 48kHz & Chuẩn Hóa EBU R128 (Tactile SFX & Audio Mastering)
Toàn bộ 6 hiệu ứng âm thanh trong `/home/zen/.gemini/config/skills/insilos-screen-recording-footage/assets/sfx/` được tổng hợp bằng toán học thuần túy qua `scripts/generate_sfx_library.py` (không phụ thuộc mẫu âm thanh bên ngoài, đảm bảo 100% bản quyền thuộc Digimate JSC):

| Mã SFX (`sfx`) | Tên tệp WAV | Thời lượng | Đặc trưng Âm học & Toán học Tổng hợp | Ngữ cảnh Nghiệp vụ Áp dụng |
| :--- | :--- | :---: | :--- | :--- |
| `sfx_click` | `sfx_click.wav` | `35 ms` | Sóng sin `3200 Hz` tắt dần nhanh ($\msup{e}{-220t}$) kết hợp xung nảy phụ `2400 Hz` tại `8 ms`. | Click mở ứng dụng, bấm nút xác nhận, đóng/mở hộp thoại. |
| `sfx_type` | `sfx_type.wav` | `45 ms` | Tổ hợp tạp âm hồng (*pink noise burst*), âm trầm cơ học `420 Hz` và âm nảy `4800 Hz` (mô phỏng trục phím cơ Cherry MX Blue). | Nhập liệu biểu mẫu B2B, điền thông tin khách hàng, gõ tìm kiếm. |
| `sfx_scanner_beep` | `sfx_scanner_beep.wav` | `85 ms` | Sóng sin thuần khiết nốt `A6` (`1760 Hz`) với đường bao tăng/giảm mượt (`5 ms` attack, `20 ms` decay). | Quét mã vạch lô/serial trong Kho (WMS) và Xưởng sản xuất (Shop Floor). |
| `sfx_whoosh` | `sfx_whoosh.wav` | `350 ms` | Quét tần số điều biến (`400 Hz -> 150 Hz`) qua đường bao hình chuông Gauss với độ trễ âm thanh nổi `8 ms` giữa kênh Trái/Phải. | Chuyển cảnh màn hình, cuộn trang mượt, bật vùng sáng Spotlight. |
| `sfx_chime` | `sfx_chime.wav` | `1,200 ms` | Hợp âm trưởng pha lê 3 nốt `C6` (`1046.50 Hz`) + `E6` (`1318.51 Hz`) + `G6` (`1567.98 Hz`) ngân vang. | Hoàn tất nghiệm thu, cân bằng tải Gantt, xác nhận sổ cái cân đối. |
| `sfx_cash` | `sfx_cash.wav` | `1,000 ms` | Chuông kim khí kép (`2489.0 Hz` + `3322.4 Hz`) kèm âm ma sát kim loại cao tần `6500 Hz` trong `40 ms` đầu. | Duyệt đơn mua hàng giá trị lớn, khóa sổ tài chính, phát hành HĐĐT Nghị định 70/2025 (`1C26TAA`). |

**Chuẩn hóa âm lượng đầu ra (FFmpeg Filter Complex trong `vfx_sfx_composer.py`):**
- Mỗi sự kiện tại thời điểm $t$ (giây) được dịch chuyển chính xác bằng bộ lọc `adelay={ts_ms}|{ts_ms},volume=0.85`.
- Tất cả các kênh SFX được trộn qua `amix=inputs=N:duration=longest:normalize=0` và đưa qua bộ chuẩn hóa âm lượng phát sóng **EBU R128**:
  ```text
  loudnorm=I=-16.0:TP=-1.5:LRA=7.0
  ```
- Luồng âm thanh đầu ra được mã hóa chuẩn **AAC `256 kbps`, tần số lấy mẫu `48,000 Hz` Stereo**.

### 2.4. Quy Chuẩn 4 — Độ Trung Thực Thị Giác Máy Tính & Nội Suy 60 FPS (Computer Vision Fidelity Standard)
Đối với các phân cảnh quay tính năng AI Thị giác Máy tính (*AI CCTV, Nhận diện Bảo hộ Lao động PPE, Kiểm tra Lỗi Sản phẩm*):
1. **Cấm tuyệt đối Bounding Box tĩnh (Zero Static Hallucinated Boxes):** Không bao giờ dùng tọa độ CSS phần trăm cố định (`top/left` tĩnh) đè lên video có đối tượng chuyển động.
2. **Nội suy chuyển động 60 FPS liên tục (60 FPS Sub-Pixel Keyframe Interpolation):** Trong mỗi khung hình `requestAnimationFrame`, tọa độ hộp giới hạn được nội suy tuyến tính giữa hai mốc thời gian $[t_1, t_2]$ theo thời gian thực của video:
   $$\alpha = \frac{t - t_1}{t_2 - t_1}, \qquad \text{box}(t) = \text{box}_1 + \alpha \cdot (\text{box}_2 - \text{box}_1)$$
3. **Tính trung thực ngữ nghĩa (Truth-in-Detection Parity):** Nhãn nhận diện phải phản ánh đúng 100% thực tế thị giác trong khung hình (ví dụ: công nhân không đội mũ bảo hộ bắt buộc hiển thị cảnh báo đỏ `[VIOLATION: NO HELMET]`, tuyệt đối không gán nhãn giả `[HELMET // 99.x%]`).
4. **Luồng Telemetry HUD Thời gian thực:** Hiển thị tọa độ `[X, Y, W, H]`, độ trễ suy luận biến thiên tự nhiên (`11.5 ms – 13.8 ms`), tốc độ khung hình `60.0 FPS` và mã thời gian chính xác đến mili-giây.
5. **Kỷ luật Thương hiệu Tuyệt đối (Strict Sovereign Branding):** Toàn bộ giao diện, nhãn, URL và thuyết minh chỉ sử dụng thương hiệu **Insilos**, **Insilos ERP**, **Vertical Resilience (GRC)**, **Mojo AI**, **Zencode Ent**, **Innoria** — nghiêm cấm để lộ tên nền tảng lõi bên dưới.

### 2.5. Quy Chuẩn 5 — Tiêu Chuẩn Chống "Lazy Code" & Điểm Mật Độ Tương Tác ($IDS \ge 2.0$)
Khi sản xuất chuỗi nhiều video nghiệp vụ liên tiếp (từ kịch bản 1 đến kịch bản $N$), kỹ sư và AI Agent phải tuân thủ 4 nguyên tắc chống suy giảm chất lượng (*Anti-Fatigue Decay Invariants*):
1. **Zero Passive Sleep Invariant:** Nghiêm cấm dùng `time.sleep()` thụ động kéo dài quá `2.5s`–`4.0s` để độn thời lượng video.
2. **Three-Level View Depth:** Mỗi kịch bản phải đi qua tối thiểu 3 tầng chiều sâu giao diện:
   $$\text{[1. Home / Kanban / List View]} \longrightarrow \text{[2. Form Detail View]} \longrightarrow \text{[3. Smart Button / Status / Line Items]}$$
3. **Công thức Điểm Mật Độ Tương Tác (Interaction Density Score — $IDS$):**
   $$IDS = \frac{N_{\text{events}}}{T_{\text{duration}}} \times 10.0$$
   Trong đó $N_{\text{events}}$ là tổng số sự kiện tương tác có chủ đích được ghi nhận trong `*_events.json` và $T_{\text{duration}}$ là thời lượng video (giây).
4. **Ngưỡng Kiểm định Tự động (`audit_screen_recording_density.py`):**
   - Số sự kiện tối thiểu: $N_{\text{events}} \ge 8$ sự kiện / video.
   - Khoảng trống chờ tối đa giữa 2 sự kiện liên tiếp: $\text{Max Idle Gap} \le 4.0\text{s}$.
   - Điểm mật độ tương tác chuẩn Gold Master: $IDS \ge 2.0$ (Khuyến nghị $IDS \ge 2.2$).

---

## 3. Cấu Trúc Thư Mục & Danh Mục Thành Phần Kỹ Thuật (Directory Structure & File Inventory)

```text
/home/zen/.gemini/config/skills/insilos-screen-recording-footage/
├── SKILL.md                                   # Đặc tả kỹ năng & quy chuẩn bất biến
├── assets/
│   └── sfx/                                   # Thư viện 6 tệp âm thanh xúc giác 48kHz Stereo PCM
│       ├── sfx_click.wav                      # Click chuột cơ học (0.035s, 3200Hz + 2400Hz bounce)
│       ├── sfx_type.wav                       # Gõ phím cơ Cherry MX (0.045s, pink noise + 420Hz/4800Hz)
│       ├── sfx_scanner_beep.wav               # Bíp máy quét mã vạch kho (0.085s, 1760Hz A6 sine)
│       ├── sfx_whoosh.wav                     # Lướt khí HUD / chuyển cảnh (0.350s, stereo FM sweep)
│       ├── sfx_chime.wav                      # Chuông pha lê nghiệm thu (1.200s, hợp âm C6-E6-G6)
│       └── sfx_cash.wav                       # Chuông kim khí phát hành HĐĐT (1.000s, 2489Hz + 3322Hz)
└── scripts/
    ├── generate_sfx_library.py                # Trình tổng hợp toán học 6 tệp WAV 48kHz Stereo
    ├── recorder.py                            # Động cơ ghi hình trang 3D Showcase & kịch bản tổng quát
    ├── recorder_business_scenarios.py         # Động cơ ghi hình 12 kịch bản nghiệp vụ (VID_01_CRM..VID_12_MKT)
    ├── vfx_sfx_composer.py                    # Trình ghép nối SFX mili-giây & chuẩn hóa âm lượng EBU R128
    └── audit_screen_recording_density.py      # Bộ kiểm toán tự động chống Lazy Code (IDS >= 2.0, Gap <= 4.0s)
```

**Thư mục xuất bản mặc định (Default Output Directory):**
- `/home/zen/hermes-agent/output/insilos_footage/`
  - Video thô đã nén H.264 (`CRF 18`): `insilos_screen_<SCENARIO>.mp4` hoặc `<output_stem>.mp4`
  - Nhật ký sự kiện & tọa độ tiêu điểm: `insilos_screen_<SCENARIO>_events.json` hoặc `<output_stem>_events.json`
  - Video hoàn chỉnh đã ghép SFX & chuẩn hóa EBU R128: `*_mastered.mp4`

---

## 4. Hướng Dẫn Vận Hành Chi Tiết Từng Bước (Step-by-Step Operational Guide)

### Bước 0: Kiểm Tra Tiền Điều Kiện & Khởi Tạo Thư Viện Âm Thanh 48kHz (Pre-Flight & SFX Synthesis)

1. **Kiểm tra máy chủ Insilos đang hoạt động tại cổng `28069`:**
   ```bash
   curl -sI http://localhost:28069/web/login | head -n 5
   ```
2. **Tạo hoặc làm mới bộ 6 tệp âm thanh chuẩn `48,000 Hz` Stereo PCM:**
   ```bash
   python3 /home/zen/.gemini/config/skills/insilos-screen-recording-footage/scripts/generate_sfx_library.py
   ```
   *Kết quả kỳ vọng:* Sinh đủ 6 tệp `.wav` (`sfx_click.wav`, `sfx_type.wav`, `sfx_scanner_beep.wav`, `sfx_whoosh.wav`, `sfx_chime.wav`, `sfx_cash.wav`) chuẩn hóa đỉnh `-1.5 dBFS` tại `/home/zen/.gemini/config/skills/insilos-screen-recording-footage/assets/sfx/`.

---

### Bước 1A: Ghi Hình Giao Diện 3D Showcase & Trải Nghiệm Tương Tác (`recorder.py`)

Sử dụng `recorder.py` khi cần quay kịch bản trình diễn trang `/showcase-3d` (cuộn Hero, mở Modal Video 4K, chuyển kênh Robot Hàn / Cảng Cát Lái, làm nổi bật cơ hội B2B 18,6 tỷ VNĐ và điền biểu mẫu đăng ký tự động):

```bash
/home/zen/hermes-agent/.venv/bin/python \
  /home/zen/.gemini/config/skills/insilos-screen-recording-footage/scripts/recorder.py \
  --url "http://localhost:28069" \
  --scenario "showcase_3d" \
  --output "insilos_footage_showcase_3d" \
  --width 1920 \
  --height 1080
```

**Tham số dòng lệnh (`recorder.py`):**
- `--url`: Địa chỉ gốc của hệ thống Insilos (mặc định: `http://localhost:28069`).
- `--scenario`: Mã kịch bản cần quay (mặc định: `showcase_3d`).
- `--output`: Tên tệp đầu ra không kèm phần mở rộng (mặc định: `insilos_footage_showcase_3d`).
- `--width`: Chiều rộng khung hình tính bằng pixel (mặc định: `1920`, hỗ trợ `2560` cho 2K QHD).
- `--height`: Chiều cao khung hình tính bằng pixel (mặc định: `1080`, hỗ trợ `1440` cho 2K QHD).

**Đầu ra:**
- Video H.264: `/home/zen/hermes-agent/output/insilos_footage/insilos_footage_showcase_3d.mp4`
- Tệp sự kiện JSON: `/home/zen/hermes-agent/output/insilos_footage/insilos_footage_showcase_3d_events.json`

---

### Bước 1B: Ghi Hình 12 Kịch Bản Nghiệp Vụ Doanh Nghiệp (`recorder_business_scenarios.py`)

Sử dụng `recorder_business_scenarios.py` để tự động đăng nhập phiên quản trị, điều hướng từ màn hình chính `/insilos` và ghi hình từng kịch bản trong chuỗi **12 Video Nghiệp vụ Công nghiệp B2B**:

```bash
/home/zen/hermes-agent/.venv/bin/python \
  /home/zen/.gemini/config/skills/insilos-screen-recording-footage/scripts/recorder_business_scenarios.py \
  --scenario "VID_02_PUR"
```

**Bảng Danh Mục 12 Kịch Bản Nghiệp Vụ Chuẩn (`VID_01_CRM` – `VID_12_MKT`):**

| Mã Kịch bản (`--scenario`) | Phân hệ Insilos | Nội dung Nghiệp vụ Trọng tâm & Điểm Nhấn Thị giác | Tệp Video & Events Đầu ra |
| :--- | :--- | :--- | :--- |
| `VID_01_CRM` | **CRM B2B** | Quản trị đường ống cơ hội B2B công nghiệp, kéo thả cơ hội Tân Cảng SNP `18,675 tỷ VNĐ`. | `insilos_screen_VID_01_CRM.mp4` |
| `VID_02_PUR` | **Purchase** | Phê duyệt Đơn mua hàng `25 tấn thép SS400 Hòa Phát` (`537.000.000 VNĐ`) & khóa sổ tài chính. | `insilos_screen_VID_02_PUR.mp4` |
| `VID_03_INV` | **Inventory (WMS)** | Truy vết lô & số Serial cáp `CADIVI` và vi mạch `ARM Cortex-M4` tại kho `WH/Stock` kèm tiếng `sfx_scanner_beep`. | `insilos_screen_VID_03_INV.mp4` |
| `VID_04_BOM` | **Manufacturing (BOM)** | Phân rã Định mức Nguyên vật liệu đa cấp (*Multi-Level BOM*) xe nâng điện `V-LIFT 2500E`. | `insilos_screen_VID_04_BOM.mp4` |
| `VID_05_PLN` | **Planning (MRP Gantt)** | Điều độ sản xuất & cân bằng tải biểu đồ Gantt giữa trạm cắt CNC Plasma và Robot Hàn. | `insilos_screen_VID_05_PLN.mp4` |
| `VID_06_SFL` | **Shop Floor Tablet** | Giao diện máy tính bảng xưởng sản xuất (*Shop Floor Terminal*), bấm giờ thực tế & đo chỉ số OEE `92.5%`. | `insilos_screen_VID_06_SFL.mp4` |
| `VID_07_FLT` | **Fleet Telematics** | Quản lý đội xe đầu kéo hạng nặng `51C-888.99`, đồng bộ công-tơ-mét và lịch sử đăng kiểm. | `insilos_screen_VID_07_FLT.mp4` |
| `VID_08_FUL` | **Fuel & EV Energy** | Phân tích chi phí nhiên liệu Diesel `PVOIL` so với trạm sạc xe điện `VinFast EV`. | `insilos_screen_VID_08_FUL.mp4` |
| `VID_09_LOG` | **Unified Operations** | Điều phối vận tải đa phương thức & vận đơn container `40ft` từ Cảng Cát Lái đi KCN VSIP Bình Dương. | `insilos_screen_VID_09_LOG.mp4` |
| `VID_10_SAL` | **Sales & E-Invoice** | Hợp đồng thương mại `THACO Chu Lai` (`2,295 tỷ VNĐ`) & phát hành Hóa đơn điện tử chuẩn Nghị định 70/2025 (`1C26TAA`). | `insilos_screen_VID_10_SAL.mp4` |
| `VID_11_ACC` | **Accounting (VAS TT200)** | Sổ cái kế toán tổng hợp chuẩn Thông tư 200/2014/TT-BTC & quy đổi đa tiền tệ tự động (`25.400 VNĐ/USD`). | `insilos_screen_VID_11_ACC.mp4` |
| `VID_12_MKT` | **Marketing Automation** | Tự động hóa tiếp thị B2B đa điểm chạm (*Multi-touch Attribution*) & nuôi dưỡng cơ hội tự động. | `insilos_screen_VID_12_MKT.mp4` |

**Chạy hàng loạt toàn bộ 12 kịch bản (Batch Execution):**
```bash
for code in VID_01_CRM VID_02_PUR VID_03_INV VID_04_BOM VID_05_PLN VID_06_SFL \
            VID_07_FLT VID_08_FUL VID_09_LOG VID_10_SAL VID_11_ACC VID_12_MKT; do
  /home/zen/hermes-agent/.venv/bin/python \
    /home/zen/.gemini/config/skills/insilos-screen-recording-footage/scripts/recorder_business_scenarios.py \
    --scenario "$code"
done
```

---

### Bước 2: Hòa Âm Xúc Giác SFX & Mastering Chuẩn EBU R128 (`vfx_sfx_composer.py`)

Sau khi có tệp `.mp4` và tệp nhật ký sự kiện `*_events.json`, chạy `vfx_sfx_composer.py` để ghép âm thanh xúc giác chính xác theo từng mốc mili-giây và chuẩn hóa âm lượng `-16.0 LUFS`:

```bash
/home/zen/hermes-agent/.venv/bin/python \
  /home/zen/.gemini/config/skills/insilos-screen-recording-footage/scripts/vfx_sfx_composer.py \
  --events "/home/zen/hermes-agent/output/insilos_footage/insilos_footage_showcase_3d_events.json" \
  --output "/home/zen/hermes-agent/output/insilos_footage/insilos_footage_showcase_3d_mastered.mp4"
```

**Tham số dòng lệnh (`vfx_sfx_composer.py`):**
- `--events` *(bắt buộc)*: Đường dẫn tới tệp JSON chứa danh sách sự kiện và đường dẫn `video_file` gốc.
- `--output` *(bắt buộc)*: Đường dẫn tệp `.mp4` Master đầu ra.
- `--no-zoom` *(tùy chọn)*: Tắt chế độ thu phóng khung hình động khi chỉ cần ghép âm thanh SFX giữ nguyên tỷ lệ khung hình 1:1.

---

### Bước 3: Kiểm Toán Mật Độ Tương Tác Chống "Lazy Code" (`audit_screen_recording_density.py`)

Trước khi nghiệm thu hoặc đưa vào biên tập video hoàn chỉnh, bắt buộc chạy bộ kiểm toán mật độ tương tác:

```bash
python3 /home/zen/.gemini/config/skills/insilos-screen-recording-footage/scripts/audit_screen_recording_density.py \
  --dir "/home/zen/hermes-agent/output/insilos_footage" \
  --output "/home/zen/hermes-agent/output/insilos_footage/density_audit_report.json"
```

- Nếu toàn bộ 12 kịch bản đạt chuẩn ($N_{\text{events}} \ge 8$, $\text{Max Gap} \le 4.0\text{s}$, $IDS \ge 2.0$), công cụ trả về **Exit Code `0`** (`✓ ALL 12 RECORDINGS PASSED THE ANTI-LAZY-CODE GOLD STANDARD!`).
- Nếu bất kỳ kịch bản nào bị thiếu sự kiện hoặc có khoảng nghỉ thụ động $> 4.0\text{s}$, công cụ trả về **Exit Code `1`** (`✗ CRITICAL: LAZY CODE DETECTED IN RECORDINGS!`) và xuất báo cáo chi tiết vào tệp JSON.

---

## 5. Cấu Trúc Dữ Liệu Nhật Ký Sự Kiện (`*_events.json` Schema Specification)

Mỗi bản ghi hình sinh ra một tệp метаdata JSON tuân thủ lược đồ chuẩn sau để liên thông giữa tầng Playwright Capture và tầng FFmpeg Composer:

```json
{
  "scenario": "VID_02_PUR",
  "video_file": "/home/zen/hermes-agent/output/insilos_footage/insilos_screen_VID_02_PUR.mp4",
  "resolution": [1920, 1080],
  "total_events": 9,
  "events": [
    {
      "timestamp": 1.642,
      "sfx": "sfx_whoosh",
      "description": "Spotlight App Tile: Purchase",
      "zoom": 1.15,
      "crop_box": {
        "x": 480.0,
        "y": 320.0,
        "width": 180.0,
        "height": 160.0
      }
    },
    {
      "timestamp": 2.851,
      "sfx": "sfx_click",
      "description": "Click App Tile: Purchase",
      "zoom": 1.0,
      "crop_box": null
    }
  ]
}
```

---

## 6. Hướng Dẫn Mở Rộng Kịch Bản Mới (Developer Extension Guide)

Khi cần bổ sung kịch bản ghi hình mới (ví dụ: `VID_13_GRC` cho phân hệ Quản trị Rủi ro & Tuân thủ hoặc `VID_14_HRM` cho Bảng lương VCB DigiBiz):

1. **Định nghĩa phương thức `_exec_<scenario_code_lower>(self, page)` trong `InsilosBusinessScenarioRecorder`:**
   ```python
   def _exec_vid_13_grc(self, page):
       """VID_13_GRC: Vertical Resilience ISO 27001/27701 & PDPD Audit Trail"""
       self._prepare_insilos_home(page)
       self._click_app_tile(page, "Vertical GRC")

       time.sleep(1.8)
       page.evaluate(INJECTED_CURSOR_VFX_JS)
       self.log_event("sfx_whoosh", "Vertical GRC Risk Register Loaded", zoom=1.0)

       # Tầng 1 -> Tầng 2: Chọn dòng hồ sơ rủi ro đầu tiên
       row = page.locator(".o_data_row").first
       if row.count() > 0:
           box = row.bounding_box()
           row.evaluate("el => window.__insilos_highlight_element(el, '#00ffcc')")
           self.log_event("sfx_whoosh", "Highlight ISO 27701 Control Matrix", zoom=1.2, crop_box=box)
           time.sleep(1.4)
           page.evaluate(f"__insilos_trigger_ripple({box['x'] + box['width']/2}, {box['y'] + box['height']/2})")
           self.log_event("sfx_click", "Open Risk Record Detail")
           row.click()
           time.sleep(2.0)

       # Tầng 3: Kiểm tra trạng thái phê duyệt & khóa sổ kiểm toán
       page.evaluate(INJECTED_CURSOR_VFX_JS)
       stat = page.locator(".o_statusbar_status, .o_form_sheet").first
       if stat.count() > 0:
           box_stat = stat.bounding_box()
           stat.evaluate("el => window.__insilos_highlight_element(el, '#00d2ff')")
           self.log_event("sfx_chime", "Verify Immutable Audit Trail Seal", zoom=1.25, crop_box=box_stat)
           time.sleep(2.0)
   ```
2. **Quy tắc bắt buộc khi viết kịch bản mới:**
   - Luôn gọi lại `page.evaluate(INJECTED_CURSOR_VFX_JS)` sau mỗi lần chuyển trang hoặc tải lại DOM lớn để đảm bảo lớp `#insilos-virtual-cursor` và các hàm `__insilos_*` luôn sẵn sàng.
   - Đảm bảo khoảng cách giữa hai lần gọi `self.log_event(...)` liên tiếp không bao giờ vượt quá `3.5s` (giữ $\text{Max Gap} \le 4.0\text{s}$ và $IDS \ge 2.0$).
   - Sử dụng bảng màu Spotlight chuẩn thương hiệu Insilos:
     - Cyan chủ đạo: `#00d2ff` / `#00f0ff` (điều hướng, thẻ tính năng, biểu đồ).
     - Emerald xác thực: `#00ffcc` (hoàn tất kiểm thử, duyệt đơn, an toàn kho).
     - Amber tài chính: `#ffaa00` (giá trị hợp đồng tỷ đồng, hóa đơn thuế, cảnh báo chi phí).

---

## 7. Danh Mục Kiểm Tra & Xử Lý Sự Cố Thườngặp (Pre-Flight Checklist & Troubleshooting)

| Triệu chứng / Lỗi (Symptom) | Nguyên nhân Gốc (Root Cause) | Biện pháp Khắc phục Chuẩn (Resolution) |
| :--- | :--- | :--- |
| **`Executable doesn't exist at /usr/bin/google-chrome`** | Máy chủ thiếu trình duyệt Google Chrome hoặc đường dẫn khác. | Kiểm tra `which google-chrome` hoặc tạo symlink tới `/usr/bin/google-chrome`. |
| **Màn hình bị chuyển hướng về `/web/login` khi quay kịch bản nghiệp vụ** | `get_session_id()` không lấy được `session_id` do sai tên DB hoặc thông tin xác thực. | Kiểm tra tên cơ sở dữ liệu mục tiêu (`insilos20_dev` / `odoo20_dev`) và đảm bảo dịch vụ tại `http://localhost:28069` đang phản hồi HTTP 200. |
| **Hiệu ứng Spotlight hoặc Ripple không hiển thị sau khi click chuyển trang** | Sự kiện điều hướng (`page.goto` hoặc SPA reload) làm mới `document.body`, xóa script VFX đã tiêm. | Gọi lại `page.evaluate(INJECTED_CURSOR_VFX_JS)` ngay sau khi view mới render xong. |
| **`audit_screen_recording_density.py` báo `REJECTED` (`Max Gap > 4.0s` hoặc `IDS < 2.0`)** | Kịch bản có lệnh `time.sleep()` quá dài hoặc thiếu tương tác ở phần giữa/cuối video. | Chia nhỏ thao tác thành chuỗi: *Spotlight phần tử (`sfx_whoosh`) -> Chờ `1.2s` -> Click kèm Ripple (`sfx_click`) -> Chuyển Tab / Smart Button -> Xác nhận (`sfx_chime`)*. |
| **Lỗi FFmpeg khi chạy `vfx_sfx_composer.py`** | Thiếu tệp `.wav` trong `assets/sfx/` hoặc đường dẫn `video_file` trong JSON không tồn tại. | Chạy lại `python3 scripts/generate_sfx_library.py` trước khi chạy `vfx_sfx_composer.py`. |

---

## 8. Bản Tóm Tắt Tiếng Anh (English Executive & Technical Reference Summary)

### 8.1. Purpose & Scope
**`SOP-MEDIA-009` (`/insilos-screen-recording-footage`)** defines the enterprise standard for producing cinema-grade, zero-chrome UI walkthroughs and B2B industrial marketing footage across the **Insilos Enterprise Platform (`http://localhost:28069`)** for **Digimate JSC (`MST: 0317958465`)** and **Innoria (`innoria.com` / `insilos.com`)**.

### 8.2. Core Technical Specifications
1. **Viewport Isolation:** Captures pure DOM frames (`1920x1080` FHD or `2560x1440` QHD, H.264 `CRF 18`, `yuv420p`) via headless Chromium with zero browser address bar, tabs, or user profile artifacts.
2. **Real-Time DOM VFX:** Injects `#insilos-virtual-cursor` (`24px` neon cyan `#00f0ff`), `__insilos_trigger_ripple(x, y)` (`0.6s` shockwave), and `__insilos_highlight_element(selector, glowColor)` (`35px` dual-glow spotlight).
3. **Mathematical 48kHz Stereo SFX & EBU R128 Mastering:** Synthesizes 6 zero-dependency stereo WAV cues (`sfx_click`, `sfx_type`, `sfx_scanner_beep`, `sfx_whoosh`, `sfx_chime`, `sfx_cash`) at `48,000 Hz` (`-1.5 dBFS` peak) and masters the final mix via FFmpeg `loudnorm=I=-16.0:TP=-1.5:LRA=7.0` (`256 kbps` AAC).
4. **60 FPS Computer Vision Tracking:** Mandates continuous `requestAnimationFrame` keyframe interpolation and strict visual semantic parity (zero static CSS bounding boxes).
5. **Anti-Lazy-Code Governance:** Enforces $\ge 8$ purposeful events per recording, maximum idle gap $\le 4.0\text{s}$, 3-level view depth (`Kanban/List -> Form -> Smart Button/Tab`), and Interaction Density Score $IDS = \frac{N_{\text{events}}}{T_{\text{duration}}} \times 10 \ge 2.0$.
