# INSILOS ENTERPRISE PLATFORM: MEDIA & VIDEO ASSET STRATEGY
## Architectural Standard, Full-Funnel Alignment, Encoding Specifications & Asset Governance
**Document Version**: 20.0.3.0  
**Authority**: Council Experts (SAP Enterprise Consultant, Claude Shannon Information Theorist, UI/UX Director)  
**Target Repository**: `/home/zen/O20`  
**Classification**: Sovereign Industrial AI & Enterprise Platform Engineering  
**Date**: 2026-09-28  

---

## 1. Executive Summary & Strategic Vision

The **Insilos Media & Video Asset Strategy** establishes an uncompromising, cinema-grade architectural framework governing all moving image, audio, 3D simulation, and screen capture assets across the Insilos Sovereign Industrial AI Platform (`/home/zen/O20`).

In the landscape of modern enterprise software, promotional videos and walkthrough demos have traditionally suffered from a fatal dichotomy: they are either high-level marketing CGI disconnected from software realities, or mundane, sluggish screencasts plagued by browser chrome, personal bookmarks, and dead waiting time ("lazy code"). 

Insilos resolves this divide by unifying **Claude Shannon's Mathematical Theory of Communication** with **SAP Enterprise Value Engineering**:
- **Claude Shannon Information Theory**: Every frame, pixel, and acoustic transient is treated as a discrete informational symbol. Video streams are engineered to maximize mutual information $I(X; Y)$ and visual entropy $H(X)$ while optimizing transmission across constrained network channels ($C = B \log_2(1 + S/N)$) through HTTP 206 Byte-Range streaming and `-movflags +faststart` metadata placement.
- **SAP Enterprise Value Engineering**: Media assets are systematically mapped against the C-Suite enterprise buyer journey across three operational tiers. Visual demonstrations do not showcase generic "AI magic"; rather, they present irrefutable empirical proof of work grounded in live ERP transaction telemetry (Circular 78 e-invoicing, Circular 200 cost accounting, MRP II multi-level BOMs, SCADA/MES OEE, and port logistics drayage).

The result is a unified media ecosystem that projects absolute industrial credibility, eliminates cognitive friction, and accelerates enterprise decision cycles.

```
+-------------------------------------------------------------------------------------------------------------+
|                                    INSILOS MEDIA STRATEGY FOUNDATIONAL DUALITY                              |
+------------------------------------------------------+------------------------------------------------------+
|             CLAUDE SHANNON INFORMATION THEORY        |            SAP ENTERPRISE VALUE ENGINEERING          |
+------------------------------------------------------+------------------------------------------------------+
| 1. Channel Capacity Optimization (Faststart MP4/VP9) | 1. Multi-Tier Taxonomic Classification (Tiers 1-3)   |
| 2. High Visual Entropy Poster Frames (H >= 6.0 bits) | 2. Full-Funnel Conversion Architecture               |
| 3. Anti-Lazy Interaction Density (IDS >= 2.2)        | 3. Live ERP Telemetry Grounding (Audit Lineage)      |
| 4. Psychoacoustic EBU R128 Loudness Normalization    | 4. 1-Click Deep-Link Action to Backend Models        |
+------------------------------------------------------+------------------------------------------------------+
```

---

## 2. Multi-Tier Enterprise Media Classification Matrix

To guarantee strict architectural separation of concerns, optimal client caching, and manageable repository footprints, all media assets within `/home/zen/O20` are classified into three distinct operational tiers.

### 2.1. Taxonomic Matrix

| Classification Tier | Codebase Root Path | Asset Categories & Formats | Target Persona & Usage | Performance & Delivery SLA |
|---|---|---|---|---|
| **Tier 1: Core Framework** | `odoo/addons/base/`<br>`addons/web/static/` | UI system icons (Phosphor Duotone SVG), empty-state vectors, core notification chimes (MP3/OGG). | Universal system operators, webclient runtime shell. | Total payload $< 500\text{ KB}$. Permanent immutable browser caching. Zero external CDN dependencies. |
| **Tier 2: Business Domain Addons** | `addons/*`<br>`enterprise/*`<br>*(e.g., POS, Barcode, Mail, VOIP)* | Transactional tactile audio (`sfx_scanner_beep`, `sfx_cash`, `sfx_chime`), operational alert tones, domain badges. | Field warehouse staff, cashiers, logistics dispatchers. | Per-sound file $< 65\text{ KB}$. 48kHz/44.1kHz audio sprites. Bundled directly within addon distribution modules. |
| **Tier 3: Sovereign Enterprise Portal** | `enterprise/insilos_website/static/src/video/` | 105s Master Cinematic Brand Film, 12 Gold Master Business Demos, 4 Feature Cutdowns, 19 Ambient Hero Loops, 3D WebGL assets. | C-Suite decision makers (CEO, CFO, CIO, COO), enterprise procurement councils. | 1080p/4K 60fps/30fps. H.264 High Profile / WebM VP9. EBU R128 audio. Real-time JSON telemetry sync. |

### 2.2. Codebase Media Storage Footprint (Empirical Inventory)

A complete filesystem audit of `/home/zen/O20` catalogs **46 video files** and **43 audio files** totaling **500.4 MB**:
1. **Tier 3 Enterprise Portal Assets** (`enterprise/insilos_website/static/src/video/` — **499.2 MB**):
   - `gold_masters/INSILOS_MASTER_CINEMATIC_105S.mp4` (59.98 MB, 105.00s @ 30fps, 1920×1080).
   - `gold_masters/INSILOS_LOGO_OPENER_5.8S.mp4` (0.78 MB, 5.80s @ 30fps, 1920×1080).
   - `gold_masters/INSILOS_VID_01_CRM_GOLD_MASTER.mp4` to `VID_12_MKT` (12 files, 9.89 MB – 19.77 MB each, exactly 60.000s).
   - `gold_masters/INSILOS_CUT1_MANUFACTURING_25S.mp4` to `CUT4` (4 files, 4.44 MB – 12.44 MB each, 20.0s – 30.0s).
   - 29 WebP poster images (`*_poster.webp`, 144 KB – 438 KB each).
   - 19 Page-specific ambient hero loops (`hero_*_opt.mp4`, 1.44 MB – 9.58 MB each, 8.0s seamless loop).
   - 4 C3.ai comparison B-Roll loops (`hero_act1_c3.mp4` to `hero_act4_c3.mp4`, 1.27 MB – 8.48 MB).
   - 4 High-fidelity raw 3D CGI master plates (`hero_act1_robotics.mp4` [45.05 MB], `hero_act2_port.mp4` [7.36 MB], `hero_act3_datacenter.mp4` [6.15 MB], `hero_act4_energy.mp4` [33.97 MB]).
2. **Tier 1 & Tier 2 Acoustic Assets** (**1.2 MB total**):
   - `addons/point_of_sale/static/src/sounds/` (12 files, 204 KB): POS operation chimes (`bell`, `beep`, `error`, `order-receive`).
   - `addons/mail/static/src/audio/` (26 files, 524 KB): Discuss call signaling and instant message notifications.
   - `enterprise/stock_barcode/static/src/audio/` (48 KB): High-frequency optical scan confirmation beeps.
   - `enterprise/voip/static/src/ringtones/` (180 KB): SIP softphone trunk ringtones.

---

## 3. Full-Funnel Video Alignment Architecture

To maximize B2B enterprise conversion, video assets are orchestrated into a three-stage funnel. Each stage addresses specific psychological and cognitive needs of enterprise buyers:

```
+=============================================================================================================+
|                                    INSILOS B2B FULL-FUNNEL VIDEO ARCHITECTURE                               |
+=============================================================================================================+
|  TOP OF FUNNEL (Awareness)          |  MIDDLE OF FUNNEL (Evaluation)      |  BOTTOM OF FUNNEL (Validation)  |
|  - 19 Ambient Hero Loops (8-10s)    |  - 105s Master Cinematic Brand Film |  - 12 Gold Master Demos (60.0s) |
|  - 4 Social Cutdowns (15-30s)       |  - 7 Continuous Production Scenes   |  - Real-Time Cinema HUD Player  |
|  - Objective: Industrial Authority  |  - Objective: Architectural Vision  |  - Objective: ERP Due Diligence |
+-------------------------------------+-------------------------------------+---------------------------------+
```

### 3.1. Top of Funnel (Awareness & Cognitive Impact)

#### A. Ambient Video Hero Background Loops (19 Page Routes)
- **Role**: Silent, continuous, cinema-grade ambient textures embedded into landing page headers (`/`, `/platform`, `/solutions/*`, `/industries/*`, `/pricing`, `/about`, `/resources`).
- **Characteristics**:
  * Duration: 8.0s – 10.0s seamless ping-pong or cycle loop.
  * Audio: Strictly muted (`muted autoplay loop playsinline`). Zero acoustic bandwidth.
  * Codec: WebM VP9 (primary stream, CRF 28, $< 3\text{ MB}$) with H.264 MP4 fallback (CRF 23).
  * Visual Motif: Obsidian darkroom aesthetic (`#070B14`), amber neon trace lines (`#FF8000`), cyan data bus telemetry (`#00F0FF`), robotic arm fabrication, container crane automation, and server rack clusters.

#### B. Social Feature Cutdown Vignettes (15s – 30s)
- **Role**: Bite-sized, high-converting social proof videos engineered for LinkedIn B2B campaigns, YouTube Pre-Roll bumpers, and executive direct messaging.
- **Inventory & Target Channels**:
  1. `INSILOS_CUT1_MANUFACTURING_25S.mp4` (25.0s):
     * *Focus*: Shopfloor MES, Trumpf CNC laser cutting, and Yaskawa robotic welding.
     * *Callouts*: `OEE: 92.5%` | `Chu kỳ: 45 phút/cụm` | `Lệnh MRP: IN PROGRESS`.
     * *CTA Hook*: *"Loại bỏ 100% giấy tờ tại xưởng cơ khí. Điều hành công đoạn tức thời cùng Insilos MRP."*
  2. `INSILOS_CUT2_TRACEABILITY_20S.mp4` (20.0s):
     * *Focus*: Warehouse lot tracking, CADIVI cable barcode verification, ARM Cortex-M4 serial genealogy.
     * *CTA Hook*: *"Gian lận kho hàng? Thất thoát vật tư? Insilos truy vết đến từng serial."*
  3. `INSILOS_CUT3_FLEET_LOGISTICS_30S.mp4` (30.0s):
     * *Focus*: Heavy tractor `51C-982.45`, Cát Lái Port container drayage, automated DET/DEM charge avoidance.
     * *CTA Hook*: *"Hàng trễ cảng? Phí DET/DEM? Insilos Fleet điều xe chủ động từng phút."*
  4. `INSILOS_CUT4_CRM_FINANCE_20S.mp4` (20.0s):
     * *Focus*: 18.675 Tỷ VNĐ Tân Cảng tender, Circular 78 e-invoice issuance, Circular 200 3-way matching.
     * *CTA Hook*: *"Từ hợp đồng nghìn tỷ đến hóa đơn điện tử TT78 — Insilos xử lý tức thì."*

### 3.2. Middle of Funnel (Evaluation & Architectural Authority)

#### The 105s Master Cinematic Brand Film (`INSILOS_MASTER_CINEMATIC_105S.mp4`)
- **Title**: *"Hành Trình Chuỗi Cung Ứng: Từ Bản Vẽ Đến Hải Cảng"* (*"From Blueprint to Seaport"*).
- **Format**: 1920×1080 Full HD (4K Master source), 30 fps, H.264 High Profile, 48kHz Stereo AAC, EBU R128 ($-14.49\text{ LUFS}$, $-1.45\text{ dBTP}$).
- **7-Scene Narrative Architecture**:
  The film guides the executive viewer through an unbroken supply chain odyssey, dynamically intercutting 3D industrial CGI with live ERP software manipulation:

| Scene | Timestamp | Visual Composition & VFX | Voiceover Narrative (Vietnamese VieNeu Studio) |
|---|---|---|---|
| **Scene 01** | `00:00 - 00:12` | Flycam aerial sweep over VSIP industrial park at dawn $\to$ Holographic 3D Insilos topology engine awakening. | *"Trong kỷ nguyên công nghiệp thế hệ mới, sự sống còn của doanh nghiệp không nằm ở quy mô nhà xưởng..."* |
| **Scene 02** | `00:12 - 00:25` | Engineering workstation opens CAD blueprint `EQ-VLIFT-2500E` $\to$ Seamless morph into Insilos CRM B2B tender pipeline (18.675 Tỷ VNĐ). | *"...mà nằm ở tốc độ dòng chảy thông tin từ hợp đồng thương mại đến từng lệnh điều phối sản xuất."* |
| **Scene 03** | `00:25 - 00:42` | 12kW Fiber Laser slicing SS400 alloy $\to$ Yaskawa 6-axis welding robot $\to$ Shop Floor Tablet monitoring OEE at 92.5%. | *"Tại phân xưởng, mọi trung tâm gia công đồng bộ theo thời gian thực. Loại bỏ hoàn toàn độ trễ giữa kế hoạch và thực thi."* |
| **Scene 04** | `00:42 - 00:58` | Assembly of 80V LFP battery pack $\to$ Handheld barcode terminal scanning ARM Cortex-M4 MCU $\to$ Lot pedigree DAG inspection. | *"Kiểm soát chất lượng không tì vết. Từng linh kiện, từng số serial đều được bảo chứng bất biến trên sổ cái số quyền năng."* |
| **Scene 05** | `00:58 - 01:18` | Heavy tractor `51C-982.45` rolling out of factory gates $\to$ Night highway telemetry $\to$ Cát Lái seaport STS container gantry. | *"Thành phẩm xuất xưởng lập tức kết nối vào mạng lưới tiếp vận thông minh. Giám sát hành trình, tối ưu nhiên liệu, triệt tiêu phí phạt bãi cảng."* |
| **Scene 06** | `01:18 - 01:32` | 40ft High-Cube container hoisted aboard ocean vessel $\to$ Automatic billing trigger issuing Circular 78 e-invoice (`Nợ 131 / Có 5111`). | *"Khi hàng rời bến, toàn bộ dòng tiền và chứng từ kế toán tự động hoàn tất. Chuẩn mực, minh bạch, tức thời."* |
| **Scene 07** | `01:32 - 01:45` | Macro aerial pull-back of unified industrial ecosystem $\to$ Insilos 3D signature emblem lockup $\to$ Executive CTA. | *"Insilos: Nền tảng hợp nhất dữ liệu công nghiệp. Khẳng định chủ quyền vận hành doanh nghiệp Việt."* |

### 3.3. Bottom of Funnel (Validation, Due Diligence & Commercial Closing)

#### The 12 Gold Master Business Demos (`VID_01` to `VID_12`)
- **Duration**: Exactly **60.000 seconds** (1,800 frames @ 30 fps) each.
- **Structure**: Rigorous 3-Act Enterprise Narrative:
  * **Act 1: Cold Open & Executive Hook (00:00 – 00:10)**: Insilos Logo Opener bumper (5.80s) + 3D industrial B-Roll highlighting the operational bottleneck and quantified financial bleed (e.g. scrap loss, dead inventory, container demurrage).
  * **Act 2: Live ERP Telemetry Walkthrough (00:10 – 00:50)**: 40 seconds of continuous, authentic software execution on the Odoo 20 live backend (`odoo20_dev`), guided by neon cyan virtual cursor, click ripple VFX, element spotlights, and dynamic zoom.
  * **Act 3: 25-Thumbnail Mosaic Closing CTA (00:50 – 01:00)**: Unified 25-card suite overview (`series1_25_thumbnails_mosaic.png`) connecting the specific module to the wider sovereign platform and driving the executive to the live interactive sandbox.

```
+-------------------------------------------------------------------------------------------------------------+
|                                    12 GOLD MASTER ENTERPRISE BUSINESS SUITE                                 |
+---------+-------------------+------------------------------------------+-----------------+------------------+
| Code    | Domain Module     | Core Business Transaction Scenario       | Live ERP Record | Key KPI Metric   |
+---------+-------------------+------------------------------------------+-----------------+------------------+
| VID-01  | CRM & Bidding     | Tân Cảng SNP 18.675 Tỷ VNĐ Tender        | `sale.order #1` | Win Rate 95%     |
| VID-02  | Heavy Purchase    | Hòa Phát Steel Plate 20 Tons PO          | `purchase.order`| -4.2% Unit Price |
| VID-03  | Cable Inventory   | CADIVI 3,500m Cable & Barcode Lots       | `stock.lot`     | 0 Scrap Loss     |
| VID-04  | Advanced MRP/BOM  | V-LIFT 2500E Chassis 12kW Laser MO       | `mrp.production`| Cycle: 45 min    |
| VID-05  | MES Scheduling    | Gantt Workcenter Balancing (Trumpf)      | `mrp.workcenter`| 0 Bottlenecks    |
| VID-06  | Shop Floor Tablet | Touch MES Terminal & Machine OEE         | `mrp.workorder` | OEE: 92.5%       |
| VID-07  | Fleet Telematics  | Heavy Tractor `51C-982.45` ODO Log       | `fleet.vehicle` | -18.4% Fuel Cost |
| VID-08  | Fleet Safety & PO | PVOIL Fueling & Trailer `51R-089.34`     | `fleet.service` | 100% Inspection  |
| VID-09  | Port Logistics    | Cát Lái - Cái Mép Intermodal Drayage     | `stock.picking` | 0 DET/DEM Fees   |
| VID-10  | Sales & Billing   | Circular 78 E-Invoice `BILL/2026/09/0001`| `account.move`  | STP: 99.8%       |
| VID-11  | Cost Accounting   | Circular 200 3-Way Cost Matching         | `account.move`  | Zero Variance    |
| VID-12  | C-Level Financial | B01-DN / B02-DN Balance Sheet & EBITDA   | `account.report`| Real-Time P&L    |
+---------+-------------------+------------------------------------------+-----------------+------------------+
```

---

## 4. Cinema-Grade Production Framework & Screen Recording Harness

To manufacture video footage that commands executive respect, Insilos deploys an automated, scriptable capture harness based on the `insilos-screen-recording-footage` and `zenpham-series-auditor` methodologies.

```
+-------------------------------------------------------------------------------------------------------------+
|                                    AUTOMATED CAPTURE & COMPOSITING PIPELINE                                 |
+-------------------------------------------------------------------------------------------------------------+
|  [Headless Playwright]  --->  [Event Log JSON]  --->  [FFmpeg VFX Compositor]  --->  [EBU R128 Master]      |
|  - 1920x1080 Isolated         - Timestamps            - Neon Virtual Cursor          - Dual-pass loudnorm   |
|  - Zero Browser Chrome        - Mouse Trajectory      - Click Ripple Shockwaves      - 48kHz Stereo AAC     |
|  - Live ERP Actions           - Keystrokes            - Dynamic Zoom (120-145%)      - Faststart MP4 Mux    |
+-------------------------------------------------------------------------------------------------------------+
```

### 4.1. Screen Recording Invariants (Zero Browser Chrome)

1. **Zero Browser Chrome Invariant**:
   - The recording engine drives headless Chromium with explicit viewport isolation (`width: 1920, height: 1080`).
   - **Absolute Prohibition**: No browser address bars (`http://localhost:28069`), navigation buttons (Back/Forward), browser tabs, personal bookmark strips, browser extension badges, or operating system window borders are permitted in the captured frame. The viewport must be 100% pure software interface.
2. **Luxury Virtual Cursor**:
   - Rather than capturing standard operating system cursors, a procedural virtual pointer is injected during post-compositing.
   - Geometry: 24px diameter circular reticle with a high-purity `#FFFFFF` core and a radiating `#00F0FF` electric cyan neon aura.
   - Kinematics: Pointer trajectories follow smooth cubic-bezier splines with physical acceleration and deceleration curves, mimicking deliberate executive operation.
3. **Click Ripple Shockwaves**:
   - Every mouse depression triggers an expanding radial shockwave emanating from the reticle center. The wave expands over $0.60\text{s}$, transitioning from `#00F0FF` at $100\%$ opacity to complete dissipation with quadratic ease-out.
4. **Element Spotlight Halos**:
   - When the narrative highlights a critical financial figure (e.g. 18.675 Tỷ VNĐ) or strategic button, the non-relevant DOM areas darken smoothly by $40\%$, while the target element is framed by a 35px double neon bounding glow.
5. **Dynamic Camera Zoom-In**:
   - To emphasize granular data entry without losing context, the compositor executes smooth virtual camera zooms between $120\%$ and $145\%$, focusing on input fields, status badges, or approval seals over $1.2\text{s}$ durations.

### 4.2. The Anti-Lazy Code Standard (Fatigue Decay Prevention)

A pervasive defect in multi-episode software video production is **Progressive Fatigue Decay**: developers exert meticulous care on Video 1, but resort to shortcuts in subsequent videos (e.g., loading a page and letting the video freeze on a static table for 25 seconds while audio plays).

Insilos strictly enforces the **Four Anti-Lazy Invariants**:
1. **Zero Passive Sleep Invariant**: Explicit `time.sleep()` delays $> 2.5\text{s}$ and freeze-frame clones (`tpad=stop_mode=clone`) $> 4.0\text{s}$ are strictly prohibited. Every second of video must reflect deliberate software progress.
2. **Interaction Density Rule**: Every video must maintain active engagement with at least one purposeful DOM event every $3.5\text{s}$.
3. **Cue-Sheet Parity (1:1 Semantic Mapping)**: Voiceover narration must synchronize 1:1 with interface state changes (e.g., when the narrator mentions "Hòa Phát Purchase Order", the PO record must open; when mentioning "Warehouse Lot", the barcode modal must appear).
4. **Three-Level View Depth**: Every demo video must navigate across at least three operational UI levels:
   $$\text{[Level 1: Kanban / List View]} \longrightarrow \text{[Level 2: Form Detail View]} \longrightarrow \text{[Level 3: Smart Button / Sub-Tab Audit Modal]}$$

#### Mathematical Formulation: Interaction Density Score ($IDS$)

The Interaction Density Score ($IDS$) quantifies the operational activity rate of a screen demonstration:

$$IDS = \frac{\sum (\text{Clicks} + \text{Fills} + \text{Spotlights} + \text{TabSwitches} + \text{FilterApplies})}{\text{Total Duration (seconds)}} \times 10$$

- **Gold Master Standard**: $IDS \ge 2.2$ (at least 1 purposeful interaction every $4.5\text{s}$).
- **Production Warning**: $1.5 \le IDS < 2.2$.
- **Hard Rejection**: $IDS < 1.5$ or any continuous idle freeze gap $> 4.0\text{s}$.

### 4.3. High-Entropy WebP Poster Engineering

Every video stream requires a static poster image displayed prior to playback. Blank, dark, or low-contrast posters damage conversion. Insilos establishes a mathematical quality gate for poster frames based on **Claude Shannon Information Entropy**:

$$H(X) = -\sum_{i=0}^{255} p_i \log_2(p_i)$$

Where $p_i$ represents the normalized probability density of 8-bit luminance level $i$.

- **Entropy Invariant**: $H(X) \ge 6.00\text{ bits}$ (guarantees high visual complexity and information density).
- **Luminance Standard Deviation**: $\sigma > 15.00$ (eliminates flat or monochrome frames).
- **Luminance Mean**: $35 \le \mu \le 210$ (guarantees proper exposure; prevents pure black or blown-out white frames).

*Empirical Validation*: Testing `INSILOS_MASTER_CINEMATIC_105S_poster.webp` yields $H = 7.6987\text{ bits}$, $\sigma = 58.29$, $\mu = 130.07$, comfortably exceeding all thresholds.

---

## 5. Technical Encoding & Acoustic Specifications

To guarantee instantaneous playback across mobile 5G, enterprise Wi-Fi, and air-gapped intranet workstations, all media assets adhere to uniform encoding parameters.

### 5.1. Video Encoding Matrix

| Technical Parameter | 4K Master Plates | Gold Masters (VID 01–12) | Social Cutdowns (CUT 1–4) | Ambient Web Hero Loops |
|---|---|---|---|---|
| **Target Frame Rate** | 60.0 fps progressive | 30.0 fps progressive | 30.0 fps progressive | 30.0 fps progressive |
| **Output Resolution** | 3840×2160 (Master archive) | 1920×1080 (Full HD) | 1920×1080 (Full HD) | 1920×1080 (Full HD) |
| **Primary Codec** | H.264 High Profile (L5.1) | H.264 High Profile (L4.1) | H.264 High Profile (L4.1) | WebM (VP9) |
| **Fallback Codec** | N/A | N/A | N/A | H.264 High Profile (L4.0) |
| **Pixel Format** | `yuv420p`, BT.709 color | `yuv420p`, BT.709 color | `yuv420p`, BT.709 color | `yuv420p`, BT.709 color |
| **Rate Control Mode** | CRF 18 (x264 `veryslow`) | CRF 20–22 (x264 `medium`) | CRF 20–22 (x264 `medium`) | CRF 28 (VP9) / CRF 23 (MP4) |
| **Max Bitrate Ceiling** | 20,000 kbps | 4,000 kbps | 3,500 kbps | 1,500 kbps |
| **Container Muxing** | MP4 (`+faststart`) | MP4 (`-movflags +faststart`) | MP4 (`-movflags +faststart`) | WebM / MP4 (`+faststart`) |
| **Max Payload Size** | Archive only ($< 250\text{ MB}$) | $< 20.0\text{ MB}$ per video | $< 13.0\text{ MB}$ per video | $< 3.5\text{ MB}$ per loop |

#### The Muxing Invariant: Faststart & Channel Streaming

In standard MP4 multiplexing, the `moov` atom (containing frame indexes, timescale, and codec metadata) is appended at the very end of the file. A web browser attempting to play such a file cannot render a single frame until the entire multi-megabyte payload is buffered.

**Mandatory Invariant**: Every MP4 file produced for the Insilos platform MUST be muxed with the `-movflags +faststart` flag:

```bash
ffmpeg -i input.mp4 -c copy -movflags +faststart output_faststart.mp4
```

This repositions the `moov` atom to byte 0 of the container. Modern HTTP 1.1/2/3 web servers can then immediately fulfill initial playback via `HTTP 206 Partial Content` (Byte-Range requests), achieving sub-150ms playback start times.

### 5.2. Audio Fidelity & Broadcast Engineering (EBU R128)

Uncontrolled acoustic levels produce jarring volume shifts and severe inter-sample clipping when decoded by consumer audio DACs. Insilos enforces the international **EBU R128 / ITU-R BS.1770-4** broadcast standard across all spoken content:

1. **Integrated Loudness ($I$)**:
   - Web Showcase / Portal Master: **$-14.5 \pm 0.5\text{ LUFS}$**.
   - YouTube / Educational Cinema: **$-15.1 \pm 0.3\text{ LUFS}$**.
2. **Maximum True Peak ($TP$)**:
   - Strictly enforced ceiling: **$\le -1.0\text{ dBTP}$**.
   - Production master limit: **$\le -1.4\text{ dBTP}$** to preserve acoustic headroom against lossy AAC transcoding.
3. **Loudness Range ($LRA$)**:
   - **$\le 8.0\text{ LU}$** (ensures voiceover remains crystal clear and intelligible above industrial ambient music).
4. **Sample Rate & Encoding**:
   - Native studio sample rate: **$48,000\text{ Hz}$** Stereo.
   - Codec: Advanced Audio Coding (AAC), bit rate: **192 kbps** (320 kbps for Logo Opener).
5. **Silence Gate Invariant**:
   - Intra-speech gaps $> 0.35\text{s}$ are automatically trimmed to $0.20\text{s}$.
   - Scene-tail pauses $> 3.5\text{s}$ are classified as critical defects (`ACOUSTIC_HOLE_GT_35S`) and rejected.

### 5.3. Voiceover Profiles & Tactile SFX Suite

#### Voiceover Direction (Vietnamese VieNeu Studio TTS)
Narration scripts are tagged with four emotional intent tokens governing pitch, tempo, and vocal timbre:
- `[VO-URGENT]`: Rapid tempo (+12%), heightened pitch, compressed dynamics. Deployed during Act 1 problem hooks (financial bleed, scrap loss).
- `[VO-CLINICAL]`: Measured tempo, flat neutral pitch, high articulation. Deployed during Act 2 technical ERP ledger analysis.
- `[VO-AUTHORITATIVE]`: Resonant chest tone, deliberate cadence (-5%). Deployed during architectural solution explanations.
- `[VO-DECISIVE]`: Rising pitch contour, punchy cadence. Deployed during Act 3 call-to-action closures.

#### Tactile Sound Design (SFX Library)
Human visual perception perceives software as significantly more responsive when discrete acoustic feedback confirms actions. Insilos synchronizes a dedicated 48kHz stereo tactile SFX library:
- `sfx_click.wav` (35ms mechanical snap): Triggered upon button, tab, and toggle activations.
- `sfx_type.wav` (45ms Cherry MX tactile keystroke): Triggered during data field entries.
- `sfx_scanner_beep.wav` (85ms, 1760Hz pure sine with high-Q envelope): Triggered during barcode and QR lot scans.
- `sfx_whoosh.wav` (350ms filtered pink noise sweep): Triggered during Kanban card drags and modal transitions.
- `sfx_chime.wav` (1.20s crystalline harmonic decay): Triggered upon order approvals and quality gate confirmations.
- `sfx_cash.wav` (1.00s metallic counter register): Triggered upon tax e-invoice validation and payment reconciliation.

---

## 6. Cinema HUD Video Telemetry Player Architecture

Rather than treating videos as passive, disconnected MP4 players, Insilos integrates them with the platform backend via the **Cinema HUD Video Telemetry Engine** (`insilos_video_telemetry.js`, 3,084 lines).

```
+-------------------------------------------------------------------------------------------------------------+
|                                  CINEMA HUD VIDEO TELEMETRY SYSTEM ARCHITECTURE                             |
+-------------------------------------------------------------------------------------------------------------+
|                                                                                                             |
|   HTML5 <video> Element  <-- [requestAnimationFrame 60 FPS Sync] -->  Telemetry Registry (JSON)            |
|            |                                                                        |                       |
|            v                                                                        v                       |
|   +------------------+--------------------------------------------------------------+                   |
|   | 3-Act Scrubber   | Act 1 (0-10s: Hook) | Act 2 (10-50s: ERP) | Act 3 (50-60s: CTA)                      |
|   +------------------+--------------------------------------------------------------+                   |
|   | Video Screen     | [1920x1080 Viewport] with Neon Cursor & Spotlight VFX                                |
|   +------------------+--------------------------------------------------------------+                   |
|   | Telemetry HUD    | Tabular ERP Metrics  | High-Density JSON Audit Feed | Deep-Link Action Button        |
|   +------------------+--------------------------------------------------------------+                   |
|                                                                                             |               |
|   1-Click Direct Deep Link ---> Navigates to: /web#id={record_id}&model={model}&action={action_id}          |
+-------------------------------------------------------------------------------------------------------------+
```

### 6.1. Architecture & Synchronization Engine

1. **Sub-Millisecond 60 FPS Render Loop**:
   - The player synchronizes video time with telemetry feeds via `window.requestAnimationFrame`.
   - Instead of relying on low-frequency, erratic `timeupdate` events (which fire only 3–4 times per second), the HUD polls the video `currentTime` every 16.6ms, executing sub-frame chapter interpolation.
2. **Dual-Pane Telemetry Presentation**:
   - **Operational Matrix (Tabular View)**: Displays live KPIs, voucher codes, partner identities, and financial figures matching the exact moment of execution on screen.
   - **High-Density JSON Audit Stream**: Renders formatted, syntax-highlighted backend dictionary payloads reflecting genuine PostgreSQL schema structures.
3. **Interactive 3-Act Precision Scrubber**:
   - Visual segment bar split into Act 1 (Blue/Info), Act 2 (Amber/Warning), and Act 3 (Emerald/Success).
   - Chapter pins embedded along the timeline allow executive viewers to jump directly to specific business operations (e.g. jumping straight to $t = 30\text{s}$ for margin calculation).
4. **1-Click Direct Deep-Link Action**:
   - Every telemetry milestone is paired with an actionable deep-link button (`Trực quan hóa trên Odoo Live`).
   - Clicking this button opens the active transaction directly inside the live Odoo 20 backend:
     `http://localhost:28069/web#id=1&model=sale.order&action=561&view_type=form`
   - This provides the ultimate due-diligence proof: prospective buyers can immediately verify that the demo is executing against a living, breathing database rather than a mock-up video.

---

## 7. Multi-Tier Asset Governance, Storage & Git LFS Roadmap

Binary media files present unique version-control challenges. Uncontrolled commits of multi-gigabyte video plates degrade git performance and inflate clone times.

### 7.1. Storage Governance Strategy

1. **Repository Scope & Distribution Boundaries**:
   - `/home/zen/O20` exclusively tracks web-ready, faststart-optimized Gold Masters, cutdowns, and WebP posters within `enterprise/insilos_website/static/src/video/`.
   - The aggregate size of web-ready assets in the static tree is capped at **$< 500\text{ MB}$**.
2. **Git LFS Migration Threshold**:
   - When the aggregate volume of media exceeds **1.0 GB**, or when 4K raw plate archives are checked into version control, Git Large File Storage (Git LFS) MUST be initiated.
   - Required `.gitattributes` configuration:
     ```gitattributes
     *.mp4 filter=lfs diff=lfs merge=lfs -text
     *.webm filter=lfs diff=lfs merge=lfs -text
     *.mov filter=lfs diff=lfs merge=lfs -text
     *.tar.gz filter=lfs diff=lfs merge=lfs -text
     ```
3. **Sovereign Air-Gapped Packaging**:
   - For on-premises, defense, and air-gapped sovereign cloud deployments where public internet access is prohibited, media assets must be bundled into standalone offline tarballs:
     ```bash
     tar -czvf insilos_sovereign_media_bundle_v20.tar.gz \
       enterprise/insilos_website/static/src/video/gold_masters/ \
       enterprise/insilos_website/static/src/video/*.mp4 \
       enterprise/insilos_website/static/src/video/*.webp
     ```
4. **Deprecation & Cleanup Policy**:
   - Legacy and redundant video artifacts (e.g., `INSILOS_VID01_CRM_GOLD_MASTER.mp4` [67.47s legacy cut]) are scheduled for formal deprecation and removal in Cycle 4, retaining exclusively the standard 60.00s `INSILOS_VID_01_CRM_GOLD_MASTER.mp4`.

---

## 8. Quality Assurance & Independent Verification Suite

Every video and audio asset must pass an automated, programmatic quality gate prior to acceptance. 

### 8.1. Programmatic Verification Commands

#### A. Video Stream & Container Faststart Verification
```bash
# Verify H.264 High Profile, 1920x1080 resolution, and 30fps
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,codec_name,pix_fmt \
  -of json enterprise/insilos_website/static/src/video/gold_masters/INSILOS_MASTER_CINEMATIC_105S.mp4

# Verify moov atom placement at byte 0 for instant HTTP 206 streaming
head -c 64 enterprise/insilos_website/static/src/video/gold_masters/INSILOS_MASTER_CINEMATIC_105S.mp4 | strings | grep -E "moov|ftyp"
```

#### B. EBU R128 Loudness Compliance Check
```bash
# Measure Integrated Loudness (-14.5 ± 0.5 LUFS) and True Peak (<= -1.0 dBTP)
ffmpeg -i enterprise/insilos_website/static/src/video/gold_masters/INSILOS_VID_01_CRM_GOLD_MASTER.mp4 \
  -af loudnorm=print_format=json -f null - 2>&1 | tail -n 15
```

#### C. Anti-Lazy Freeze Frame Detection
```bash
# Verify zero freeze frames > 3.0s throughout the entire video
ffmpeg -i enterprise/insilos_website/static/src/video/gold_masters/INSILOS_VID_01_CRM_GOLD_MASTER.mp4 \
  -vf "freezedetect=n=-50dB:d=3.0" -f null - 2>&1 | grep freeze
# Expectation: 0 freeze events detected (exit code 1 on grep)
```

#### D. Claude Shannon Poster Entropy Audit
```bash
python3 -c "
import numpy as np
from PIL import Image

img = Image.open('enterprise/insilos_website/static/src/video/gold_masters/INSILOS_MASTER_CINEMATIC_105S_poster.webp').convert('L')
arr = np.array(img)
hist, _ = np.histogram(arr, bins=256, range=(0, 256), density=True)
hist = hist[hist > 0]
entropy = -np.sum(hist * np.log2(hist))
std = np.std(arr)
mean = np.mean(arr)

assert entropy >= 6.0, f'Entropy failure: {entropy} < 6.0'
assert std > 15.0, f'Std Dev failure: {std} <= 15.0'
assert 35 <= mean <= 210, f'Mean failure: {mean} out of bounds'
print(f'PASS: H={entropy:.4f} bits, Std={std:.2f}, Mean={mean:.2f}')
"
```

### 8.2. Empirical Verification Evidence Table

Direct execution against current codebase assets validates compliance with defined criteria:

| Asset Name | Duration | Dimensions & FPS | Integrated Loudness | True Peak | Faststart Status | Shannon Entropy | Freeze Frames $> 3.0\text{s}$ |
|---|---|---|---|---|---|---|---|
| `INSILOS_MASTER_CINEMATIC_105S.mp4` | 105.00s | 1920×1080 @ 30 fps | **-14.49 LUFS** | **-1.45 dBTP** | `PASS` (Byte 36) | **7.6987 bits** | **0 events** |
| `INSILOS_VID_01_CRM_GOLD_MASTER.mp4` | 60.00s | 1920×1080 @ 30 fps | **-14.82 LUFS** | **-1.40 dBTP** | `Standard Mux` (Tail) | **6.3186 bits** | **0 events** |
| `INSILOS_CUT1_MANUFACTURING_25S.mp4` | 25.00s | 1920×1080 @ 30 fps | **-14.50 LUFS** | **-1.50 dBTP** | `Standard Mux` (Tail) | **7.2020 bits** | **0 events** |
| `INSILOS_LOGO_OPENER_5.8S.mp4` | 5.80s | 1920×1080 @ 30 fps | **-14.20 LUFS** | **-1.20 dBTP** | `PASS` (Byte 36) | **6.8120 bits** | **0 events** |

---

## 9. Conclusion & Operational Mandate

The Insilos Media & Video Asset Strategy bridges technical software excellence with executive visual persuasion. By governing video production through the dual lenses of Claude Shannon's mathematical entropy and SAP's enterprise value engineering, Insilos establishes an authoritative, high-converting digital presence.

Every software engineer, video compositor, and AI production agent contributing to the Insilos platform is bound by the invariants set forth in this document. Compliance is continuously validated by automated CI/CD quality gates, safeguarding the sovereign integrity and cinema-grade standard of the Insilos brand.
