# Hard Refactor — Phần A: Branding, Assets và Taxonomy

## 1. Phạm vi và thứ tự nguồn sự thật

Tài liệu này quy định tài sản thị giác và văn bản thương hiệu. Khi có mâu thuẫn, ưu tiên theo thứ tự:

1. gate và code đang chạy;
2. [`INSILOS_LEXICON.md`](INSILOS_LEXICON.md) cho thuật ngữ;
3. tài sản triển khai hiện có;
4. tài liệu kế hoạch chỉ để tham khảo, không phải trạng thái hiện hành.

Mọi rename code, model, XML ID, bundle hoặc path liên quan phải theo [Phần B — AST Mapping & Coding Guide](HARD_REFACTOR_PART_B_AST_MAPPING_CODING_GUIDE.md).

## 2. Logo

### Source of truth và trạng thái checkout

`tools/sync_branding_logos.py` xác định `branding/` là nguồn và ánh xạ các biến thể sang runtime. Tuy nhiên, **ba source mà script yêu cầu hiện đang thiếu trong checkout này**:

- `branding/h-logo-light.svg`;
- `branding/h-logo-dark.svg`;
- `branding/icon-dark.svg`.

Vì vậy không được tuyên bố `branding/` hiện đầy đủ, không chạy chế độ ghi của script, không dựng lại source từ file đích. Các file runtime như `insilos/addons/web/static/img/logo.svg` vẫn là bằng chứng triển khai hiện có, không tự động trở thành source canonical.

### Contract

| Biến thể | Mục đích | Contract hiện hành |
|---|---|---|
| `h-logo-light.svg` | logo ngang trên nền sáng | SVG gốc; script copy sang `logo.svg`, `insilos_logo.svg`; render PNG `512×120` |
| `h-logo-dark.svg` | logo ngang chữ sáng trên nền tối | SVG gốc; copy sang `logo_dark.svg`, `insilos_logo_dark.svg`, website logo và inverse logo; render PNG `512×120` |
| `icon-dark.svg` | brand mark vuông, favicon | SVG gốc tỷ lệ vuông; copy sang hai brand-icon SVG; render PNG `1000×1000`, company logo `256×256`, favicon PNG/ICO `16–256 px` |

`#004455` **tồn tại trong logo triển khai hiện hành** (`insilos/addons/web/static/img/logo.svg`); không thay bằng màu app icon. Tỷ lệ, `viewBox`, mask và màu nội tại của logo phải giữ nguyên theo source được khôi phục.

**Cấm:** sửa tay file đích; kéo méo tỷ lệ; đổi light/dark theo tên file thay vì nền sử dụng; tự tạo source thay thế; dùng logo làm icon chức năng.

**Verifier:** sau khi ba source được khôi phục, chạy `python3 tools/sync_branding_logos.py --check`; kiểm tra trực quan trên nền sáng/tối và favicon. Gate đang fail sớm vì thiếu source là kết quả đúng của checkout hiện tại.

## 3. Icon taxonomy

### 3.1 App Icons — launcher cấp cao nhất

App Icon là icon của root `<menuitem web_icon="module,static/description/icon.svg">` trong app drawer.

- **Authority gate:** `tools/icon_mapping.json`. File `branding/icon_mapping.json` không phải authority. Checkout hiện tại mới có một mapping (`insilos_logistics_idp`); gate đầy đủ đang báo 14 lỗi, gồm mapping thiếu, một launcher không canonical và ba `viewBox` không chuẩn.
- **Nguồn glyph canonical:** `tools/phosphor_duotone/<glyph>-duotone.svg`. Checkout hiện tại mới có `identification-card-duotone.svg`; không được suy diễn rằng thư mục đã đủ glyph cho mọi launcher.
- **Đích:** `<module>/static/description/icon.svg`; launcher governed khác path này phải có mapping theo `module.xmlid`.
- **Định dạng:** SVG Phosphor duotone; `viewBox="0 0 256 256"`; có lớp holder `opacity="0.2"`.
- **Màu:** `#0B2E64` bị gate cưỡng chế; `currentColor` và `none` được chấp nhận trong SVG canonical tương đương. Không màu khác.
- **Kích thước:** vector 256-unit; không nhúng raster, không tự đặt kích thước pixel khác trong contract launcher.
- **Tính duy nhất:** app governed không dùng trùng glyph canonical.

**Cấm:** thêm app governed mà thiếu mapping; dùng glyph không có trong nguồn; đổi màu; placeholder; copy cùng glyph cho nhiều app; sửa SVG đích mà không đồng bộ mapping/source.

**Verifier:** `python3 tools/check_app_icons_integrity.py --self-check` phải xanh. `python3 tools/check_app_icons_integrity.py` hiện phải tái hiện 14 lỗi đã ghi trên; chỉ được coi app-icon migration hoàn tất khi gate đầy đủ xanh.

### 3.2 Module Icons — metadata/module card

Module Icon là icon metadata được module loader tìm theo thứ tự `static/description/icon.svg`, rồi `icon.png`, cuối cùng fallback `base/static/description/icon.svg|png`. Manifest có thể khai báo URL `/module/static/description/icon.svg`.

- **Source of truth:** file trong chính module và cơ chế lookup tại `insilos/insilos/modules/module.py`.
- **Định dạng/path:** ưu tiên SVG ở `<module>/static/description/icon.svg`; PNG chỉ là compatibility fallback.
- **Kích thước/màu:** checkout hiện không có gate riêng áp một kích thước hay palette chung cho toàn bộ Module Icons. Nếu cùng file được root `web_icon` sử dụng, toàn bộ contract App Icon áp dụng.

**Cấm:** gọi mọi module icon là app launcher; ép `#0B2E64` lên icon metadata không thuộc phạm vi app gate; tạo path ngoài cơ chế loader rồi giả định tự được phân phối.

**Verifier:** kiểm tra manifest/path, module card thực tế; nếu là root launcher, chạy app-icon gate.

### 3.3 UI Icons — hành động và trạng thái trong giao diện

UI Icon là glyph nội tuyến trong XML/QWeb/JS, dùng cặp class weight + glyph, ví dụ `ph-duotone ph-camera`.

- **Source of truth runtime:** `insilos/addons/web/static/src/libs/phosphor/<weight>/style.css`.
- **Weights hiện có:** `duotone`, `fill`, `bold`, `light`, `thin`, `regular`; weight dùng phải được bundle trong manifest.
- **Nguồn upstream vendored:** `branding/phosphor/`; đây không thay thế CSS runtime.
- **Định dạng/kích thước/màu:** icon font/CSS; kích thước theo typography/component; màu theo semantic role hoặc `currentColor`, không hard-code màu app-icon.
- **Trạng thái:** mỗi trạng thái phải dùng glyph/weight có thật; khi toggle weight, cả hai stylesheet phải được bundle.

**Cấm:** ghép tên `ph-*` bằng suy đoán; dùng weight chưa bundle; để selector test `.fa-*` mất điểm bám; chèn token class vào biểu thức `x-att-class`; dùng App Icon SVG như UI glyph.

**Verifier:**

```bash
python3 tools/check_icon_integrity.py
python3 tools/check_phosphor_icon_names.py
python3 tools/check_icon_lib_dispatch.py
python3 tools/audit_test_icon_selectors.py
```

## 4. Semantic Color Taxonomy

| Vai trò | Giá trị/chính sách đã chứng minh | Phạm vi |
|---|---|---|
| App Icon foreground | `#0B2E64` | gate bắt buộc trong `check_app_icons_integrity.py` |
| Script background | `#1F76D2` | chỉ `tools/sync_branding_logos.py` ghi nhận làm nền tối để chọn logo inverse; không phải màu foreground icon hoặc token UI tổng quát |
| Logo internal color | `#004455` | có trong logo runtime hiện hành; giữ theo artwork |
| UI semantic | dùng token/component hiện hành: primary/action, info, success, warning, danger, neutral, surface/text/border | không suy ra hex từ plan |

Các màu khác từng nêu trong plan **chưa được gate hóa**. Không nâng chúng thành chuẩn, không thay semantic token bằng hex rời rạc. Sai khác light/dark chỉ hợp lệ khi có contract theo ngữ cảnh; yêu cầu contrast và trạng thái không được dựa riêng vào màu.

## 5. Text Taxonomies

| Nhóm | Contract |
|---|---|
| Product/brand | Viết `Insilos` theo tên sản phẩm; không đưa tên upstream hoặc biến thể tự đặt vào UI mới |
| App/module display name | English canonical trong source/manifest; tên người dùng thấy không được rò technical module ID; bản dịch theo lexicon |
| Action | Động từ mệnh lệnh canonical. Nút tạo record dùng `Create`, không dùng `New`; `New` chỉ giữ khi mô tả trạng thái, stage, filter hoặc cụm từ được lexicon miễn trừ |
| Menu | Nhánh báo cáo cấp 1 dùng `Reporting`; nhánh thiết lập nghiệp vụ dùng `Configuration`; giữ đúng các ngoại lệ ghi trong lexicon |
| Message | msgid English ổn định, rõ hành động/trạng thái; không nối câu làm mất khả năng dịch; placeholder phải giữ nguyên qua locale |
| User content | Không rename/dịch tự động dữ liệu người dùng, stage, record name hoặc nội dung DB chỉ vì trùng text UI |
| Technical contracts | Model/table/field, XML ID, bundle key, import specifier, MIME type, route, selector và file/path là protected contracts; không đổi như branding text |

## 6. Branding Text và i18n

[`INSILOS_LEXICON.md`](INSILOS_LEXICON.md) là source of truth. Mã nguồn dùng **Canonical English msgid**; thứ tự thị trường **VI → EN → FR**; VI và FR nằm trong `i18n/*.po`.

Các contract bắt buộc:

- `Create` là action tạo record; không thay mọi `New` bằng regex.
- Menu cấp 1 dùng `Reporting`, không dùng `Analytics`, trừ ngoại lệ lexicon.
- Nhánh cấu hình dùng `Configuration`, không dùng `System Admin`, trừ dữ liệu test được lexicon bảo vệ.
- Cùng msgid phải có msgstr thống nhất theo locale.
- Chuỗi upstream còn sót, tên kỹ thuật lộ ra UI và alias nội bộ cấm trong nội dung mới; ngoại lệ protected contract phải giữ nguyên, ví dụ key `web.assets_clickbot`.
- Không đưa credential, token, password, session ID hoặc secret vào msgid, bản dịch, ảnh hay tài liệu.

**Verifier:** `python3 tools/check_lexicon_consistency.py`; parse gettext; kiểm tra source và các locale VI/EN/FR; chạy UI smoke cho menu/action đã đổi.

## 7. Điều cấm chung

- Không lấy snapshot plan cũ làm trạng thái hiện tại.
- Không global replace màu, text, class, path hoặc identifier.
- Không trộn Logo, App Icon, Module Icon và UI Icon thành một contract.
- Không sửa generated/deployed asset trực tiếp khi source canonical tồn tại.
- Không biến giá trị chưa có gate thành policy bắt buộc.
- Không rename protected contracts để “sạch thương hiệu”; dùng quy trình parser/AST và migration của Phần B khi thay đổi thật sự cần thiết.

## 8. Review checklist

- [ ] Phân loại đúng Logo / App Icon / Module Icon / UI Icon.
- [ ] Source of truth và path tồn tại; nếu thiếu, ghi rõ như ba logo source hiện tại.
- [ ] App Icon có entry trong `tools/icon_mapping.json`, glyph tồn tại, SVG duotone `0 0 256 256`, màu `#0B2E64`.
- [ ] UI Icon có glyph và weight thật; stylesheet đã bundle; selector test được cập nhật.
- [ ] Không dùng `#1F76D2` ngoài vai trò background đã chứng minh; giữ `#004455` trong artwork logo; không hợp thức hóa màu plan chưa có gate.
- [ ] Text dùng canonical English msgid; VI/EN/FR đúng lexicon.
- [ ] `Create`/`New`, `Reporting`, `Configuration` đúng ngữ cảnh và ngoại lệ.
- [ ] Protected contracts không bị đổi ngoài migration nguyên tử.
- [ ] Verifier tương ứng chạy xanh, hoặc failure đã biết do source thiếu được ghi rõ.
- [ ] Diff chỉ chứa asset/text cần thiết; không chứa credential.
- [ ] Thay đổi identifier/path đã được review theo [Phần B](HARD_REFACTOR_PART_B_AST_MAPPING_CODING_GUIDE.md).
