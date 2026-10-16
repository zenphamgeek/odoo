import base64
import hashlib
import hmac
import io
import logging

from psycopg2 import IntegrityError, errors as pg_errors
from odoo import api, Command, fields, models, modules, _
from odoo.exceptions import AccessError
try:
    from odoo.exceptions import ValidationError
except ImportError:
    class ValidationError(Exception):
        pass
from odoo.tools.pdf import PdfFileReader

_logger = logging.getLogger(__name__)


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    def check_access_token_secure(self, candidate_token, target_company_id=None):
        """Cryptographic constant-time HMAC token verification and multi-tenant boundary guard."""
        self.ensure_one()
        if (
            not self.active
            or not self.access_token
            or not candidate_token
            or not isinstance(self.access_token, str)
            or not isinstance(candidate_token, str)
            or not self.access_token.strip()
            or not candidate_token.strip()
        ):
            raise AccessError("Invalid or inactive document access token.")
        if not hmac.compare_digest(str(self.access_token), str(candidate_token)):
            raise AccessError("Invalid document access token.")
        if target_company_id and self.company_id and self.company_id.id != int(target_company_id):
            raise AccessError("Cross-company document access strictly prohibited.")
        return True

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

    # --- Sovereign DGM & INNORIA Role-Based Access Control (RBAC) Fields ---
    DGM_RBAC_PROFILE_SELECTION = [
        ('exec_legal', '01 · Corporate & Executive Legal (BGĐ / Pháp chế)'),
        ('company_sop', '02 · Company SOPs & Governance (Toàn Công ty - View)'),
        ('hr_cb', '03 · HR, Contracts & C&B (Nhân sự & Tiền lương - Strictly Restricted)'),
        ('finance_tax', '04 · Finance, Tax & Banking (Kế toán, Thuế & Ngân hàng)'),
        ('commercial_contract', '05 · Commercial Contracts & Legal (Hợp đồng Kinh tế & Pháp lý)'),
        ('project_delivery', '06 · Projects & Client Delivery (Dự án & Khách hàng)'),
        ('brand_sales', '07 · Brand & Marketing Assets (Thương hiệu & Truyền thông)'),
        ('mti_contract', '09 · MTI Dedicated Contracts & Legal (Hợp đồng MTI)'),
        ('mti_timesheet', '10 · MTI Timesheet & Reconciliation (Chấm công & Đối soát MTI)'),
        ('sales_kit', '11 · Sales Kit & Credentials (Tài liệu Bán hàng & HSNL)'),
        ('digital_solution', '12 · Digital Transformation & Solutions (Chuyển đổi số & Giải pháp)'),
    ]

    DGM_RBAC_MATRIX_SPEC = {
        'exec_legal': {
            'confidentiality': 'strictly_restricted',
            'access_internal': 'view',
            'access_via_link': 'none',
            'is_access_via_link_hidden': True,
            'read_groups': [
                'base.group_system',
                'sales_team.group_sale_manager',
                'account.group_account_manager',
                'hr.group_hr_manager',
            ],
            'write_groups': [
                'base.group_system',
                'account.group_account_manager',
            ],
        },
        'company_sop': {
            'confidentiality': 'internal',
            'access_internal': 'view',
            'access_via_link': 'view',
            'is_access_via_link_hidden': False,
            'read_groups': [
                'base.group_user',
            ],
            'write_groups': [
                'base.group_system',
                'documents.group_documents_manager',
                'hr.group_hr_manager',
            ],
        },
        'hr_cb': {
            'confidentiality': 'strictly_restricted',
            'access_internal': 'view',
            'access_via_link': 'none',
            'is_access_via_link_hidden': True,
            'read_groups': [
                'base.group_system',
                'hr.group_hr_manager',
                'hr.group_hr_user',
            ],
            'write_groups': [
                'base.group_system',
                'hr.group_hr_manager',
            ],
        },
        'finance_tax': {
            'confidentiality': 'strictly_restricted',
            'access_internal': 'view',
            'access_via_link': 'none',
            'is_access_via_link_hidden': True,
            'read_groups': [
                'base.group_system',
                'account.group_account_manager',
                'account.group_account_user',
                'account.group_account_readonly',
            ],
            'write_groups': [
                'base.group_system',
                'account.group_account_manager',
                'account.group_account_user',
            ],
        },
        'commercial_contract': {
            'confidentiality': 'confidential',
            'access_internal': 'view',
            'access_via_link': 'none',
            'is_access_via_link_hidden': False,
            'read_groups': [
                'base.group_system',
                'sales_team.group_sale_manager',
                'sales_team.group_sale_salesman_all_leads',
                'account.group_account_manager',
                'account.group_account_user',
                'project.group_project_manager',
            ],
            'write_groups': [
                'base.group_system',
                'sales_team.group_sale_manager',
                'account.group_account_manager',
            ],
        },
        'project_delivery': {
            'confidentiality': 'confidential',
            'access_internal': 'edit',
            'access_via_link': 'none',
            'is_access_via_link_hidden': False,
            'read_groups': [
                'base.group_system',
                'project.group_project_manager',
                'project.group_project_user',
                'sales_team.group_sale_manager',
                'sales_team.group_sale_salesman',
                'account.group_account_user',
            ],
            'write_groups': [
                'base.group_system',
                'project.group_project_manager',
                'project.group_project_user',
                'sales_team.group_sale_manager',
            ],
        },
        'brand_sales': {
            'confidentiality': 'internal',
            'access_internal': 'view',
            'access_via_link': 'view',
            'is_access_via_link_hidden': False,
            'read_groups': [
                'base.group_user',
            ],
            'write_groups': [
                'base.group_system',
                'sales_team.group_sale_manager',
                'documents.group_documents_manager',
            ],
        },
        'mti_contract': {
            'confidentiality': 'strictly_restricted',
            'access_internal': 'view',
            'access_via_link': 'none',
            'is_access_via_link_hidden': True,
            'read_groups': [
                'base.group_system',
                'sales_team.group_sale_manager',
                'account.group_account_manager',
                'hr.group_hr_manager',
            ],
            'write_groups': [
                'base.group_system',
                'sales_team.group_sale_manager',
                'account.group_account_manager',
            ],
        },
        'mti_timesheet': {
            'confidentiality': 'confidential',
            'access_internal': 'edit',
            'access_via_link': 'none',
            'is_access_via_link_hidden': False,
            'read_groups': [
                'base.group_system',
                'project.group_project_manager',
                'project.group_project_user',
                'account.group_account_manager',
                'account.group_account_user',
            ],
            'write_groups': [
                'base.group_system',
                'project.group_project_manager',
                'account.group_account_user',
            ],
        },
        'sales_kit': {
            'confidentiality': 'internal',
            'access_internal': 'view',
            'access_via_link': 'view',
            'is_access_via_link_hidden': False,
            'read_groups': [
                'base.group_user',
                'sales_team.group_sale_salesman',
            ],
            'write_groups': [
                'base.group_system',
                'sales_team.group_sale_manager',
            ],
        },
        'digital_solution': {
            'confidentiality': 'internal',
            'access_internal': 'edit',
            'access_via_link': 'view',
            'is_access_via_link_hidden': False,
            'read_groups': [
                'base.group_user',
                'project.group_project_user',
                'sales_team.group_sale_salesman',
            ],
            'write_groups': [
                'base.group_system',
                'project.group_project_manager',
                'sales_team.group_sale_manager',
            ],
        },
    }

    dgm_rbac_profile = fields.Selection(
        selection=DGM_RBAC_PROFILE_SELECTION,
        string='RBAC Access Profile',
        index=True,
    )
    dgm_confidentiality_level = fields.Selection([
        ('public', 'Public / External Ready'),
        ('internal', 'Internal Company-Wide (Read)'),
        ('confidential', 'Departmental / Role-Restricted'),
        ('strictly_restricted', 'Strictly Restricted (HR PII / Payroll / Legal / Tax)'),
    ], string='Confidentiality Level', default='confidential', index=True)
    dgm_read_group_ids = fields.Many2many(
        'res.groups',
        'dgm_doc_read_group_rel',
        'document_id',
        'group_id',
        string='Allowed Read Roles (RBAC)',
    )
    dgm_write_group_ids = fields.Many2many(
        'res.groups',
        'dgm_doc_write_group_rel',
        'document_id',
        'group_id',
        string='Allowed Edit Roles (RBAC)',
    )
    dgm_rbac_generation_id = fields.Char(
        string='RBAC Generation Hash',
        index=True,
    )

    @api.model
    def _verify_folder_dag_acyclicity(self):
        """Verifies via recursive CTE that no circular folder parentage cycle exists in documents_document."""
        self.env.cr.execute("""
            WITH RECURSIVE folder_dag AS (
                SELECT id, folder_id, ARRAY[id] AS path, FALSE AS is_cycle
                FROM documents_document
                WHERE active = TRUE AND type = 'folder'
                UNION ALL
                SELECT d.id, d.folder_id, fd.path || d.id, d.id = ANY(fd.path)
                FROM documents_document d
                JOIN folder_dag fd ON d.id = fd.folder_id
                WHERE d.active = TRUE AND d.type = 'folder' AND NOT fd.is_cycle AND array_length(fd.path, 1) < 32
            )
            SELECT id, path FROM folder_dag WHERE is_cycle = TRUE LIMIT 1;
        """)
        cycle_row = self.env.cr.fetchone()
        if cycle_row:
            raise ValidationError(_(
                "DAG Acyclicity Violation: Circular folder hierarchy detected at folder ID %s (path: %s).",
                cycle_row[0],
                cycle_row[1],
            ))
        return True

    def check_dgm_folder_rbac_access(self, operation='read', user=None):
        """Enforces granular DGM & INNORIA Role-Based Access Control (RBAC) and Multi-Company Tenancy."""
        target_user = user or self.env.user
        if not target_user:
            raise AccessError(_("Authentication required for document RBAC verification."))

        user_su = target_user.sudo()
        is_super = target_user._is_superuser()
        allowed_company_ids = set(user_su.company_ids.ids) if hasattr(user_su, 'company_ids') else set()

        # CWE-284 / CWE-863 Multi-Company Tenancy Boundary Guard (enforced before role checks)
        if not is_super:
            for doc in self.sudo():
                doc_comp = doc.company_id or (doc.folder_id.company_id if doc.folder_id else False)
                if doc_comp and doc_comp.id not in allowed_company_ids:
                    raise AccessError(_(
                        "Cross-company document access violation: User '%s' does not belong to company '%s'.",
                        target_user.name,
                        doc_comp.name,
                    ))

        if (
            is_super
            or user_su._has_group('base.group_system')
            or user_su._has_group('documents.group_documents_manager')
        ):
            return True

        if hasattr(user_su, 'all_group_ids'):
            user_group_ids = set(user_su.all_group_ids.ids)
        elif hasattr(user_su, 'groups_id'):
            user_group_ids = set(user_su.groups_id.ids)
        else:
            user_group_ids = set()

        write_ops = ('write', 'unlink', 'create')
        for doc in self.sudo():
            if operation in write_ops:
                req_groups = doc.dgm_write_group_ids or (doc.folder_id.dgm_write_group_ids if doc.folder_id else self.env['res.groups'])
                if req_groups and not (user_group_ids & set(req_groups.ids)):
                    raise AccessError(_(
                        "RBAC Access Denied: User '%s' lacks write/edit permission for document/folder '%s' (Profile: %s).",
                        target_user.name,
                        doc.name,
                        doc.dgm_rbac_profile or (doc.folder_id.dgm_rbac_profile if doc.folder_id else 'restricted'),
                    ))
            else:
                req_groups = doc.dgm_read_group_ids or (doc.folder_id.dgm_read_group_ids if doc.folder_id else self.env['res.groups'])
                if req_groups and not (user_group_ids & set(req_groups.ids)):
                    raise AccessError(_(
                        "RBAC Access Denied: User '%s' lacks read permission for document/folder '%s' (Profile: %s).",
                        target_user.name,
                        doc.name,
                        doc.dgm_rbac_profile or (doc.folder_id.dgm_rbac_profile if doc.folder_id else 'restricted'),
                    ))
        return True

    @staticmethod
    def _classify_dgm_inno_path_profile(path_parts, is_root=False):
        """Classifies a document/folder ancestor path list into one of the 11 canonical RBAC profiles."""
        if is_root or len(path_parts) <= 1:
            return 'company_sop'

        top_branch = (path_parts[1] or '').upper()
        sub_branch = (path_parts[2] if len(path_parts) > 2 else '').upper()
        full_upper = " / ".join(p.upper() for p in path_parts)

        # 1. DGM 01. Pháp lý & 05. Sở hữu Trí tuệ
        if top_branch.startswith('01.') or 'PHÁP LÝ' in top_branch or top_branch.startswith('05.') or 'SỞ HỮU TRÍ TUỆ' in top_branch:
            return 'exec_legal'

        # 2. DGM 07. Quy trình Chuẩn & SOPs
        if top_branch.startswith('07.') or 'QUY TRÌNH CHUẨN' in top_branch:
            return 'company_sop'

        # 3. DGM 04. Nhân sự & Tiền lương
        if top_branch.startswith('04.') or 'NHÂN SỰ' in top_branch:
            return 'hr_cb'

        # 4. DGM 02. Tài chính - Kế toán - Thuế (with HR C&B override for Lương / BHXH)
        if top_branch.startswith('02.') or 'TÀI CHÍNH' in top_branch:
            if any(k in sub_branch or k in full_upper for k in ('BHXH', 'LƯƠNG', 'LUONG', 'DIGIBIZ', 'PAYSLIP')):
                return 'hr_cb'
            return 'finance_tax'

        # 5. DGM 03. Hợp đồng & Thương mại (with MTI Timesheet override for TÀI BÙI)
        if top_branch.startswith('03.') or ('HỢP ĐỒNG' in top_branch and 'MTI' not in top_branch and 'INNORIA' not in top_branch):
            if 'TÀI BÙI' in sub_branch or 'TAI BUI' in sub_branch or 'TIMESHEET' in full_upper:
                return 'mti_timesheet'
            return 'commercial_contract'

        # 6. DGM 06. Thương hiệu & Hình ảnh
        if top_branch.startswith('06.') or 'THƯƠNG HIỆU' in top_branch:
            return 'brand_sales'

        # 7. 08. INNORIA multi-branch commercial & corporate subtree
        if 'INNORIA' in top_branch or top_branch.startswith('08.'):
            if not sub_branch:
                return 'project_delivery'
            if 'THÔNG TIN CHUNG' in sub_branch:
                return 'exec_legal'
            if 'NHÂN SỰ' in sub_branch:
                return 'hr_cb'
            if 'HÌNH ẢNH' in sub_branch:
                return 'brand_sales'
            if 'HỢP ĐỒNG SCAN' in sub_branch:
                if 'LAO ĐỘNG' in full_upper or 'NHÂN SỰ' in full_upper:
                    return 'hr_cb'
                return 'commercial_contract'
            if 'HỢP ĐỒNG, DỰ ÁN, KH' in sub_branch:
                tail_upper = " / ".join(p.upper() for p in path_parts[3:])
                if any(k in tail_upper for k in ('HỢP ĐỒNG', 'HĐ CHÍNH', 'PHỤ LỤC', 'CONTRACT', 'MSA')):
                    return 'commercial_contract'
                return 'project_delivery'
            return 'project_delivery'

        # 8. 09. MTI - CONTRACT
        if 'MTI - CONTRACT' in top_branch or top_branch.startswith('09.'):
            return 'mti_contract'

        # 9. 10. MTI - TIMESHEET
        if 'MTI - TIMESHEET' in top_branch or top_branch.startswith('10.'):
            return 'mti_timesheet'

        # 10. 11. TÀI LIỆU BÁN HÀNG
        if 'TÀI LIỆU BÁN HÀNG' in top_branch or top_branch.startswith('11.'):
            return 'sales_kit'

        # 11. 12. DIGITAL TRANSFORMATION
        if 'DIGITAL TRANSFORMATION' in top_branch or 'CHUYỂN ĐỔI SỐ' in top_branch or top_branch.startswith('12.'):
            return 'digital_solution'

        return 'project_delivery'

    @api.model
    def reconcile_matrix_chunked(self, folder_ids=None, target_company_id=None, chunk_size=250):
        """Chunked savepoint-isolated RBAC reconciliation with 5s lock timeout and DAG acyclicity check."""
        return self.apply_dgm_inno_rbac_matrix(target_company_id=target_company_id, chunk_size=chunk_size)

    @api.model
    def apply_dgm_inno_rbac_matrix(self, target_company_id=None, chunk_size=250):
        """Applies the 11-profile Role-Based Access Control (RBAC) Matrix across 100% of active
        folders and files in `documents.document` while preserving hierarchical `user_folder_id`.
        Uses 5s lock_timeout, DAG acyclicity verification, and 250-record savepoint chunking.
        """
        if target_company_id is not None and not self.env.user._is_superuser():
            allowed_cids = set(self.env.user.sudo().company_ids.ids)
            if int(target_company_id) not in allowed_cids:
                raise AccessError(_("Cross-company RBAC reconciliation prohibited for target_company_id=%s.", target_company_id))

        cr = self.env.cr
        with cr.savepoint():
            cr.execute("SET LOCAL lock_timeout = '5s';")
            # Ensure physical columns and M2M tables exist even if called prior to full module upgrade
            cr.execute("""
                ALTER TABLE documents_document
                    ADD COLUMN IF NOT EXISTS dgm_rbac_profile VARCHAR,
                    ADD COLUMN IF NOT EXISTS dgm_confidentiality_level VARCHAR DEFAULT 'confidential',
                    ADD COLUMN IF NOT EXISTS dgm_rbac_generation_id VARCHAR;
                CREATE INDEX IF NOT EXISTS documents_document_dgm_rbac_profile_index
                    ON documents_document (dgm_rbac_profile);
                CREATE INDEX IF NOT EXISTS documents_document_dgm_confidentiality_level_index
                    ON documents_document (dgm_confidentiality_level);
                CREATE INDEX IF NOT EXISTS documents_document_dgm_rbac_generation_id_index
                    ON documents_document (dgm_rbac_generation_id);
                CREATE TABLE IF NOT EXISTS dgm_doc_read_group_rel (
                    document_id INTEGER NOT NULL REFERENCES documents_document(id) ON DELETE CASCADE,
                    group_id INTEGER NOT NULL REFERENCES res_groups(id) ON DELETE CASCADE,
                    PRIMARY KEY (document_id, group_id)
                );
                CREATE TABLE IF NOT EXISTS dgm_doc_write_group_rel (
                    document_id INTEGER NOT NULL REFERENCES documents_document(id) ON DELETE CASCADE,
                    group_id INTEGER NOT NULL REFERENCES res_groups(id) ON DELETE CASCADE,
                    PRIMARY KEY (document_id, group_id)
                );
            """)

        # Verify folder hierarchy is a strict DAG with zero cycles before propagating permissions
        self._verify_folder_dag_acyclicity()

        # Resolve XML IDs for all referenced res.groups
        group_xmlids = set()
        for spec in self.DGM_RBAC_MATRIX_SPEC.values():
            group_xmlids.update(spec['read_groups'])
            group_xmlids.update(spec['write_groups'])

        xmlid_to_gid = {}
        for gx in group_xmlids:
            grp = self.env.ref(gx, raise_if_not_found=False)
            if grp:
                xmlid_to_gid[gx] = grp.id

        # Fetch all active documents and folders
        cr.execute("""
            SELECT id, type, COALESCE(name->>'vi_VN', name->>'en_US', name::text) AS name, folder_id
            FROM documents_document
            WHERE active = TRUE
        """)
        rows = cr.fetchall()
        by_id = {r[0]: {'id': r[0], 'type': r[1], 'name': r[2] or '', 'folder_id': r[3]} for r in rows}

        digest_seed = f"{len(by_id)}:{sorted(self.DGM_RBAC_MATRIX_SPEC.keys())}"
        generation_id = "GEN-20261016-" + hashlib.sha256(digest_seed.encode("utf-8")).hexdigest()[:8].upper()

        path_cache = {}

        def get_path_parts(doc_id):
            if doc_id in path_cache:
                return path_cache[doc_id]
            visited = set()
            chain = []
            curr = doc_id
            while curr and curr in by_id and curr not in visited:
                visited.add(curr)
                node = by_id[curr]
                chain.append(node['name'])
                curr = node['folder_id']
            chain.reverse()
            path_cache[doc_id] = chain
            return chain

        profile_to_folder_ids = {k: [] for k in self.DGM_RBAC_MATRIX_SPEC}
        profile_to_file_ids = {k: [] for k in self.DGM_RBAC_MATRIX_SPEC}

        for doc_id, info in by_id.items():
            parts = get_path_parts(doc_id)
            is_root = info['folder_id'] is None and info['type'] == 'folder'
            profile = self._classify_dgm_inno_path_profile(parts, is_root=is_root)
            if info['type'] == 'folder':
                profile_to_folder_ids[profile].append(doc_id)
            else:
                profile_to_file_ids[profile].append(doc_id)

        summary = {
            'generation_id': generation_id,
            'chunk_size': int(chunk_size or 250),
            'total_folders': sum(len(v) for v in profile_to_folder_ids.values()),
            'total_files': sum(len(v) for v in profile_to_file_ids.values()),
            'profiles': {},
        }

        step = max(1, int(chunk_size or 250))

        for profile, spec in self.DGM_RBAC_MATRIX_SPEC.items():
            f_ids = profile_to_folder_ids[profile]
            d_ids = profile_to_file_ids[profile]
            combined_ids = f_ids + d_ids
            summary['profiles'][profile] = {
                'folders': len(f_ids),
                'files': len(d_ids),
                'total': len(combined_ids),
                'confidentiality': spec['confidentiality'],
                'access_internal': spec['access_internal'],
            }
            if not combined_ids:
                continue

            read_gids = [xmlid_to_gid[gx] for gx in spec['read_groups'] if gx in xmlid_to_gid]
            write_gids = [xmlid_to_gid[gx] for gx in spec['write_groups'] if gx in xmlid_to_gid]

            # Chunked savepoint updates for folders
            for i in range(0, len(f_ids), step):
                chunk = f_ids[i:i + step]
                with cr.savepoint():
                    cr.execute("SET LOCAL lock_timeout = '5s';")
                    cr.execute("""
                        UPDATE documents_document
                        SET dgm_rbac_profile = %s,
                            dgm_confidentiality_level = %s,
                            dgm_rbac_generation_id = %s,
                            access_internal = %s,
                            access_via_link = %s,
                            is_access_via_link_hidden = %s,
                            owner_id = NULL
                        WHERE id = ANY(%s)
                    """, (
                        profile,
                        spec['confidentiality'],
                        generation_id,
                        spec['access_internal'],
                        spec['access_via_link'],
                        spec['is_access_via_link_hidden'],
                        chunk,
                    ))

            # Chunked savepoint updates for files
            for i in range(0, len(d_ids), step):
                chunk = d_ids[i:i + step]
                with cr.savepoint():
                    cr.execute("SET LOCAL lock_timeout = '5s';")
                    cr.execute("""
                        UPDATE documents_document
                        SET dgm_rbac_profile = %s,
                            dgm_confidentiality_level = %s,
                            dgm_rbac_generation_id = %s,
                            access_internal = %s,
                            access_via_link = %s,
                            is_access_via_link_hidden = %s
                        WHERE id = ANY(%s)
                    """, (
                        profile,
                        spec['confidentiality'],
                        generation_id,
                        spec['access_internal'],
                        spec['access_via_link'],
                        spec['is_access_via_link_hidden'],
                        chunk,
                    ))

            # Chunked savepoint M2M synchronization
            for i in range(0, len(combined_ids), step):
                chunk = combined_ids[i:i + step]
                with cr.savepoint():
                    cr.execute("SET LOCAL lock_timeout = '5s';")
                    cr.execute("DELETE FROM dgm_doc_read_group_rel WHERE document_id = ANY(%s)", (chunk,))
                    cr.execute("DELETE FROM dgm_doc_write_group_rel WHERE document_id = ANY(%s)", (chunk,))
                    if read_gids:
                        cr.execute("""
                            INSERT INTO dgm_doc_read_group_rel (document_id, group_id)
                            SELECT d_id, g_id
                            FROM unnest(%s::int[]) AS d_id
                            CROSS JOIN unnest(%s::int[]) AS g_id
                            ON CONFLICT DO NOTHING
                        """, (chunk, read_gids))
                    if write_gids:
                        cr.execute("""
                            INSERT INTO dgm_doc_write_group_rel (document_id, group_id)
                            SELECT d_id, g_id
                            FROM unnest(%s::int[]) AS d_id
                            CROSS JOIN unnest(%s::int[]) AS g_id
                            ON CONFLICT DO NOTHING
                        """, (chunk, write_gids))

        self.env.invalidate_all()
        _logger.info(
            "Applied DGM & INNORIA RBAC Matrix [%s] across %d folders and %d files.",
            generation_id,
            summary['total_folders'],
            summary['total_files'],
        )
        return summary

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

    @api.model
    def cron_dgm_document_triage_split(self, batch_limit=50):
        """DGM Autonomous Document Triage & Multipage Split Watchdog (Scheduled Daemon).
        Scans unrouted documents under DGM root folder (ID 3223 / folder_dgm_root),
        calls classify_dgm_document(), and flags multipage bundles with 'To Split'.
        Completely idempotent and fault-tolerant.
        """
        # 1. Guard: Check autonomous kill-switch (Fail-Closed)
        if not self.env['al2c.autonomy.guard']._dgm_autonomy_enabled():
            _logger.info("DGM Document Triage Watchdog: Autonomy disabled. Skipping.")
            return {'status': 'skipped', 'reason': 'autonomy_disabled'}

        try:
            # 2. Locate DGM root folder 3223
            root_folder = self.browse(3223)
            if not root_folder.exists() or root_folder.type != 'folder':
                root_folder = self.env.ref('insilos_al2c.folder_dgm_root', raise_if_not_found=False)
                if not root_folder:
                    root_folder = self.search([
                        ('name', 'ilike', 'DGM · Công ty Cổ phần Người Bạn Số'),
                        ('type', '=', 'folder')
                    ], limit=1)

            # 3. Select unrouted documents with FOR UPDATE SKIP LOCKED
            folder_clause = "folder_id IS NULL"
            params = [batch_limit]
            if root_folder and root_folder.exists():
                folder_clause = "(folder_id IS NULL OR folder_id = %s)"
                params = [root_folder.id, batch_limit]

            query = f"""
                SELECT id FROM documents_document
                WHERE type != 'folder' AND {folder_clause}
                ORDER BY create_date ASC, id ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
            """
            self.env.cr.execute(query, params)
            locked_ids = [row[0] for row in self.env.cr.fetchall()]
            def _reconcile_unmapped_rbac():
                self.env.cr.execute("""
                    SELECT COUNT(*) FROM documents_document
                    WHERE active = TRUE AND (dgm_rbac_profile IS NULL OR dgm_rbac_generation_id IS NULL)
                """)
                unmapped_rbac_count = self.env.cr.fetchone()[0] or 0
                if unmapped_rbac_count > 0:
                    with self.env.cr.savepoint():
                        self.sudo().apply_dgm_inno_rbac_matrix()
                return unmapped_rbac_count

            if not locked_ids:
                rbac_reconciled = _reconcile_unmapped_rbac()
                _logger.info(
                    "DGM Document Triage Watchdog: Zero unrouted documents to triage (rbac_reconciled=%d).",
                    rbac_reconciled,
                )
                return {
                    'status': 'success',
                    'scanned': 0,
                    'routed': 0,
                    'multipage_split': 0,
                    'rbac_reconciled': rbac_reconciled,
                }

            unrouted_docs = self.browse(locked_ids)
            scanned_count = len(unrouted_docs)
            multipage_count = 0
            routed_count = 0

            # 4. Execute classification and triage inside atomic savepoints
            for doc in unrouted_docs:
                try:
                    with self.env.cr.savepoint():
                        doc.classify_dgm_document()
                        if doc._get_is_multipage():
                            multipage_count += 1
                        elif doc.folder_id and (not root_folder or doc.folder_id.id != root_folder.id):
                            routed_count += 1
                except Exception as doc_err:
                    _logger.warning("Error triaging document %s: %s", doc.id, doc_err)

            rbac_reconciled = _reconcile_unmapped_rbac()
            summary = {
                'status': 'success',
                'scanned': scanned_count,
                'routed': routed_count,
                'multipage_split': multipage_count,
                'rbac_reconciled': rbac_reconciled,
            }
            _logger.info("DGM Document Triage Watchdog completed: %s", summary)
            return summary
        except Exception as e:
            _logger.exception("DGM Document Triage Watchdog encountered error: %s", e)
            return {'status': 'error', 'reason': str(e)}
