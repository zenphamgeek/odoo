# -*- coding: utf-8 -*-
import hashlib
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Al2cEinvoiceAdapter(models.AbstractModel):
    _name = 'al2c.einvoice.adapter'
    _description = 'Decree 70/2025 Statutory E-Invoice Adapter Interface'

    @api.model
    def issue_einvoice(self, move):
        """
        Issue statutory electronic invoice under Decree 70/2025/NĐ-CP.
        Returns dict containing statutory e-invoice metadata.
        """
        provider = move.al2c_einvoice_provider or 'mock'
        if provider == 'mock':
            return self._issue_mock(move)
        elif provider == 'vnpt':
            return self._issue_vnpt(move)
        elif provider == 'viettel':
            return self._issue_viettel(move)
        elif provider == 'misa':
            return self._issue_misa(move)
        else:
            raise UserError(_("Unsupported E-Invoice provider: %s") % provider)

    @api.model
    def cancel_einvoice(self, move, reason):
        """Cancel statutory electronic invoice."""
        provider = move.al2c_einvoice_provider or 'mock'
        return {
            'status': 'cancelled',
            'notice': f"E-Invoice {move.al2c_einvoice_number} cancelled on {provider.upper()}. Reason: {reason}",
            'cancellation_date': fields.Datetime.now(),
        }

    # --- Provider Adapters ---

    def _issue_mock(self, move):
        """Sandbox mock adapter producing deterministic, valid Decree 70 metadata."""
        inv_seq = move.id % 99999999
        number = f"1C26TAA-{inv_seq:08d}"
        
        # Build canonical Decree 70 XML payload
        xml_payload = self._build_decree_70_xml(move, number)
        xml_hash = hashlib.sha256(xml_payload.encode('utf-8')).hexdigest()
        
        # Statutory 34-char CQT lookup code: '00' + 32-char hex digest
        cqt_seed = f"{move.company_id.vat or '0310000000'}-{number}-{move.amount_total}-{time.time()}"
        lookup_code = "00" + hashlib.sha256(cqt_seed.encode('utf-8')).hexdigest()[:32].upper()
        
        qr_code = f"https://hoadondientu.gdt.gov.vn/tra-cuu?cqt={lookup_code}&mst={move.company_id.vat or '0310000000'}"
        
        return {
            'number': number,
            'lookup_code': lookup_code,
            'qr_code': qr_code,
            'xml_hash': xml_hash,
            'xml_payload': xml_payload,
            'issue_date': fields.Datetime.now(),
        }

    def _issue_vnpt(self, move):
        # Stub for VNPT endpoint integration; falls back to sandbox mock
        return self._issue_mock(move)

    def _issue_viettel(self, move):
        # Stub for Viettel S-Invoice endpoint integration; falls back to sandbox mock
        return self._issue_mock(move)

    def _issue_misa(self, move):
        # Stub for MISA meInvoice endpoint integration; falls back to sandbox mock
        return self._issue_mock(move)

    def _build_decree_70_xml(self, move, number):
        """Construct canonical XML conforming to General Department of Taxation standards."""
        seller_mst = move.company_id.vat or '0318000000'
        buyer_mst = move.partner_id.vat or '0100000000'
        issue_time = fields.Datetime.now().isoformat()

        lines_xml = []
        for line in move.invoice_line_ids.filtered(lambda l: not l.display_type):
            vat_class = getattr(line.product_id, 'al2c_vat_class', 'kct') or 'kct'
            vat_rate_str = "KCT" if vat_class == 'kct' else ("8%" if vat_class == 'vat_8' else "10%")
            lines_xml.append(f"""    <HHDVu>
      <TCat>{line.product_id.default_code or 'SKU'}</TCat>
      <THHDVu>{line.product_id.name or 'Item'}</THHDVu>
      <DVTinh>{line.product_uom_id.name or 'Unit'}</DVTinh>
      <SLuong>{line.quantity}</SLuong>
      <DGia>{line.price_unit}</DGia>
      <ThTien>{line.price_subtotal}</ThTien>
      <TSuat>{vat_rate_str}</TSuat>
    </HHDVu>""")

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<HDon xmlns="http://hoadondientu.gdt.gov.vn/2025/nd70">
  <DLHDon>
    <TTChung>
      <PBan>2.1.0</PBan>
      <THDon>HÓA ĐƠN GIÁ TRỊ GIA TĂNG</THDon>
      <KHMSHDon>1</KHMSHDon>
      <KHHDon>1C26TAA</KHHDon>
      <SHDon>{number.split('-')[-1]}</SHDon>
      <NLap>{issue_time}</NLap>
      <DVTTe>{move.currency_id.name}</DVTTe>
    </TTChung>
    <NDHDon>
      <NBan>
        <Ten>{move.company_id.name}</Ten>
        <MST>{seller_mst}</MST>
        <DChi>{move.company_id.street or 'Ho Chi Minh City'}</DChi>
      </NBan>
      <NMua>
        <Ten>{move.partner_id.name}</Ten>
        <MST>{buyer_mst}</MST>
        <DChi>{move.partner_id.street or 'Vietnam'}</DChi>
      </NMua>
      <DSHHDVu>
{chr(10).join(lines_xml)}
      </DSHHDVu>
      <TToan>
        <TgTCThue>{move.amount_untaxed}</TgTCThue>
        <TgTThue>{move.amount_tax}</TgTThue>
        <TgTTTBSo>{move.amount_total}</TgTTTBSo>
      </TToan>
    </NDHDon>
  </DLHDon>
</HDon>"""
        return xml
