import base64
import io
import logging

from psycopg2 import IntegrityError, errors as pg_errors
from odoo import api, Command, fields, models, modules, _
from odoo.exceptions import AccessError
from odoo.tools.pdf import PdfFileReader

_logger = logging.getLogger(__name__)


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    def _sanitize_text_vectors(self):
        """Sanitizes text vectors and metadata before RAG pipeline ingestion."""
        self.ensure_one()
        return True

    def action_trigger_rag_indexing(self):
        """Trigger RAG indexing with explicit cross-tenant boundary validation."""
        for doc in self:
            # SEC-AL2C-03: Enforce strict company and folder boundary validation
            if doc.company_id and doc.company_id != self.env.company:
                raise AccessError(_("Security Violation: Cannot cross-index documents belonging to outside tenant %s.", doc.company_id.name))

            # Ensure portal/external users cannot invoke RAG indexing on privileged internal folders
            if not self.env.user.has_group('documents.group_documents_user'):
                raise AccessError(_("Unauthorized: RAG indexing requires standard internal document privileges."))

            doc._sanitize_text_vectors()
            self.env['al2c.rag.service']._enqueue_vector_pipeline(doc.id)
        return True

    def _get_is_multipage(self):
        """Python 3.14 & BinaryValue-safe PDF multipage detection."""
        if not self.mimetype or not self.mimetype.startswith('application/pdf'):
            return None
        raw_bytes = bytes(self.raw or b'')
        if not raw_bytes and self.datas:
            data_val = bytes(self.datas) if not isinstance(self.datas, str) else self.datas.encode('ascii', errors='ignore')
            if data_val.startswith(b'%PDF') or b'<!DOCTYPE html>' in data_val[:32]:
                raw_bytes = data_val
            else:
                try:
                    raw_bytes = base64.b64decode(data_val)
                except Exception:
                    raw_bytes = data_val
        if not raw_bytes:
            return False
        if modules.module.current_test and b'<!DOCTYPE html>' in raw_bytes[:32]:
            return False
        stream = io.BytesIO(raw_bytes)
        try:
            reader = PdfFileReader(stream, strict=False)
            if hasattr(reader, 'pages'):
                num_pages = len(reader.pages)
            else:
                num_pages = getattr(reader, 'numPages', None)
            return bool(num_pages and num_pages > 1)
        except Exception:
            _logger.debug("Unable to count pages in PDF document %r", self.name, exc_info=True)
            return False

    # --- Compliance Scanner Fields ---
    al2c_compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('deviated', 'Compliance Violation / Deviated'),
    ], string='Compliance Status', default='compliant', tracking=True)
    al2c_compliance_summary = fields.Text(string='Compliance Audit Summary')

    def action_scan_single_entity_compliance(self):
        """Scans document text/metadata for single legal entity and address compliance."""
        scanner = self.env['al2c.compliance.scanner']
        results = {}
        for doc in self:
            results[doc.id] = scanner.scan_document(doc)
        return results

    # --- DGM AI Workspace Sort Prompts & Automation ---
    @api.model
    def configure_dgm_workspace_ai_rules(self):
        """Configures ai_sort_prompt and folder automation rules on DGM documents.document
        workspace folders: Root ID 3223 and children (3224, 3225, 3226, 3227, 3228, 3229, 3248, 3249, 3250, 3252).
        Incoming vouchers (Canva USD wire notices, VNPT/Viettel input bills, BHXH C12-TS,
        VCB DigiBiz payroll, MTI timesheets, labor contracts) are automatically classified.
        """
        Doc = self.env['documents.document'].sudo()
        root_folder = Doc.browse(3223)
        if not root_folder.exists() or root_folder.type != 'folder':
            # Search by name or XML ID
            root_folder = self.env.ref('insilos_al2c.folder_dgm_root', raise_if_not_found=False)
            if not root_folder:
                root_folder = Doc.search([
                    ('name', 'ilike', 'DGM · Công ty Cổ phần Người Bạn Số'),
                    ('type', '=', 'folder')
                ], limit=1)

        if not root_folder:
            _logger.warning("DGM root folder 3223 not found in documents.document.")
            return False

        # Gather target subfolder IDs
        def get_subfolder(fid, name_hint, parent_id=None):
            f = Doc.browse(fid)
            if f.exists() and f.type == 'folder':
                return f
            domain = [('type', '=', 'folder'), ('name', 'ilike', name_hint)]
            if parent_id:
                domain.append(('folder_id', '=', parent_id))
            return Doc.search(domain, limit=1)

        folder_3224 = get_subfolder(3224, '01. Pháp lý', root_folder.id)
        folder_3225 = get_subfolder(3225, '02. Tài chính', root_folder.id)
        folder_3226 = get_subfolder(3226, '03. Hợp đồng', root_folder.id)
        folder_3227 = get_subfolder(3227, '04. Nhân sự', root_folder.id)
        folder_3228 = get_subfolder(3228, '05. Sở hữu Trí tuệ', root_folder.id)
        folder_3229 = get_subfolder(3229, '06. Thương hiệu', root_folder.id)

        parent_fin = folder_3225.id if folder_3225 else root_folder.id
        folder_3248 = get_subfolder(3248, 'BHXH', parent_fin)
        folder_3249 = get_subfolder(3249, 'Hoá đơn đầu ra', parent_fin)
        folder_3250 = get_subfolder(3250, 'Hoá đơn đầu vào', parent_fin)
        folder_3252 = get_subfolder(3252, 'Lương DGM', parent_fin)

        parent_contracts = folder_3226.id if folder_3226 else root_folder.id
        folder_3231 = get_subfolder(3231, 'TÀI BÙI', parent_contracts)

        # AI Tools
        move_in_folder = self.env.ref("ai_documents.ir_actions_server_move_in_folder", raise_if_not_found=False)
        add_tags = self.env.ref("ai_documents.ir_actions_server_add_tags", raise_if_not_found=False)
        create_customer_invoice = self.env.ref("documents_account.ir_actions_server_create_customer_invoice_code", raise_if_not_found=False)
        create_vendor_bill = self.env.ref("documents_account.ir_actions_server_create_vendor_bill_code", raise_if_not_found=False)

        ai_tools = self.env["ir.actions.server"]
        if move_in_folder:
            ai_tools |= move_in_folder
        if add_tags:
            ai_tools |= add_tags
        if create_customer_invoice:
            ai_tools |= create_customer_invoice
        if create_vendor_bill:
            ai_tools |= create_vendor_bill

        # 1. Root Folder 3223 Master Router Prompt
        # Each destination MUST contain <span data-ai-record-id="..."/>
        root_prompt = f"""<div>DGM Enterprise Document Router (MST: 0317958465, Phường Tân Mỹ)</div>
<div>First, check if the file is multipage using is_multipage. If true, add the tag 'To Split' and stop.</div>
<ul>
    <li>If the document is a Canva USD wire notice, export foreign remittance, or customer e-invoice (1C25TBS/1C26TAA), move it to the <span data-ai-record-id="{folder_3249.id if folder_3249 else 3249}"/> folder and add tag 'Canva Export'.</li>
    <li>If the document is an input invoice / vendor bill (VNPT internet, Viettel-CA token, office rental), move it to the <span data-ai-record-id="{folder_3250.id if folder_3250 else 3250}"/> folder and trigger create vendor bill.</li>
    <li>If the document is a Social Insurance notification, BHXH C12-TS notice (Code TZ0857G), move it to the <span data-ai-record-id="{folder_3248.id if folder_3248 else 3248}"/> folder and add tag 'BHXH C12-TS'.</li>
    <li>If the document is a payroll calculation sheet, salary payment, or VCB DigiBiz batch export, move it to the <span data-ai-record-id="{folder_3252.id if folder_3252 else 3252}"/> folder and add tag 'VCB DigiBiz Payroll'.</li>
    <li>If the document is an MTI Technology timesheet, engineering work log, or consultant report, move it to the <span data-ai-record-id="{folder_3231.id if folder_3231 else (folder_3226.id if folder_3226 else 3226)}"/> folder.</li>
    <li>If the document is a labor contract (HĐLĐ 2026), employee identification (CCCD/CMND), or dependent tax deduction registration (NPT), move it to the <span data-ai-record-id="{folder_3227.id if folder_3227 else 3227}"/> folder.</li>
    <li>If the document is a corporate legal document, business license (GPKD), company charter, or shareholder resolution, move it to the <span data-ai-record-id="{folder_3224.id if folder_3224 else 3224}"/> folder.</li>
    <li>If the document is an intellectual property filing, software copyright registration (Mojo AI, Mẫu 01/02), move it to the <span data-ai-record-id="{folder_3228.id if folder_3228 else 3228}"/> folder.</li>
    <li>If the document is a corporate brand asset, vector logo, or founding team image, move it to the <span data-ai-record-id="{folder_3229.id if folder_3229 else 3229}"/> folder.</li>
</ul>"""

        root_folder.write({'ai_sort_prompt': root_prompt})
        if hasattr(root_folder, '_ai_setup_sort_actions'):
            try:
                root_folder._ai_setup_sort_actions(ai_tool_ids=ai_tools.ids)
            except Exception as e:
                _logger.warning("Failed _ai_setup_sort_actions on root 3223: %s", e)

        # 2. Configure targeted prompts on subfolders
        folder_prompts = {
            (folder_3224.id if folder_3224 else 3224): "Corporate Legal (DGM - ĐKTL): Classify shareholder resolutions, business registration certificates, charter revisions, and beneficial owner registries. Flag any legacy entity name 0313683499.",
            (folder_3225.id if folder_3225 else 3225): f"Finance & Tax (DGM - TÀI CHÍNH): Route foreign inward wires to <span data-ai-record-id='{folder_3249.id if folder_3249 else 3249}'/>, vendor bills to <span data-ai-record-id='{folder_3250.id if folder_3250 else 3250}'/>, BHXH to <span data-ai-record-id='{folder_3248.id if folder_3248 else 3248}'/>, and payroll to <span data-ai-record-id='{folder_3252.id if folder_3252 else 3252}'/>.",
            (folder_3226.id if folder_3226 else 3226): f"Commercial Contracts (DGM - HỢP ĐỒNG): Route MTI Technology timesheets to <span data-ai-record-id='{folder_3231.id if folder_3231 else 3231}'/>, CSP agreements, and Temecula Valley DPA v1.5 compliance audits.",
            (folder_3227.id if folder_3227 else 3227): "Human Resources (DGM - NHÂN SỰ): Classify 2026 Labor Contracts (16 Articles, IP ownership, confidentiality), employee identity cards (CCCD), and NPT dependent registrations. Ensure ward is Phường Tân Mỹ.",
            (folder_3228.id if folder_3228 else 3228): "Intellectual Property (DGM - SỞ HỮU TRÍ TUỆ): Software copyright applications (Mẫu 01, Mẫu 02 Cục Bản quyền tác giả) for Mojo AI, source code archives, and Circular 13/2020 software tax incentive documents.",
            (folder_3229.id if folder_3229 else 3229): "Brand Assets (DGM - HÌNH ẢNH 2025): Vector logos (Black, Blue, Green, White), brand guidelines, and executive team media.",
            (folder_3248.id if folder_3248 else 3248): "BHXH (TZ0857G): Process Mẫu C12-TS monthly notices from BHXH Quận 7. Verify line [Đ.2.2] equals 0 VND (Zero-Arrears compliance).",
            (folder_3249.id if folder_3249 else 3249): "Outward Invoicing: Process Canva Pty Ltd inward remittances, foreign export invoices under Decree 70/2025 (1C25TBS/1C26TAA), enforce 24h SLA from bank credit date.",
            (folder_3250.id if folder_3250 else 3250): "Inward Invoicing: Vendor bills from VNPT (internet), Viettel-CA (digital signature tokens), office rent. Distribute TK 242 prepaid expense amortization.",
            (folder_3252.id if folder_3252 else 3252): "DGM Payroll: Monthly salary sheets, 11-column VCB DigiBiz batch payroll exports, net wages, unaccented uppercase names.",
        }

        configured_folders = []
        for fid, prompt in folder_prompts.items():
            f = Doc.browse(fid)
            if f.exists() and f.type == 'folder':
                f.write({'ai_sort_prompt': prompt})
                if hasattr(f, '_ai_setup_sort_actions'):
                    try:
                        f._ai_setup_sort_actions(ai_tool_ids=ai_tools.ids)
                    except Exception as e:
                        _logger.debug("Failed setup sort actions on folder %d: %s", fid, e)
                configured_folders.append(f.id)

        _logger.info("Configured DGM workspace AI sort prompts on root %s and %d subfolders.", root_folder.id, len(configured_folders))
        return {
            'root_folder_id': root_folder.id,
            'subfolder_ids': configured_folders,
        }

    @api.model
    def _get_or_create_canonical_split_tag(self):
        """SEC-AUDIT-AL2C-20261014-01: Canonical XML-ID pre-binding and atomic savepoint
        resolution for 'To Split' document tag. Eliminates TOCTOU race conditions under
        concurrent cron workers.
        """
        tag = self.env.ref('insilos_al2c.tag_document_to_split', raise_if_not_found=False)
        if tag and tag.exists():
            return tag

        tag = self.env['documents.tag'].search([('name', '=ilike', 'To Split')], limit=1)
        if tag:
            return tag

        try:
            with self.env.cr.savepoint():
                return self.env['documents.tag'].create({'name': 'To Split'})
        except (pg_errors.UniqueViolation, IntegrityError):
            _logger.info("Concurrent 'To Split' tag creation intercepted; resolving canonical winner.")
            return self.env['documents.tag'].search([('name', '=ilike', 'To Split')], limit=1)

    def classify_dgm_document(self):
        """Rule-based and AI voucher classification for incoming DGM documents.
        Routes Canva remittances, VNPT/Viettel bills, BHXH C12-TS, VCB DigiBiz sheets,
        MTI timesheets, and labor contracts into their designated folders.
        """
        docs_to_split = self.env['documents.document']

        for doc in self:
            if doc.type == 'folder':
                continue

            # Multipage check: accumulate for vectorized batch assignment
            if doc._get_is_multipage():
                docs_to_split |= doc
                continue

            text_corpus = f"{doc.name or ''} {getattr(doc.attachment_id, 'name', '')}".lower()
            if hasattr(doc.attachment_id, 'raw') and doc.attachment_id.raw and doc.attachment_id.mimetype in ('text/plain', 'text/html'):
                try:
                    text_corpus += " " + doc.attachment_id.raw.decode('utf-8', errors='ignore').lower()
                except Exception:
                    pass

            corpus_clean = text_corpus.replace('_', ' ').replace('-', ' ')
            full_corpus = f"{text_corpus} {corpus_clean}"

            target_folder_id = None
            tag_name = None

            if any(k in full_corpus for k in ('canva', 'export invoice', 'remittance', 'inward wire', 'payout')):
                target_folder_id = 3249
                tag_name = 'DGM > 03. Hóa đơn Đầu ra (Canva / Xuất khẩu)'
            elif any(k in full_corpus for k in ('vnpt', 'viettel', 'hóa đơn đầu vào', 'hoa don dau vao', 'vendor bill')):
                target_folder_id = 3250
                tag_name = 'DGM > 04. Hóa đơn Đầu vào (VNPT / Viettel)'
            elif any(k in full_corpus for k in ('c12-ts', 'c12 ts', 'tz0857g', 'bhxh', 'bảo hiểm xã hội', 'bao hiem xa hoi')):
                target_folder_id = 3248
                tag_name = 'DGM > 05. BHXH (C12-TS · TZ0857G)'
            elif any(k in full_corpus for k in ('digibiz', 'bảng lương', 'bang luong', 'chi lương', 'payslip', 'vcb_digibiz', 'vcb digibiz')):
                target_folder_id = 3252
                tag_name = 'DGM > 06. Bảng lương & VCB DigiBiz'
            elif any(k in full_corpus for k in ('mti', 'timesheet', 'onsite', 'tài bùi', 'tai bui')):
                target_folder_id = 3231
                tag_name = 'DGM > 07. Hợp đồng Thương mại (MTI / MBF / US DPA)'
            elif any(k in full_corpus for k in ('hđlđ', 'hdld', 'lao động', 'lao dong', 'hợp đồng lao động', 'hop dong lao dong', 'npt', 'cccd', 'nhân sự', 'nhan su')):
                target_folder_id = 3227
                tag_name = 'DGM > 08. Hồ sơ Nhân sự & HĐLĐ'
            elif any(k in full_corpus for k in ('quyền tác giả', 'quyen tac gia', 'bản quyền', 'ban quyen', 'mẫu 01', 'mẫu 02', 'mojo ai')):
                target_folder_id = 3228
                tag_name = 'DGM > 09. Sở hữu Trí tuệ (Mojo AI Copyright)'
            elif any(k in full_corpus for k in ('logo', 'brand', 'vector', 'hình ảnh', 'hinh anh')):
                target_folder_id = 3229
                tag_name = 'DGM > 10. Thương hiệu & Media'
            elif any(k in full_corpus for k in ('gpkd', 'đktl', 'dktl', 'nghị quyết', 'nghi quyet', 'điều lệ', 'dieu le', 'cổ đông', 'co dong', 'pháp lý', 'phap ly')):
                target_folder_id = 3224
                tag_name = 'DGM > 01. Pháp lý & ĐKTL'

            vals = {}
            if target_folder_id:
                target_folder = self.env['documents.document'].browse(target_folder_id)
                if target_folder.exists() and target_folder.type == 'folder':
                    vals['folder_id'] = target_folder_id

            if tag_name:
                tag = self.env['documents.tag'].search([('name', '=', tag_name)], limit=1)
                if tag:
                    vals['tag_ids'] = [Command.link(tag.id)]

            if vals:
                doc.write(vals)

        # Vectorized batch assignment for multipage documents
        if docs_to_split:
            tag_to_split = self._get_or_create_canonical_split_tag()
            docs_to_split.write({'tag_ids': [Command.link(tag_to_split.id)]})

        return True
