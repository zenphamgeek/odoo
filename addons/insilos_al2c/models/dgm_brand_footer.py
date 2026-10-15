# -*- coding: utf-8 -*-
import base64
import html
import os
import re
from pathlib import Path

from odoo import api, models

_LOGO_CACHE = {}

_IMG_DIR = Path(__file__).resolve().parent.parent / 'static' / 'src' / 'img'

_VARIANT_FILENAMES = {
    'default': 'digimate_drive_logo.png',
    'green': 'digimate_drive_logo.png',
    'black': 'digimate_drive_logo_black.png',
    'white': 'digimate_drive_logo_white.png',
}


def get_digimate_logo_url(variant="default"):
    """Returns the web-accessible static path to the authentic Google Drive Digimate logo."""
    key = str(variant or 'default').strip().lower()
    fname = _VARIANT_FILENAMES.get(key, 'digimate_drive_logo.png')
    return f"/insilos_al2c/static/src/img/{fname}"


def get_digimate_logo_data_uri(variant="default"):
    """Reads the authentic Google Drive Digimate logo PNG from disk and returns a base64 data URI.
    Cached in memory for zero-I/O overhead across batch template generation.
    """
    key = str(variant or 'default').strip().lower()
    if key in _LOGO_CACHE:
        return _LOGO_CACHE[key]

    fname = _VARIANT_FILENAMES.get(key, 'digimate_drive_logo.png')
    fpath = _IMG_DIR / fname
    if not fpath.is_file():
        fpath = _IMG_DIR / 'digimate_drive_logo.png'

    if fpath.is_file():
        raw_bytes = fpath.read_bytes()
        b64_str = base64.b64encode(raw_bytes).decode('ascii')
        data_uri = f"data:image/png;base64,{b64_str}"
    else:
        data_uri = get_digimate_logo_url(variant=key)

    _LOGO_CACHE[key] = data_uri
    return data_uri


def render_dgm_brand_header_html(doc_title="", doc_code=None, sop_ref=None):
    """Renders the standardized Digimate Executive Brand Header with the authentic Google Drive Logo."""
    logo_uri = get_digimate_logo_data_uri("default")
    safe_title = html.escape(str(doc_title or 'HỒ SƠ QUẢN TRỊ DOANH NGHIỆP DIGIMATE'))
    safe_code = html.escape(str(doc_code or 'DGM-STD-2026'))
    safe_sop = html.escape(str(sop_ref or 'SOP-DGM'))

    return f"""<header class="dgm-brand-header" data-dgm-header="drive-logo-v1" style="border-bottom: 2px solid var(--insilos-border-subtle, #1e3a8a); padding-bottom: 14px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap;">
  <div style="display: flex; align-items: center; gap: 14px;">
    <img class="dgm-header-drive-logo" src="{logo_uri}" alt="Digimate Official Brand Logo" data-logo-source="google-drive-logo-folder" style="height:40px; width:auto; object-fit:contain; display:block;" />
    <div style="line-height: 1.35;">
      <div style="font-weight: 700; font-size: 14px; color: var(--insilos-text-primary, #1e293b);">CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</div>
      <div style="font-size: 11.5px; color: var(--insilos-text-secondary, #475569);">MST: <strong>0317958465</strong> • Mã ĐV BHXH: <strong>TZ0857G</strong> • Ký hiệu HĐĐT: <strong>1C26TAA</strong></div>
      <div style="font-size: 11px; color: var(--insilos-text-secondary, #64748b);">{safe_title}</div>
    </div>
  </div>
  <div style="text-align: right;">
    <span style="display: inline-block; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 11.5px; background: var(--insilos-bg-subtle, #dbeafe); color: var(--insilos-text-primary, #1e40af); border: 1px solid var(--insilos-border-subtle, #93c5fd);">
      {safe_code} • {safe_sop}
    </span>
  </div>
</header>"""


def render_dgm_brand_footer_html(
    doc_code=None,
    sop_ref=None,
    classification="INTERNAL / B2B CONFIDENTIAL",
):
    """Renders the canonical standardized Digimate Brand Footer featuring the authentic Google Drive Logo,
    statutory tax/insurance/e-invoice identifiers, and SOP governance metadata.
    """
    logo_uri = get_digimate_logo_data_uri("default")
    safe_code = html.escape(str(doc_code or 'DGM-STD-2026'))
    safe_sop = html.escape(str(sop_ref or 'SOP-DGM'))
    safe_class = html.escape(str(classification or 'INTERNAL / B2B CONFIDENTIAL'))

    return f"""<footer class="dgm-brand-footer" data-dgm-footer="drive-logo-v1" style="margin-top: 32px; padding-top: 16px; border-top: 2px solid var(--insilos-border-subtle, #cbd5e1); font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size: 11.5px; color: var(--insilos-text-secondary, #475569); background: var(--insilos-bg-surface, transparent); page-break-inside: avoid;">
  <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; flex-wrap: wrap;">
    <div style="display: flex; align-items: center; gap: 12px; min-width: 190px;">
      <img class="dgm-footer-drive-logo" src="{logo_uri}" alt="Digimate Official Brand Logo" data-logo-source="google-drive-logo-folder" style="height:38px; width:auto; object-fit:contain; display:block;" />
    </div>
    <div style="flex: 1 1 360px; line-height: 1.45;">
      <div style="font-weight: 700; color: var(--insilos-text-primary, #1e293b); font-size: 12px;">CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC)</div>
      <div><strong>MST (Tax ID):</strong> 0317958465 | <strong>Mã ĐV BHXH:</strong> TZ0857G | <strong>Ký hiệu HĐĐT:</strong> 1C26TAA</div>
      <div><strong>Trụ sở:</strong> 344–346 Nguyễn Trọng Tuyển, Phường 2, Quận Tân Bình, TP. Hồ Chí Minh, Việt Nam</div>
      <div><strong>Website:</strong> digimate.vn • <strong>Email:</strong> contact@digimate.vn</div>
    </div>
    <div style="text-align: right; min-width: 210px; line-height: 1.45; font-size: 11px;">
      <div><strong>Mã Tài liệu (Doc Code):</strong> <code>{safe_code}</code></div>
      <div><strong>Quy trình (SOP Ref):</strong> <code>{safe_sop}</code></div>
      <div><strong>Phân loại (Class):</strong> {safe_class}</div>
      <div style="color: var(--insilos-text-secondary, #64748b); margin-top: 2px;">Digimate Enterprise Governance • Drive Brand Standard v2026.10</div>
    </div>
  </div>
</footer>"""


_EXISTING_FOOTER_RE = re.compile(
    r'<footer\b[^>]*\bdata-dgm-footer=["\']drive-logo-v1["\'][^>]*>[\s\S]*?</footer>',
    re.IGNORECASE,
)


def wrap_dgm_branded_html_document(
    body_html,
    title="Digimate Enterprise Document",
    doc_code="DGM-DOC-2026",
    sop_ref="SOP-DGM",
    classification="INTERNAL / B2B CONFIDENTIAL",
    include_header=False,
    doc_title=None,
    **kw,
):
    """Idempotently injects the standardized Digimate Brand Footer (and optional Brand Header)
    into any HTML document or fragment.
    """
    effective_title = doc_title or title or "Digimate Enterprise Document"
    raw = str(body_html or '')
    footer_html = render_dgm_brand_footer_html(
        doc_code=doc_code,
        sop_ref=sop_ref,
        classification=classification,
    )
    header_html = (
        render_dgm_brand_header_html(doc_title=effective_title, doc_code=doc_code, sop_ref=sop_ref)
        if include_header
        else ''
    )

    # Case 1: Full HTML document containing <html or <!DOCTYPE
    if '<html' in raw.lower() or '<!doctype' in raw.lower():
        updated = raw
        if include_header and 'data-dgm-header="drive-logo-v1"' not in updated:
            body_open_match = re.search(r'<body\b[^>]*>', updated, flags=re.IGNORECASE)
            if body_open_match:
                insert_pos = body_open_match.end()
                updated = updated[:insert_pos] + "\n" + header_html + "\n" + updated[insert_pos:]

        if _EXISTING_FOOTER_RE.search(updated):
            updated = _EXISTING_FOOTER_RE.sub(lambda _m: footer_html, updated, count=1)
        else:
            body_close_match = re.search(r'</body\s*>', updated, flags=re.IGNORECASE)
            if body_close_match:
                insert_pos = body_close_match.start()
                updated = updated[:insert_pos] + "\n" + footer_html + "\n" + updated[insert_pos:]
            else:
                updated = updated + "\n" + footer_html
        return updated

    # Case 2: HTML fragment -> wrap into a full HTML5 document with print & semantic CSS variables
    safe_title = html.escape(str(title or 'Digimate Enterprise Document'))
    if _EXISTING_FOOTER_RE.search(raw):
        content_with_footer = _EXISTING_FOOTER_RE.sub(lambda _m: footer_html, raw, count=1)
    else:
        content_with_footer = f"{raw}\n{footer_html}"

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8"/>
<title>{safe_title}</title>
<style>
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
    color: var(--insilos-text-primary, #1e293b);
    background: var(--insilos-bg-card, #fcfcfd);
    margin: 28px auto;
    max-width: 980px;
    padding: 0 16px;
    line-height: 1.55;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
  }}
  th, td {{
    border: 1px solid var(--insilos-border-subtle, #cbd5e1);
    padding: 8px 12px;
    font-size: 13px;
    text-align: left;
  }}
  th {{
    background: var(--insilos-bg-subtle, #e2e8f0);
  }}
  @media print {{
    .dgm-brand-footer {{
      page-break-inside: avoid;
    }}
  }}
</style>
</head>
<body>
{header_html}
{content_with_footer}
</body>
</html>"""


_BaseAbstractModel = getattr(models, 'AbstractModel', getattr(models, 'Model', object))


class DgmBrandFooterMixin(_BaseAbstractModel):
    _name = 'dgm.brand.footer.mixin'
    _description = 'Digimate Official Google Drive Logo & Brand Footer Mixin'

    @api.model
    def get_digimate_logo_data_uri(self, variant="default"):
        return get_digimate_logo_data_uri(variant=variant)

    @api.model
    def get_digimate_logo_url(self, variant="default"):
        return get_digimate_logo_url(variant=variant)

    @api.model
    def render_dgm_brand_header_html(self, doc_title="", doc_code=None, sop_ref=None):
        return render_dgm_brand_header_html(
            doc_title=doc_title,
            doc_code=doc_code,
            sop_ref=sop_ref,
        )

    @api.model
    def render_dgm_brand_footer_html(
        self,
        doc_code=None,
        sop_ref=None,
        classification="INTERNAL / B2B CONFIDENTIAL",
    ):
        return render_dgm_brand_footer_html(
            doc_code=doc_code,
            sop_ref=sop_ref,
            classification=classification,
        )

    @api.model
    def wrap_dgm_branded_html_document(
        self,
        body_html,
        title="Digimate Enterprise Document",
        doc_code="DGM-DOC-2026",
        sop_ref="SOP-DGM",
        classification="INTERNAL / B2B CONFIDENTIAL",
        include_header=False,
    ):
        return wrap_dgm_branded_html_document(
            body_html=body_html,
            title=title,
            doc_code=doc_code,
            sop_ref=sop_ref,
            classification=classification,
            include_header=include_header,
        )
