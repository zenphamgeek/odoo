# Hard Refactor — Phần B: AST Mapping & Coding Guide

> Tài liệu đồng hành: [Phần A — Branding, Assets & Taxonomy](HARD_REFACTOR_PART_A_BRANDING_ASSETS_TAXONOMY.md).

## 1. Nguyên tắc bắt buộc

- Lập inventory trước khi sửa: vị trí cú pháp, chủ sở hữu, phụ thuộc, dữ liệu lưu trong DB, cache và artifact triển khai.
- Semantic rename phải dùng parser/CST/AST hoặc API schema; không dùng global regex/Ctrl+H mù.
- Mỗi mapping phải có source, target, guard và verifier rõ ràng. Không suy diễn từ chuỗi con.
- Một đợt biến đổi chỉ có một mutation owner; giới hạn scope; tạo diff nhỏ, có thể review và rollback.
- Không trộn đổi hợp đồng hiện hành với migration lịch sử. Không ghi credential, DSN, token hoặc mật khẩu vào script, log hay evidence.

### Hợp đồng hiện hành và migration lịch sử

**Current protected contracts** là định danh đang được loader, API, manifest, extension, editor, module bên thứ ba hoặc dữ liệu production sử dụng. Mặc định giữ nguyên; chỉ đổi khi có mapping được duyệt, compatibility window và verifier runtime. Ví dụ: package ngoài, endpoint ngoài, XML ID công khai, selector/plugin hook, CLI flag.

**Historical schema migration** là phép chuyển trạng thái DB/version đã phát hành: table, column, relation table, sequence, index, constraint, metadata model và dữ liệu lưu sẵn. Phải nằm trong migration versioned, chạy đúng một lần, có precondition, transaction, rehearsal trên bản restore và bằng chứng hậu kiểm. Không biến migration lịch sử thành scanner chạy thường xuyên; không sửa backup/artifact quá khứ để “làm sạch” tên.

## 2. Mapping matrix

| Miền | Source pattern | Target pattern | Parser/codemod | Guards | Verifier |
|---|---|---|---|---|---|
| Python | `Name`, `Attribute`, import, class/base, call; literal của `_name`, `_inherit`, field/comodel | Mapping tường minh theo loại node và qualified symbol | `libcst` ưu tiên vì giữ format/comment; `ast` cho inventory/read-only | Chỉ node đúng loại, module và scope; không đổi comment/docstring/user text; parse trước/sau; idempotent | compile/import; static residue theo allowlist; registry startup; targeted test |
| JS/TS | `ImportDeclaration.source`, export, identifier, `MemberExpression`, registry key, runtime suffix | Module specifier/symbol/member/key tương ứng | Babel/TypeScript AST hoặc `jscodeshift`; giữ parser plugins của dự án | Phân biệt identifier với property/string; không chạm package ngoài; loader key và producer/consumer đổi atomically | parse/type/lint; bundle build; module graph; browser console; SILO/SWEEP |
| XML/QWeb | element/attribute, `t-call`, template ID, XPath `expr`, asset/template reference | QName/attribute/reference đã duyệt | XML parser bảo toàn namespace, encoding, CDATA và whitespace tối đa; XPath-aware transform | Không regex cả file; namespace đúng; XPath chỉ đổi token mục tiêu; template producer/consumer cùng batch | parse toàn bộ XML; schema/static refs; module upgrade; render/smoke |
| SCSS/CSS | selector class/ID, custom property, variable, mixin, placeholder, keyframe, `url()` | Token cùng loại, ví dụ selector sang selector | SCSS/PostCSS AST; selector/value parser | Boundary hỗ trợ BEM và chữ hoa; không đổi chuỗi con, URL, tên hàm/package ngoài; inventory HTML/JS/XML consumers | compile asset; residue có allowlist; computed style/DOM metrics; visual/SWEEP |
| Manifest/config | asset glob, tuple `remove/include`, dependency, entry point, job ID, CLI flag, JSON/YAML key | Path/key/reference đồng bộ với producer | Parser gốc: Python AST cho manifest; JSON/YAML parser; workflow parser | Không stringify/reformat ngoài scope; glob phải match; job ID/`needs`, flag/parser đổi cùng batch | parse config; resolve glob; dependency graph; CI dry-run/build |
| File/path | tên file/thư mục, import path, glob, fixture/snapshot/reference | Path đích duy nhất và mọi consumer | Filesystem move + AST/config updates; không search-replace basename mù | Kiểm collision, case sensitivity, symlink, generated/vendor/backup; giữ lịch sử ngoài scope | không path mồ côi; import/asset resolution; build/package inventory |
| Model/table/field/DB | model string, `_table`, field/comodel, relation table, table/column/sequence/index/FK/constraint, metadata/XML ID | Mapping schema tường minh 1:1 | ORM-aware codemod + migration SQL versioned/catalog-driven | Dependency order; exact identifier whitelist; transaction; pre/post assertions; rehearsal; compatibility window | registry; catalog queries; integrity/orphan checks; module upgrade; runtime CRUD |

### Ngoại lệ regex được phép

Regex chỉ được dùng khi **exact literal được neo trọn**, trên tập file/record đã whitelist và đã chứng minh không cần hiểu ngữ nghĩa. Ví dụ: kiểm tra hoặc thay giá trị toàn trường bằng `^old\.literal$`, không phải thay chuỗi con. Với DB, bắt buộc whitelist table + column + record/domain; dùng equality hoặc regex neo `^...$`; xem trước số hàng và mẫu diff; assertion row count; transaction; hậu kiểm. Cấm `REPLACE()`/`regexp_replace()` global trên mọi cột hoặc dữ liệu người dùng.

## 3. Workflow chuẩn

1. **Inventory** — Chốt source/target dictionary; phân loại semantic, lexical, protected, external, generated và historical. Ghi mọi producer/consumer: code, loader, manifest, template, asset, DB, cache, test, CI, deployed edge. Baseline residue và gate hiện tại.
2. **Dependency ordering** — Dựng đồ thị rồi đổi từ contract nền tới consumer: relation/schema nền → field/model metadata → Python registry → JS loader/import → XML/QWeb/assets → manifest/config/path → DB-stored views/noupdate/cache → deployed edge. Với compatibility migration, triển khai reader kép trước writer mới; dọn compatibility sau khi toàn bộ tenant đã migrate.
3. **Atomic transform** — Chia batch nhỏ theo một contract; parser/codemod idempotent; code, path, manifest và migration liên quan nằm cùng change set. DB dùng transaction khi DDL hỗ trợ; backup/restore point và rollback owner được xác nhận trước mutation. Không `-u all`; chỉ upgrade module bị ảnh hưởng.
4. **Verification** — Chạy gate ladder theo thứ tự, dừng tại gate đỏ đầu tiên. So diff với inventory; chứng minh cả presence của target lẫn absence có kiểm soát của source. Rollback code và DB theo cùng release unit nếu invariant hỏng.

## 4. Gate ladder

| Gate | Mục tiêu | Điều kiện qua |
|---|---|---|
| 1. Static | Syntax, imports, mapping/residue, manifest/glob, dead refs | Parser/compile xanh; residue chỉ còn allowlist có lý do |
| 2. XML parse | Well-formed XML/QWeb, namespace, XPath/reference | Tất cả file parse; target reference resolve |
| 3. Smoke | Registry, module loader, bundle và route tối thiểu | Server khởi động; module mục tiêu load; không traceback/console error |
| 4. SILO | Logic/unit/integration theo module | Test mục tiêu thực sự được discover và chạy; pass count hợp lệ |
| 5. SWEEP | UI flows, console/network, asset/template integrity | Luồng hẹp xanh; không missing module/template/asset |
| 6. DB/runtime | Schema, metadata, noupdate, stored views, CRUD, cache | Catalog/integrity assertions xanh; upgrade và CRUD thành công |
| 7. Deployed edge | Hành vi qua proxy/CDN/container/tenant route thật | Canary/health/route/security surface xanh tại edge; artifact gắn digest |

Gate sau không bù cho gate trước. “Không có lỗi” không đủ nếu test bị bỏ qua: luôn lưu discovered/executed count, command, commit/digest, môi trường và timestamp.

## 5. Lessons learned

| Failure mode | Root cause | Detection | Prevention | Verifier |
|---|---|---|---|---|
| Module loader không nạp test/module nhưng pipeline vẫn xanh | Đổi import/path hoặc runtime suffix lệch giữa producer và consumer; zero tests bị coi là pass | Module graph, console; so discovered/executed count với baseline | Đổi loader key, suffix, import và manifest atomically; minimum-test assertion | Bundle smoke + SILO discovery assertion |
| CSS gãy im lặng | Selector đổi một phía; boundary bỏ sót BEM/chữ hoa; CSS vẫn compile | DOM metrics/computed style, screenshot/visual diff, residue theo context | SCSS/selector AST; map selector tới HTML/JS/XML consumers; hỗ trợ `[a-zA-Z]` | Asset compile + SWEEP/visual verify |
| Model/table/field lệch | Đổi ORM mà thiếu table/column/relation/metadata, sequence hoặc FK | Registry traceback, catalog diff, missing column/table, CRUD lỗi | Mapping schema 1:1; dependency order; migration versioned và rehearsal | Registry + catalog/integrity + CRUD |
| QWeb/assets mất template hoặc bundle | Template ID, `t-call`, XPath, file path và manifest glob đổi không cùng nhịp; cache cũ | XML parse chưa đủ; runtime báo missing template/asset; network 404 | XML-aware transform; producer/consumer inventory; rebuild/warm cache | XML parse + bundle build + rendered smoke/SWEEP |
| DB contamination | Global replace chạm dữ liệu người dùng, `noupdate`, JSONB hoặc chuỗi chứa token | Row sampling/diff, count bất thường, integrity scan, rendered residue | Exact-match whitelist, transaction, row-count assertion, backup và restore rehearsal | DB pre/post oracle + runtime render |
| False-positive rename | Chuỗi con hợp lệ trong từ khác, package ngoài, URL, icon hoặc artifact lịch sử | Contextual residue review; diff cho thấy unrelated changes | AST/node guard; exact boundaries; external/historical allowlist | Focused static scanner + manual diff review |
| Evidence release không tái lập | Log mutable, thiếu commit/digest/environment; evidence ghi source thay cho runtime | Không truy được binary/DB/tenant đã test | Artifact immutable: digest, command, timestamp, environment/tenant identity, result, owner; SBOM/provenance; canary/rollback record | Release governance gate + deployed-edge proof |

## 6. Anti-pattern

- Global regex/Ctrl+H hoặc SQL replace toàn cục.
- Đổi file trước nhưng để import/glob/loader cho “lần sau”.
- Đổi model mà không inventory relation table, metadata, stored views và `noupdate`.
- Chỉ grep source rồi tuyên bố hoàn tất; bỏ DB, cache, rendered HTML và deployed edge.
- Reformat toàn file do parser, làm chìm semantic diff.
- Dùng test pass khi discovered count bằng 0.
- Sửa package/endpoint ngoài, backup, vendor hoặc artifact lịch sử để đạt residue bằng 0.
- Gộp nhiều mapping độc lập vào một migration không thể rollback riêng.
- Lưu credential trong command, migration, log hoặc release evidence.

## 7. Checklist hoàn tất một mapping

- [ ] Source/target, scope, owner và protected/external allowlist đã duyệt.
- [ ] Inventory đủ code, path, manifest, loader, XML/assets, DB/cache và CI.
- [ ] Parser/codemod phù hợp; chạy lần hai tạo zero diff.
- [ ] Batch atomic; migration có precondition, transaction/rollback và rehearsal.
- [ ] Gate ladder chạy tuần tự; test discovery không bằng 0.
- [ ] DB/runtime và deployed edge được kiểm nếu contract đi qua các lớp đó.
- [ ] Evidence bất biến gắn commit/build digest, môi trường, timestamp, command và kết quả; không chứa credential.
