#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Verification Suite for SOP-DGM-06:
Partner Onboarding, Tiering (`tier_s`, `tier_a`, `tier_b`, `tier_c`),
Companion Document Templates (`TPL-ONB-01..04`), Conflict-Free Deduplication,
Sales-First Non-Blocking `sale.order.action_confirm()`, and Outbound Payment Gate.
"""
import configparser
import os
import sys
import types
import psycopg2

ROOT_DIR = "/home/zen/O20"


def get_local_conn(dbname):
    cfg = configparser.ConfigParser()
    cfg.read("/home/zen/O20/odoo.conf")
    return psycopg2.connect(
        dbname=dbname,
        user=cfg["options"].get("db_user", "odoo"),
        password=cfg["options"].get("db_password", "odoo"),
        host=cfg["options"].get("db_host", "127.0.0.1"),
        port=int(cfg["options"].get("db_port", "5434")),
    )


def _read_attachment_text(dbname, store_fname, db_datas):
    if store_fname:
        fpath = os.path.join(ROOT_DIR, "data", "filestore", dbname, store_fname)
        if os.path.isfile(fpath):
            with open(fpath, "rb") as f:
                return f.read().decode("utf-8", errors="replace")
    if db_datas:
        return bytes(db_datas).decode("utf-8", errors="replace")
    return ""


def verify_db_partner_onboarding(dbname):
    conn = get_local_conn(dbname)
    cur = conn.cursor()

    # 1. Verify the 8 canonical DGM partners have PTN-DGM-2026-0001..0008, exact groups, tiers, and 4/4 docs
    cur.execute(
        """
        SELECT DISTINCT ON (dgm_partner_code)
               id, dgm_partner_code, dgm_provisional_code, name,
               dgm_partner_group, dgm_partner_tier, dgm_tier_score,
               dgm_credit_limit_vnd, dgm_allowed_payment_rail,
               dgm_onboarding_state, dgm_onboarding_doc_count,
               dgm_all_companion_docs_ready, dgm_onboarding_folder_id
          FROM res_partner
         WHERE dgm_partner_code IN (
             'PTN-DGM-2026-0001', 'PTN-DGM-2026-0002', 'PTN-DGM-2026-0003',
             'PTN-DGM-2026-0004', 'PTN-DGM-2026-0005', 'PTN-DGM-2026-0006',
             'PTN-DGM-2026-0007', 'PTN-DGM-2026-0008'
         )
         ORDER BY dgm_partner_code ASC, dgm_onboarding_doc_count DESC NULLS LAST, id ASC;
        """
    )
    rows = cur.fetchall()
    assert len(rows) == 8, f"{dbname}: Expected 8 canonical approved DGM partners, got {len(rows)}"

    expected = [
        ("PTN-DGM-2026-0001", "strategic_b2b", "tier_s", 2_000_000_000.0, "vcb_digibiz"),
        ("PTN-DGM-2026-0002", "global_platform", "tier_s", 2_000_000_000.0, "swift_usd"),
        ("PTN-DGM-2026-0003", "strategic_b2b", "tier_s", 2_000_000_000.0, "vcb_digibiz"),
        ("PTN-DGM-2026-0004", "gov_edu", "tier_s", 2_000_000_000.0, "swift_usd"),
        ("PTN-DGM-2026-0005", "infra_vendor", "tier_a", 500_000_000.0, "vcb_digibiz"),
        ("PTN-DGM-2026-0006", "infra_vendor", "tier_a", 500_000_000.0, "vcb_digibiz"),
        ("PTN-DGM-2026-0007", "strategic_b2b", "tier_s", 2_000_000_000.0, "vcb_digibiz"),
        ("PTN-DGM-2026-0008", "strategic_b2b", "tier_s", 2_000_000_000.0, "vcb_digibiz"),
    ]
    partner_ids_by_code = {}
    for row, exp in zip(rows, expected):
        pid, pcode, prov_code, name, grp, tier, score, limit_vnd, rail, state, doc_cnt, docs_ready, folder_id = row
        partner_ids_by_code[pcode] = pid
        exp_code, exp_grp, exp_tier, exp_limit, exp_rail = exp
        assert pcode == exp_code, f"{dbname}: Expected code {exp_code}, got {pcode}"
        assert prov_code and prov_code.startswith("TMP-DGM-"), f"{dbname}: Missing provisional code on {pcode}"
        assert grp == exp_grp, f"{dbname}: {pcode} group mismatch {grp} != {exp_grp}"
        assert tier == exp_tier, f"{dbname}: {pcode} tier mismatch {tier} != {exp_tier}"
        assert float(limit_vnd) == exp_limit, f"{dbname}: {pcode} credit limit mismatch {limit_vnd} != {exp_limit}"
        assert rail == exp_rail, f"{dbname}: {pcode} rail mismatch {rail} != {exp_rail}"
        assert state == "approved", f"{dbname}: {pcode} state mismatch {state}"
        assert doc_cnt == 4 and docs_ready is True, f"{dbname}: {pcode} docs not ready ({doc_cnt}, {docs_ready})"
        assert folder_id is not None, f"{dbname}: {pcode} missing onboarding folder_id"

        # Verify 4 companion documents in dgm_partner_onboarding_doc_rel and documents_document
        cur.execute(
            """
            SELECT d.id, d.name->>'en_US', d.access_internal, d.owner_id, a.name, a.file_size,
                   a.store_fname, a.db_datas
              FROM dgm_partner_onboarding_doc_rel rel
              JOIN documents_document d ON d.id = rel.document_id
              LEFT JOIN ir_attachment a ON a.id = d.attachment_id
             WHERE rel.partner_id = %s AND d.active = TRUE
             ORDER BY d.id ASC;
            """,
            (pid,),
        )
        docs = cur.fetchall()
        assert len(docs) == 4, f"{dbname}: {pcode} expected 4 linked documents, got {len(docs)}"
        tpl_markers = ["[TPL-ONB-01]", "[TPL-ONB-02]", "[TPL-ONB-03]", "[TPL-ONB-04]"]
        for d_row, marker in zip(docs, tpl_markers):
            _, d_name, acc_int, own_id, att_name, fsize, store_fname, db_datas = d_row
            assert marker in d_name, f"{dbname}: Missing marker {marker} in {d_name}"
            assert acc_int in ("edit", "view"), f"{dbname}: Invalid access_internal {acc_int} on {d_name}"
            assert own_id is None, f"{dbname}: Company document {d_name} must have owner_id=None, got {own_id}"
            assert fsize and fsize > 400, f"{dbname}: Attachment {att_name} empty or too small ({fsize})"
            html_text = _read_attachment_text(dbname, store_fname, db_datas)
            for brand_marker in (
                "dgm-brand-footer",
                'data-dgm-footer="drive-logo-v1"',
                'data-logo-source="google-drive-logo-folder"',
                "0317958465",
            ):
                assert brand_marker in html_text, (
                    f"{dbname}: {pcode} {d_name} missing Drive Logo Brand Footer marker `{brand_marker}`"
                )

    # 1a-bis. Verify SOP-DGM-09 Software Contract Templates on MTI (>=4), KTT (>=4), and AIfin (>=8)
    for pcode, min_sw_docs, expected_codes in [
        ("PTN-DGM-2026-0001", 4, ["[TPL-SW-MTI-01]", "[TPL-SW-MTI-02]", "[TPL-SW-MTI-03]", "[TPL-SW-MTI-04]"]),
        ("PTN-DGM-2026-0008", 4, ["[TPL-SW-KTT-01]", "[TPL-SW-KTT-02]", "[TPL-SW-KTT-03]", "[TPL-SW-KTT-04]"]),
        (
            "PTN-DGM-2026-0007",
            8,
            [
                "[TPL-SW-MTI-01]", "[TPL-SW-MTI-02]", "[TPL-SW-MTI-03]", "[TPL-SW-MTI-04]",
                "[TPL-SW-KTT-01]", "[TPL-SW-KTT-02]", "[TPL-SW-KTT-03]", "[TPL-SW-KTT-04]",
            ],
        ),
    ]:
        pid = partner_ids_by_code[pcode]
        cur.execute(
            """
            SELECT d.name->>'en_US', d.owner_id, d.access_internal
              FROM dgm_partner_sw_contract_doc_rel rel
              JOIN documents_document d ON d.id = rel.document_id
             WHERE rel.partner_id = %s AND d.active = TRUE AND d.type != 'folder';
            """,
            (pid,),
        )
        sw_docs = cur.fetchall()
        assert len(sw_docs) >= min_sw_docs, (
            f"{dbname}: {pcode} expected >= {min_sw_docs} SOP-DGM-09 software contract docs, got {len(sw_docs)}"
        )
        joined_names = " | ".join(r[0] or "" for r in sw_docs)
        for exp_marker in expected_codes:
            assert exp_marker in joined_names, f"{dbname}: {pcode} missing software contract {exp_marker}"
        for d_name, own_id, acc_int in sw_docs:
            assert own_id is None and acc_int in ("edit", "view"), (
                f"{dbname}: Software contract {d_name} must have owner_id=None and access_internal=edit"
            )

    # 1b. Verify AIfin (PTN-DGM-2026-0007) MTI-Style Staff Augmentation sale.order, project & Documents folder files
    cur.execute(
        "SELECT id, client_order_ref, state, amount_total FROM sale_order WHERE client_order_ref = 'DIGIMATE-AIFIN-VN_2610-001' AND state = 'sale';"
    )
    aifin_so = cur.fetchone()
    assert aifin_so is not None and float(aifin_so[3]) >= 256_000_000.0, f"{dbname}: Missing AIfin confirmed sale.order: {aifin_so}"

    cur.execute(
        """
        SELECT COUNT(*) FROM documents_document
         WHERE active = TRUE AND type != 'folder'
           AND (name->>'en_US' ILIKE '%AIFIN%' OR name->>'en_US' ILIKE '%Huynh_Pho%' OR name->>'en_US' ILIKE '%HUỲNH PHỐ%');
        """
    )
    aifin_doc_cnt = cur.fetchone()[0]
    assert aifin_doc_cnt >= 9, f"{dbname}: Expected >= 9 active AIfin / Trần Văn Huỳnh Phố documents in Documents, got {aifin_doc_cnt}"

    # 1c. Verify Google Drive `Logo` folder under `06. Thương hiệu & Hình ảnh` has >= 5 active PNG logos
    cur.execute(
        """
        SELECT COUNT(*)
          FROM documents_document d
          JOIN documents_document f ON f.id = d.folder_id
          JOIN ir_attachment a ON a.id = d.attachment_id
         WHERE f.type = 'folder' AND f.active = TRUE
           AND (f.name->>'en_US' = 'Logo' OR f.name::text ILIKE '%Logo%')
           AND d.active = TRUE AND d.type != 'folder'
           AND d.owner_id IS NULL AND a.file_size > 1000;
        """
    )
    logo_file_cnt = cur.fetchone()[0]
    assert logo_file_cnt >= 5, f"{dbname}: Expected >= 5 Google Drive logo PNGs in `Logo` folder, got {logo_file_cnt}"

    # 1d. Verify Master Standardized Template Library (`Bộ Mẫu Biểu Chuẩn Digimate - HR, Partner, Project, Finance`) has >= 22 templates
    cur.execute(
        """
        SELECT d.name->>'en_US', a.store_fname, a.db_datas
          FROM documents_document d
          JOIN documents_document f ON f.id = d.folder_id
          JOIN ir_attachment a ON a.id = d.attachment_id
         WHERE f.type = 'folder' AND f.active = TRUE
           AND (f.name->>'en_US' ILIKE '%Bộ Mẫu Biểu Chuẩn Digimate%' OR f.name::text ILIKE '%Bộ Mẫu Biểu Chuẩn Digimate%')
           AND d.active = TRUE AND d.type != 'folder';
        """
    )
    master_tpl_rows = cur.fetchall()
    assert len(master_tpl_rows) >= 22, (
        f"{dbname}: Expected >= 22 master templates in Bộ Mẫu Biểu Chuẩn Digimate, got {len(master_tpl_rows)}"
    )
    master_names_joined = " | ".join(r[0] or "" for r in master_tpl_rows)
    for sw_code in (
        "[TPL-SW-MTI-01]", "[TPL-SW-MTI-02]", "[TPL-SW-MTI-03]", "[TPL-SW-MTI-04]",
        "[TPL-SW-KTT-01]", "[TPL-SW-KTT-02]", "[TPL-SW-KTT-03]", "[TPL-SW-KTT-04]",
    ):
        assert sw_code in master_names_joined, f"{dbname}: Master template library missing {sw_code}"
    for mt_name, mt_sf, mt_db in master_tpl_rows:
        mt_html = _read_attachment_text(dbname, mt_sf, mt_db)
        assert 'data-dgm-footer="drive-logo-v1"' in mt_html and 'data-logo-source="google-drive-logo-folder"' in mt_html, (
            f"{dbname}: Master template {mt_name} missing Drive Logo Brand Footer"
        )

    # 2. Verify Zero Empty Folders Invariant (Rule 6) across active folders in documents_document
    cur.execute(
        """
        SELECT f.id, f.name->>'en_US'
          FROM documents_document f
         WHERE f.type = 'folder' AND f.active = TRUE
           AND NOT EXISTS (
               SELECT 1 FROM documents_document c
                WHERE c.folder_id = f.id AND c.active = TRUE
           );
        """
    )
    empty_folders = cur.fetchall()
    assert len(empty_folders) == 0, f"{dbname}: Found empty active folders violating Rule 6: {empty_folders}"

    # 3. Verify SOP-DGM-06, SOP-DGM-07, SOP-DGM-08 & SOP-DGM-09 Knowledge Articles exist
    cur.execute(
        "SELECT id, name FROM knowledge_article WHERE name ILIKE 'SOP-DGM-06%' AND active = TRUE;"
    )
    kb = cur.fetchone()
    assert kb is not None, f"{dbname}: Missing SOP-DGM-06 Knowledge Article"

    cur.execute(
        "SELECT id, name FROM knowledge_article WHERE name ILIKE 'SOP-DGM-07%' AND active = TRUE;"
    )
    kb07 = cur.fetchone()
    assert kb07 is not None, f"{dbname}: Missing SOP-DGM-07 Knowledge Article"

    cur.execute(
        "SELECT id, name FROM knowledge_article WHERE name ILIKE 'SOP-DGM-08%' AND active = TRUE;"
    )
    kb08 = cur.fetchone()
    assert kb08 is not None, f"{dbname}: Missing SOP-DGM-08 Knowledge Article"

    cur.execute(
        "SELECT id, name FROM knowledge_article WHERE name ILIKE 'SOP-DGM-09%' AND active = TRUE;"
    )
    kb09 = cur.fetchone()
    assert kb09 is not None, f"{dbname}: Missing SOP-DGM-09 Knowledge Article"

    cur.execute(
        """
        SELECT COUNT(*) FROM dgm_project_timesheet_sheet
         WHERE name IN ('TS-DGM-202610-0001', 'TS-DGM-202610-0002')
           AND state = 'official_invoiced';
        """
    )
    ts08_cnt = cur.fetchone()[0]
    assert ts08_cnt == 2, f"{dbname}: Expected 2 official_invoiced SOP-DGM-08 timesheet sheets, got {ts08_cnt}"

    # 4. Verify SOP-DGM-07 SKUs (SVC-ONSITE-SR, SVC-ONSITE-MID, ERP-360-SALES) & Quotation Template
    for sku_code, expected_price in [
        ("SVC-ONSITE-SR", 350_000.0),
        ("SVC-ONSITE-MID", 250_000.0),
        ("ERP-360-SALES", 200_000_000.0),
    ]:
        cur.execute(
            "SELECT id, list_price FROM product_template WHERE default_code = %s AND active = TRUE;",
            (sku_code,),
        )
        sku_row = cur.fetchone()
        assert sku_row is not None and float(sku_row[1]) == expected_price, (
            f"{dbname}: Missing or wrong price for SKU {sku_code}: {sku_row}"
        )

    cur.execute(
        """
        SELECT id FROM sale_order_template
         WHERE active = TRUE
           AND (name->>'en_US' ILIKE '%Staff Augmentation%' OR name->>'vi_VN' ILIKE '%Staff Augmentation%');
        """
    )
    sot_row = cur.fetchone()
    assert sot_row is not None, f"{dbname}: Missing sale_tpl_staff_augmentation quotation template"

    conn.close()
    print(f"[✓] {dbname}: 8 canonical DGM partners (PTN-DGM-2026-0001..0008 incl. AIfin & KTT Khang Trường Thịnh), 32 companion documents (TPL-ONB-01..04), SOP-DGM-09 Software Contracts (TPL-SW-MTI-01..04 & TPL-SW-KTT-01..04), 5 Drive Logo PNGs, 22 Master Standardized Templates, 3 SOP-DGM-07 SKUs, 2 SOP-DGM-08 Official E-Invoiced Timesheet Sheets, 0 empty folders, and SOP-DGM-06/07/08/09 Knowledge Articles verified")



def verify_workflow_state_machine_and_gates():
    """Tests the Python model logic of `ResPartnerOnboarding`, `SaleOrder.action_confirm`,
    and `AccountPaymentOnboardingGate.action_post`:
    1. Partner Tiering (`tier_s`, `tier_a`, `tier_b`, `tier_c`) & Group classification.
    2. Sales Flexibility: Creating a provisional partner (`TMP-DGM-...`) and confirming a `sale.order`
       succeeds 100% without blocking and auto-generates the 4 companion documents (`TPL-ONB-01..04`).
    3. Conflict Prevention: Creating a second partner with the same Tax ID (`vat`) detects and links
       to the canonical partner without crashing Sales.
    4. Approval Gate & Payment Gate: Outbound payment to an `unapproved` partner is blocked by
       `check_dgm_partner_payment_gate()`, whereas Inbound customer payment is allowed; once
       `action_approve_partner_onboarding()` (or `action_fast_track_onboard()`) is called,
       official `dgm_partner_code` (`PTN-DGM-2026-XXXX`) is issued and outbound payment succeeds!
    """
    import importlib.util

    # Load res_partner_onboarding module source and execute unit/behavioral checks
    spec_path = os.path.join(ROOT_DIR, "addons/insilos_al2c/models/res_partner_onboarding.py")
    with open(spec_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Verify required classes, fields, and methods in res_partner_onboarding.py
    required_symbols = [
        "dgm_partner_group",
        "dgm_partner_tier",
        "dgm_tier_score",
        "dgm_credit_limit_vnd",
        "dgm_allowed_payment_rail",
        "dgm_onboarding_state",
        "dgm_provisional_code",
        "dgm_partner_code",
        "dgm_sales_flex_mode",
        "dgm_canonical_partner_id",
        "dgm_onboarding_doc_ids",
        "dgm_onboarding_doc_count",
        "dgm_all_companion_docs_ready",
        "action_generate_onboarding_documents",
        "action_approve_partner_onboarding",
        "action_fast_track_onboard",
        "action_check_partner_conflict",
        "_resolve_or_link_existing_partner",
        "check_dgm_partner_payment_gate",
    ]
    for sym in required_symbols:
        assert sym in source_code, f"Missing required symbol `{sym}` in res_partner_onboarding.py"

    # Load and execute behavioral harness against ResPartnerOnboarding & AccountPaymentOnboardingGate
    class DummyUserError(Exception):
        pass

    # Build lightweight in-memory ORM harness to test every method of ResPartnerOnboarding
    odoo_mod = types.ModuleType("odoo")
    odoo_mod.SUPERUSER_ID = 1
    odoo_mod._ = lambda s, **kw: (s % kw if kw else s)

    class _DummyApi:
        @staticmethod
        def depends(*args):
            return lambda fn: fn

        @staticmethod
        def model(fn):
            return fn

        @staticmethod
        def model_create_multi(fn):
            return fn

    class _DummyField:
        def __init__(self, *args, **kwargs):
            pass

    class _DummyDatetime(_DummyField):
        @staticmethod
        def now():
            return "2026-10-15 10:30:00"

    class _DummyFields:
        Selection = _DummyField
        Integer = _DummyField
        Float = _DummyField
        Char = _DummyField
        Boolean = _DummyField
        Many2one = _DummyField
        Many2many = _DummyField
        Datetime = _DummyDatetime

    class _DummyModel:
        pass

    odoo_mod.api = _DummyApi
    odoo_mod.fields = _DummyFields
    odoo_mod.models = types.SimpleNamespace(
        Model=_DummyModel,
        AbstractModel=_DummyModel,
        TransientModel=_DummyModel,
    )
    exc_mod = types.ModuleType("odoo.exceptions")
    exc_mod.UserError = DummyUserError

    old_odoo = sys.modules.get("odoo")
    old_exc = sys.modules.get("odoo.exceptions")
    sys.modules["odoo"] = odoo_mod
    sys.modules["odoo.exceptions"] = exc_mod
    try:
        spec = importlib.util.spec_from_file_location("res_partner_onboarding_test", spec_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if old_odoo is not None:
            sys.modules["odoo"] = old_odoo
        else:
            sys.modules.pop("odoo", None)
        if old_exc is not None:
            sys.modules["odoo.exceptions"] = old_exc
        else:
            sys.modules.pop("odoo.exceptions", None)

    PartnerCls = mod.ResPartnerOnboarding

    # Test 1: Normalization & Business Email Domain Extraction
    assert PartnerCls._normalize_vat_code(" 0314015511 ") == "0314015511"
    assert PartnerCls._normalize_vat_code("0100109106-122") == "0100109106-122"
    assert PartnerCls._extract_business_domain("contact@mti-tech.vn") == "mti-tech.vn"
    assert PartnerCls._extract_business_domain("user@gmail.com") == ""

    # Test 2: Tiering & Credit Terms Calculation (`_compute_dgm_tier_and_terms`)
    class MockPartnerRecord:
        def __init__(self, **kw):
            self.id = kw.get("id", 9001)
            self.name = kw.get("name", "Công ty TNHH Giải pháp Số SME")
            self.display_name = self.name
            self.vat = kw.get("vat", "0318889999")
            self.street = kw.get("street", "123 Nguyễn Huệ, Quận 1, TP.HCM")
            self.email = kw.get("email", "billing@sme-tech.vn")
            self.country_id = types.SimpleNamespace(code=kw.get("country_code", "VN"), name="Việt Nam")
            self.is_company = kw.get("is_company", True)
            self.active = True
            self.employee = False
            self.bank_ids = kw.get("bank_ids", [])
            self.dgm_partner_group = kw.get("dgm_partner_group", "sme_commercial")
            self.dgm_partner_tier = kw.get("dgm_partner_tier", False)
            self.dgm_tier_score = 0
            self.dgm_credit_limit_vnd = 0.0
            self.dgm_allowed_payment_rail = False
            self.dgm_onboarding_state = kw.get("dgm_onboarding_state", "provisional")
            self.dgm_provisional_code = kw.get("dgm_provisional_code", f"TMP-DGM-{self.id:04d}")
            self.dgm_partner_code = kw.get("dgm_partner_code", False)
            self.dgm_sales_flex_mode = True
            self.dgm_canonical_partner_id = False
            self.dgm_conflict_warning = False
            self.dgm_onboarding_folder_id = False
            self.dgm_onboarding_doc_ids = types.SimpleNamespace(
                ids=[],
                filtered=lambda fn: [d for d in self._docs if fn(d)],
            )
            self._docs = []
            self.dgm_onboarding_doc_count = 0
            self.dgm_all_companion_docs_ready = False
            self.dgm_approved_by = types.SimpleNamespace(name="Administrator")
            self.dgm_approved_date = None
            self.dgm_payment_gate_override = False
            self._origin = types.SimpleNamespace(dgm_partner_tier=False, dgm_partner_group=self.dgm_partner_group)
            self.env = None

        def __iter__(self):
            yield self

        def ensure_one(self):
            return self

        def sudo(self):
            return self

        def with_context(self, **ctx):
            return self

        def write(self, vals):
            for k, v in vals.items():
                if k == "dgm_onboarding_doc_ids" and isinstance(v, list) and v and v[0][0] == 6:
                    doc_id_list = v[0][2]
                    self._docs = [
                        types.SimpleNamespace(id=did, active=True, type="binary")
                        for did in doc_id_list
                    ]
                    self.dgm_onboarding_doc_ids = types.SimpleNamespace(
                        ids=doc_id_list,
                        filtered=lambda fn: [d for d in self._docs if fn(d)],
                    )
                else:
                    setattr(self, k, v)
            return True

    # Verify Tier S (Strategic B2B), Tier A (Infra Vendor), Tier B (SME with VAT), Tier C (Provisional no VAT)
    p_tier_s = MockPartnerRecord(id=9001, dgm_partner_group="strategic_b2b", vat="0314015511")
    PartnerCls._compute_dgm_tier_and_terms(p_tier_s)
    assert p_tier_s.dgm_partner_tier == "tier_s" and p_tier_s.dgm_credit_limit_vnd == 2_000_000_000.0

    p_tier_a = MockPartnerRecord(id=9002, dgm_partner_group="infra_vendor", vat="0300954529")
    PartnerCls._compute_dgm_tier_and_terms(p_tier_a)
    assert p_tier_a.dgm_partner_tier == "tier_a" and p_tier_a.dgm_credit_limit_vnd == 500_000_000.0

    p_tier_b = MockPartnerRecord(id=9003, dgm_partner_group="sme_commercial", vat="0318889999")
    PartnerCls._compute_dgm_tier_and_terms(p_tier_b)
    assert p_tier_b.dgm_partner_tier == "tier_b" and p_tier_b.dgm_credit_limit_vnd == 100_000_000.0

    p_tier_c = MockPartnerRecord(id=9004, dgm_partner_group="sme_commercial", vat="")
    PartnerCls._compute_dgm_tier_and_terms(p_tier_c)
    assert p_tier_c.dgm_partner_tier == "tier_c" and p_tier_c.dgm_credit_limit_vnd == 0.0 and p_tier_c.dgm_allowed_payment_rail == "prepaid_only"

    # Test 3: Companion Document Templates Rendering (`TPL-ONB-01..04`) with Drive Logo Brand Footer
    rendered_tpls = PartnerCls._render_companion_templates_payload(p_tier_b)
    assert len(rendered_tpls) == 4
    assert [t["tpl_code"] for t in rendered_tpls] == ["TPL-ONB-01", "TPL-ONB-02", "TPL-ONB-03", "TPL-ONB-04"]
    for t in rendered_tpls:
        assert "0317958465" in t["html"] and "CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ" in t["html"]
        assert "dgm-brand-footer" in t["html"] and 'data-logo-source="google-drive-logo-folder"' in t["html"]


    # Test 4: Payment Gate Enforcement (`check_dgm_partner_payment_gate`)
    class MockEnv:
        def __init__(self, partners):
            self.context = {}
            self.user = types.SimpleNamespace(id=2, name="Administrator")
            self._partners = partners
            self._docs_created = []
            self._seq = 10

        def ref(self, xmlid, raise_if_not_found=False):
            return types.SimpleNamespace(id=100, exists=lambda: True, active=True, owner_id=False, access_internal="edit")

        def __getitem__(self, model_name):
            env_self = self
            if model_name == "hr.employee":
                return types.SimpleNamespace(sudo=lambda: types.SimpleNamespace(search_count=lambda dom, limit=1: 0))
            if model_name == "ir.sequence":
                return types.SimpleNamespace(sudo=lambda: types.SimpleNamespace(next_by_code=lambda code: f"PTN-DGM-2026-00{env_self._seq}"))
            if model_name == "ir.attachment":
                return types.SimpleNamespace(
                    sudo=lambda: types.SimpleNamespace(
                        create=lambda vals: types.SimpleNamespace(id=500, write=lambda v: True)
                    )
                )
            if model_name == "documents.document":
                class _DocMgr:
                    def sudo(self):
                        return self

                    def search(self, dom, order=None, limit=None):
                        return []

                    def create(self, vals):
                        env_self._seq += 1
                        rec = types.SimpleNamespace(
                            id=env_self._seq,
                            name=vals.get("name"),
                            type=vals.get("type", "binary"),
                            active=True,
                            owner_id=False,
                            access_internal="edit",
                            attachment_id=types.SimpleNamespace(write=lambda v: True),
                            exists=lambda: True,
                            write=lambda v: True,
                        )
                        env_self._docs_created.append(rec)
                        return rec

                return _DocMgr()
            if model_name == "res.partner":
                class _PartnerMgr:
                    def sudo(self):
                        return self

                    def browse(self, cid=None):
                        if cid is None:
                            return []
                        for p in env_self._partners:
                            if p.id == cid:
                                return p
                        return []

                    def search(self, dom, order=None, limit=None):
                        return [p for p in env_self._partners if p.id != env_self._active_id]

                    def search_count(self, dom):
                        return 0

                return _PartnerMgr()
            return types.SimpleNamespace()

    mock_env = MockEnv([p_tier_s, p_tier_b])
    p_tier_s.dgm_partner_code = "PTN-DGM-2026-0001"
    p_tier_s.dgm_onboarding_state = "approved"
    p_tier_b.env = mock_env
    p_tier_s.env = mock_env

    # 4a. Inbound customer payment on Provisional partner MUST succeed without blocking
    assert PartnerCls.check_dgm_partner_payment_gate(p_tier_b, payment_type="inbound") is True

    # 4b. Outbound payment on Provisional partner MUST raise UserError
    blocked = False
    try:
        PartnerCls.check_dgm_partner_payment_gate(p_tier_b, payment_type="outbound")
    except DummyUserError as err:
        blocked = True
        assert "SOP-DGM-06" in str(err)
    assert blocked is True, "Outbound payment to unapproved provisional partner must be blocked!"

    # 4c. Generate companion documents and approve partner onboarding (or Fast-Track Onboard)
    p_tier_b._get_or_create_dgm_onboarding_folder = lambda: types.SimpleNamespace(id=3226)
    p_tier_b._render_companion_templates_payload = lambda: PartnerCls._render_companion_templates_payload(p_tier_b)
    p_tier_b._compute_dgm_onboarding_docs = lambda: PartnerCls._compute_dgm_onboarding_docs(p_tier_b)
    p_tier_b._compute_dgm_tier_and_terms = lambda: PartnerCls._compute_dgm_tier_and_terms(p_tier_b)
    p_tier_b._next_dgm_partner_code = lambda pid=None: "PTN-DGM-2026-0007"
    p_tier_b.action_generate_onboarding_documents = lambda: PartnerCls.action_generate_onboarding_documents(p_tier_b)
    p_tier_b.action_approve_partner_onboarding = lambda: PartnerCls.action_approve_partner_onboarding(p_tier_b)
    p_tier_b._resolve_or_link_existing_partner = lambda: True

    PartnerCls.action_fast_track_onboard(p_tier_b)
    assert p_tier_b.dgm_onboarding_state == "approved"
    assert p_tier_b.dgm_partner_code == "PTN-DGM-2026-0007"
    assert p_tier_b.dgm_onboarding_doc_count == 4 and p_tier_b.dgm_all_companion_docs_ready is True

    # 4d. Outbound payment after approval MUST succeed!
    assert PartnerCls.check_dgm_partner_payment_gate(p_tier_b, payment_type="outbound") is True

    # Test 5: Conflict-Free Deduplication (`_resolve_or_link_existing_partner` & `action_check_partner_conflict`)
    p_dup = MockPartnerRecord(id=9099, name="MTI Tech Chi nhánh 2", vat="0314015511")
    p_dup.env = mock_env
    mock_env._active_id = p_dup.id
    p_dup._normalize_vat_code = PartnerCls._normalize_vat_code
    p_dup._extract_business_domain = PartnerCls._extract_business_domain
    p_dup._resolve_or_link_existing_partner = lambda: PartnerCls._resolve_or_link_existing_partner(p_dup)
    conflict_res = PartnerCls.action_check_partner_conflict(p_dup)
    assert conflict_res["has_conflict"] is True
    assert conflict_res["canonical_partner_code"] == "PTN-DGM-2026-0001"
    assert p_dup.dgm_partner_code == "PTN-DGM-2026-0001"

    # Test 6: Sales-First Flexibility on `sale.order.action_confirm()` (Non-Blocking + Auto Companion Docs)
    so_path = os.path.join(ROOT_DIR, "addons/insilos_al2c/models/sale_order.py")
    with open(so_path, "r", encoding="utf-8") as f:
        so_src = f.read()
    assert "action_generate_onboarding_documents" in so_src, "sale_order.py must call action_generate_onboarding_documents on confirm"
    assert "[Sales-First Flex]" in so_src, "sale_order.py must post [Sales-First Flex] chatter note on confirm"

    p_sales_new = MockPartnerRecord(id=9105, name="Công ty Cổ phần Thương mại Mới", vat="0319998887")
    p_sales_new.env = mock_env
    p_sales_new._get_or_create_dgm_onboarding_folder = lambda: types.SimpleNamespace(id=3226)
    p_sales_new._render_companion_templates_payload = lambda: PartnerCls._render_companion_templates_payload(p_sales_new)
    p_sales_new._compute_dgm_onboarding_docs = lambda: PartnerCls._compute_dgm_onboarding_docs(p_sales_new)
    p_sales_new._compute_dgm_tier_and_terms = lambda: PartnerCls._compute_dgm_tier_and_terms(p_sales_new)
    assert p_sales_new.dgm_onboarding_state == "provisional"
    assert p_sales_new.dgm_provisional_code == "TMP-DGM-9105"
    PartnerCls.action_generate_onboarding_documents(p_sales_new)
    assert p_sales_new.dgm_onboarding_state == "docs_ready"
    assert p_sales_new.dgm_onboarding_doc_count == 4 and p_sales_new.dgm_all_companion_docs_ready is True

    # Test 7: SOP-DGM-07 Staff Augmentation Contract Lifecycle (`compute_staff_aug_monthly_settlement` & `action_generate_staff_aug_acceptance_doc`)
    staff_aug_path = os.path.join(ROOT_DIR, "addons/insilos_al2c/models/staff_augmentation_sop.py")
    assert os.path.exists(staff_aug_path), "Missing staff_augmentation_sop.py"

    class DummyValidationError(Exception):
        pass

    exc_mod.ValidationError = DummyValidationError
    sys.modules["odoo"] = odoo_mod
    sys.modules["odoo.exceptions"] = exc_mod
    try:
        spec_sa = importlib.util.spec_from_file_location("staff_augmentation_sop_test", staff_aug_path)
        mod_sa = importlib.util.module_from_spec(spec_sa)
        spec_sa.loader.exec_module(mod_sa)
    finally:
        if old_odoo is not None:
            sys.modules["odoo"] = old_odoo
        else:
            sys.modules.pop("odoo", None)
        if old_exc is not None:
            sys.modules["odoo.exceptions"] = old_exc
        else:
            sys.modules.pop("odoo.exceptions", None)

    StaffAugCls = mod_sa.SaleOrderStaffAugmentation

    class MockStaffAugOrder:
        def __init__(self, partner):
            self.id = 7701
            self.name = "SO-DGM-AIFIN-2610"
            self.partner_id = partner
            self.dgm_is_staff_augmentation = True
            self.dgm_min_monthly_hours = 140.0
            self.dgm_max_standard_hours = 180.0
            self.dgm_hourly_rate_vnd = 350000.0
            self.dgm_payment_term_days = 40
            self.dgm_replacement_notice_days = 30
            self.dgm_free_trial_days = 5
            self.env = mock_env

        def ensure_one(self):
            return self

        def compute_staff_aug_monthly_settlement(self, *a, **kw):
            return StaffAugCls.compute_staff_aug_monthly_settlement(self, *a, **kw)

        def action_generate_staff_aug_acceptance_doc(self, *a, **kw):
            return StaffAugCls.action_generate_staff_aug_acceptance_doc(self, *a, **kw)

    p_aifin = MockPartnerRecord(
        id=9007,
        name="CÔNG TY CỔ PHẦN AIFIN COMPANY GLOBAL",
        vat="0319631994",
        dgm_partner_group="strategic_b2b",
        dgm_partner_code="PTN-DGM-2026-0007",
        dgm_onboarding_state="approved",
    )
    p_aifin.dgm_onboarding_folder_id = types.SimpleNamespace(id=3227)
    so_aug = MockStaffAugOrder(p_aifin)

    # 7a. Within 140-180h SLA band (160h standard, 0 OT)
    res_std = so_aug.compute_staff_aug_monthly_settlement(160.0)
    assert res_std["sla_status"] == "within_sla_band"
    assert res_std["billable_std_hours"] == 160.0
    assert res_std["base_amount_vnd"] == 56_000_000.0
    assert res_std["vat_amount_vnd"] == 4_480_000
    assert res_std["total_with_vat_vnd"] == 60_480_000.0
    assert res_std["payment_term_days"] == 40
    assert res_std["payment_gate_ready"] is True

    # 7b. Under 140h minimum SLA warning (120h logged, not replacement trial)
    res_under = so_aug.compute_staff_aug_monthly_settlement(120.0)
    assert res_under["sla_status"] == "under_minimum_sla"
    assert res_under["billable_std_hours"] == 120.0
    assert res_under["base_amount_vnd"] == 42_000_000.0

    # 7c. Weekday OT (100%) + Weekend/Holiday OT (150%): 160h std + 10h weekday OT + 8h weekend OT
    res_ot = so_aug.compute_staff_aug_monthly_settlement(
        160.0, ot_weekday_hours=10.0, ot_weekend_hours=8.0
    )
    assert res_ot["ot_weekday_amount_vnd"] == 3_500_000.0
    assert res_ot["ot_weekend_amount_vnd"] == 4_200_000.0  # 8h * 350,000 * 1.5
    assert res_ot["subtotal_vnd"] == 63_700_000.0

    # 7d. 5-day Replacement Free Trial deduction (5 days * 8h = 40h deducted from 160h -> 120h billable)
    res_trial = so_aug.compute_staff_aug_monthly_settlement(
        160.0, is_replacement_trial=True
    )
    assert res_trial["trial_deducted_hours"] == 40.0
    assert res_trial["billable_std_hours"] == 120.0
    assert res_trial["base_amount_vnd"] == 42_000_000.0
    assert res_trial["sla_status"] == "within_sla_band"

    # 7e. Generate [TPL-ONB-05] Acceptance & Billing Certificate in Documents
    doc_05 = so_aug.action_generate_staff_aug_acceptance_doc(
        period_label="10/2026", logged_hours=160.0, ot_weekday_hours=10.0, ot_weekend_hours=8.0
    )
    assert doc_05 is not None and "[TPL-ONB-05]" in doc_05.name
    assert doc_05.owner_id is False and doc_05.access_internal == "edit"

    print("[✓] SOP-DGM-06 & SOP-DGM-07 Partner Tiering, Sales-First Confirm, Companion Docs (TPL-ONB-01..05), Staff Augmentation 140-180h SLA, OT 100%/150%, 5-Day Trial & Net 40 Gate verified")


def verify_k8s_partner_onboarding():
    import subprocess
    k8s_script = """
import os, psycopg2
conn = psycopg2.connect(
    dbname=os.environ.get('DB_NAME', 'innoria_prod'),
    user=os.environ.get('DB_USER', 'odoo'),
    password=os.environ.get('PGPASSWORD', ''),
    host=os.environ.get('DB_HOST', 'pgbouncer-service'),
    port=int(os.environ.get('DB_PORT', '6432')),
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM res_partner WHERE dgm_partner_code LIKE 'PTN-DGM-2026-000%' AND dgm_onboarding_state = 'approved' AND dgm_all_companion_docs_ready = TRUE;")
p_cnt = cur.fetchone()[0]
assert p_cnt >= 8, f'Expected >=8 canonical approved DGM partners on K8s, got {p_cnt}'

cur.execute("SELECT COUNT(*) FROM dgm_partner_onboarding_doc_rel;")
doc_cnt = cur.fetchone()[0]
assert doc_cnt >= 32, f'Expected >=32 companion docs on K8s, got {doc_cnt}'

cur.execute('''
    SELECT COUNT(*) FROM documents_document f
     WHERE f.type = 'folder' AND f.active = TRUE
       AND NOT EXISTS (SELECT 1 FROM documents_document c WHERE c.folder_id = f.id AND c.active = TRUE);
''')
empty_cnt = cur.fetchone()[0]
assert empty_cnt == 0, f'Expected 0 empty active folders on K8s, got {empty_cnt}'

cur.execute("SELECT COUNT(*) FROM knowledge_article WHERE name ILIKE 'SOP-DGM-06%' AND active = TRUE;")
kb_cnt = cur.fetchone()[0]
assert kb_cnt >= 1, 'Missing SOP-DGM-06 Knowledge Article on K8s'

cur.execute("SELECT COUNT(*) FROM knowledge_article WHERE name ILIKE 'SOP-DGM-07%' AND active = TRUE;")
kb07_cnt = cur.fetchone()[0]
assert kb07_cnt >= 1, 'Missing SOP-DGM-07 Knowledge Article on K8s'

cur.execute("SELECT COUNT(*) FROM knowledge_article WHERE name ILIKE 'SOP-DGM-09%' AND active = TRUE;")
kb09_cnt = cur.fetchone()[0]
assert kb09_cnt >= 1, 'Missing SOP-DGM-09 Knowledge Article on K8s'

cur.execute("SELECT COUNT(*) FROM product_template WHERE default_code IN ('SVC-ONSITE-SR', 'SVC-ONSITE-MID', 'ERP-360-SALES') AND active = TRUE;")
sku_cnt = cur.fetchone()[0]
assert sku_cnt == 3, f'Expected 3 SOP-DGM-07 SKUs on K8s, got {sku_cnt}'
conn.close()
assert os.path.exists('/app/insilos/addons/insilos_al2c/models/res_partner_onboarding.py'), 'Missing res_partner_onboarding.py on K8s pod'
assert os.path.exists('/app/insilos/addons/insilos_al2c/models/staff_augmentation_sop.py'), 'Missing staff_augmentation_sop.py on K8s pod'
assert os.path.exists('/app/insilos/addons/insilos_al2c/models/dgm_software_contract_templates.py'), 'Missing dgm_software_contract_templates.py on K8s pod'
print(f'K8S_SOP_DGM_06_07_OK partners={p_cnt} companion_docs={doc_cnt} empty_folders={empty_cnt} kb06={kb_cnt} kb07={kb07_cnt} kb09={kb09_cnt} skus={sku_cnt}')
"""
    # Dynamically discover active innoria-prod pod
    pod_name = "innoria-prod-app-7cdc9b8ddc-8st7m"
    try:
        discovered = subprocess.check_output(
            ["kubectl", "get", "pods", "-n", "production", "-l", "app=innoria-prod", "--field-selector=status.phase=Running", "-o", "jsonpath={.items[0].metadata.name}"],
            text=True,
        ).strip()
        if discovered:
            pod_name = discovered
    except Exception:
        pass

    proc = subprocess.run(
        [
            "kubectl", "exec", "-i", "-n", "production",
            pod_name, "-c", "innoria",
            "--", "python3", "-",
        ],
        input=k8s_script,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "K8S_SOP_DGM_06_07_OK" in proc.stdout, proc.stdout
    print(f"[✓] K8s live production (`innoria_prod` SOP-DGM-06 & SOP-DGM-07): {proc.stdout.strip()}")


def main():
    for db in ("insilos20_dev", "innoria_prod"):
        verify_db_partner_onboarding(db)
    verify_workflow_state_machine_and_gates()
    verify_k8s_partner_onboarding()
    print("[🎉] ALL SOP-DGM-06 & SOP-DGM-07 PARTNER ONBOARDING, STAFF AUGMENTATION & PAYMENT GATE CHECKS PASSED (EXIT 0)")


if __name__ == "__main__":
    main()

