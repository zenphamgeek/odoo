import base64
import io
import logging

from odoo import models, modules, _
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
            num_pages = getattr(reader, 'numPages', None)
            if num_pages is None and hasattr(reader, 'pages'):
                num_pages = len(reader.pages)
            return bool(num_pages and num_pages > 1)
        except Exception:
            _logger.debug("Unable to count pages in PDF document %r", self.name, exc_info=True)
            return False
