# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import logging
from insilos import models, api

_logger = logging.getLogger(__name__)

# ==============================================================================
# SAP Enterprise Lexicon Canonical Mapping
# ==============================================================================
SAP_MODEL_DESCRIPTIONS = {
    'res.partner': 'Business Partner (BP)',
    'product.template': 'Material Master (MM)',
    'product.product': 'Material Variant',
    'sale.order': 'Sales Order (SD)',
    'sale.order.line': 'Sales Order Line Item',
    'purchase.order': 'MM Purchase Order',
    'purchase.order.line': 'Purchase Order Line Item',
    'purchase.requisition': 'Purchase Requisition (Banf) / Outline Agreement',
    'stock.picking': 'Goods Movement / Delivery',
    'stock.move': 'Material Movement Item',
    'stock.quant': 'Physical Inventory Adjustment (MI01/MI07)',
    'account.move': 'FI Accounting Document (BKPF)',
    'account.move.line': 'FI Document Line Item (BSEG)',
    'account.account': 'Chart of Accounts / G/L Accounts',
    'account.analytic.account': 'Cost Center / Profit Center',
    'account.analytic.plan': 'Controlling Area Plan (KOKRS)',
    'mrp.production': 'Production Order (PP/CO01)',
    'mrp.bom': 'Production BOM (CS01)',
    'mrp.workcenter': 'Work Center / Routing Resource (CR01)',
    'stock.warehouse': 'Plant / Distribution Center',
    'stock.location': 'Storage Location (SLoc / LGORT)',
    'res.company': 'Company Code (Bukrs)',
    # Human Resources & SuccessFactors (HCM / HRM)
    'hr.employee': 'Personnel Master / Employee',
    'hr.department': 'Organizational Unit (OrgUnit)',
    'hr.job': 'Position / Job Role',
    'hr.version': 'Personnel Contract / Work Agreement',
    'hr.contract.type': 'Work Agreement Category',
    'hr.payslip': 'Remuneration Statement / Payroll Result',
    'hr.payslip.run': 'Payroll Run / Area Processing',
    'hr.salary.rule': 'Wage Type (Lohnart / LGART)',
    'hr.salary.rule.category': 'Wage Type Category / Group',
    'hr.salary.attachment': 'Garnishment / Recurring Deduction',
    'hr.applicant': 'Candidate / Job Applicant (E-Recruiting)',
    'hr.recruitment.stage': 'Candidate Selection Stage',
    # Plant Maintenance (SAP PM)
    'maintenance.equipment': 'Technical Equipment / Functional Location',
    'maintenance.request': 'PM Maintenance Order / Notification',
    'maintenance.team': 'Maintenance Planner Group / Work Center',
    'maintenance.stage': 'Maintenance Notification / Order Status',
    'maintenance.equipment.category': 'Equipment Class / Technical Category',
    # Project Systems (SAP PS)
    'project.project': 'PS Project Definition / WBS Header',
    'project.task': 'WBS Element / Network Activity',
    'project.milestone': 'Project Milestone (WBS Milestone)',
    'project.task.type': 'WBS Activity Execution Stage / Status',
    # Quality Management (SAP QM)
    'quality.point': 'Inspection Plan / Characteristic',
    'quality.check': 'Quality Inspection Lot / Result Recording',
    'quality.alert': 'Quality Notification / Defect Report',
    'quality.alert.stage': 'Quality Notification Processing Stage',
    'quality.alert.team': 'Quality Planner Group / Inspection Team',
}

SAP_FIELD_STRINGS = {
    'res.partner': {
        'name': 'Business Partner Name',
        'ref': 'BP Number / Search Term',
        'customer_rank': 'Customer Role Indicator',
        'supplier_rank': 'Vendor Role Indicator',
        'vat': 'Tax Number (Tax ID / VAT)',
        'company_type': 'BP Category',
        'parent_id': 'Parent Business Partner',
        'street': 'Street / House Number',
        'city': 'City / Postal District',
        'zip': 'Postal Code',
        'country_id': 'Country Key',
        'phone': 'Telephone',
        'email': 'E-Mail Address',
    },
    'product.template': {
        'name': 'Material Description',
        'default_code': 'Material Number (MATNR)',
        'type': 'Material Type (MTART)',
        'categ_id': 'Material Group (MATKL)',
        'list_price': 'Standard Selling Price',
        'standard_price': 'Moving Avg / Standard Cost',
        'uom_id': 'Base Unit of Measure (BUn)',
        'uom_po_id': 'Order Unit of Measure',
    },
    'product.product': {
        'name': 'Material Description',
        'default_code': 'Material Number (MATNR)',
        'standard_price': 'Moving Avg / Standard Cost',
    },
    'res.company': {
        'name': 'Company Code Name',
        'currency_id': 'Company Code Currency',
    },
    'stock.warehouse': {
        'name': 'Plant Name / Distribution Center',
        'code': 'Plant Code (Werks)',
        'company_id': 'Company Code Assignment',
    },
    'stock.location': {
        'name': 'Storage Location Name',
    },
    'sale.order': {
        'name': 'SD Document Number',
        'partner_id': 'Sold-to Party (BP)',
        'partner_invoice_id': 'Bill-to Party / Payer (BP)',
        'partner_shipping_id': 'Ship-to Party (BP)',
        'date_order': 'Document Date',
        'validity_date': 'Quotation Valid Until',
        'order_line': 'Sales Order Items',
        'amount_total': 'Net Value + Tax',
        'payment_term_id': 'Terms of Payment',
    },
    'sale.order.line': {
        'product_id': 'Material Master (MM)',
        'product_uom_qty': 'Order Quantity',
        'price_unit': 'Condition Unit Price',
        'price_subtotal': 'Item Net Value',
    },
    'purchase.requisition': {
        'name': 'Requisition / Agreement No. (BANFN)',
        'vendor_id': 'Vendor / Supplier BP',
        'requisition_type': 'Agreement Category',
        'line_ids': 'Requisition Line Items',
    },
    'purchase.order': {
        'name': 'MM Document Number',
        'partner_id': 'Vendor / Supplier BP',
        'date_order': 'PO Order Date',
        'date_planned': 'Scheduled Delivery Date',
        'order_line': 'Purchase Order Items',
        'amount_total': 'Gross Order Value',
        'payment_term_id': 'Terms of Payment',
    },
    'purchase.order.line': {
        'product_id': 'Material Master (MM)',
        'product_qty': 'Order Quantity',
        'price_unit': 'Net Order Price',
    },
    'stock.picking': {
        'name': 'Delivery / Goods Movement No.',
        'partner_id': 'Delivery BP Party',
        'picking_type_id': 'Movement Type / Process',
        'location_id': 'Source Storage Location (SLoc)',
        'location_dest_id': 'Destination Storage Location (SLoc)',
        'scheduled_date': 'Planned Movement Date',
        'origin': 'Reference Document (PO/SO)',
    },
    'stock.move': {
        'product_id': 'Material Master (MM)',
        'product_uom_qty': 'Scheduled Quantity',
        'quantity': 'Delivered Quantity',
        'location_id': 'Source Storage Location (SLoc)',
        'location_dest_id': 'Destination Storage Location (SLoc)',
    },
    'stock.quant': {
        'product_id': 'Material Master (MM)',
        'location_id': 'Storage Location (SLoc)',
        'quantity': 'Quantity On Hand',
        'inventory_quantity': 'Physical Counted Quantity',
        'inventory_diff_quantity': 'Count Difference',
    },
    'account.move': {
        'name': 'FI Document Number',
        'ref': 'Reference Document (XBLNR)',
        'date': 'Posting Date in General Ledger (BUDAT)',
        'invoice_date': 'Document Date (BLDAT)',
        'partner_id': 'Business Partner Account',
        'invoice_line_ids': 'Billing Document Items',
        'line_ids': 'General Ledger Line Items',
        'invoice_payment_term_id': 'Terms of Payment',
    },
    'account.move.line': {
        'account_id': 'G/L Account Number (HKONT)',
        'debit': 'Debit Amount (Soll)',
        'credit': 'Credit Amount (Haben)',
        'analytic_distribution': 'CO Account Assignment',
        'partner_id': 'Business Partner Account',
    },
    'account.account': {
        'code': 'G/L Account Number (SAKNR)',
        'name': 'G/L Account Description',
        'account_type': 'Financial Statement Category',
    },
    'account.analytic.account': {
        'name': 'Cost Center / Profit Center Name',
        'code': 'Cost Center / Profit Center Key',
        'plan_id': 'Controlling Area Plan (KOKRS)',
        'co_type': 'CO Category',
    },
    'account.analytic.plan': {
        'name': 'Controlling Area Plan (KOKRS)',
    },
    'mrp.production': {
        'name': 'Production Order Number (AUFNR)',
        'product_id': 'Header Material Master',
        'product_qty': 'Target Order Quantity',
        'move_raw_ids': 'Component Reservations (RESB)',
        'bom_id': 'Production BOM Reference',
        'date_deadline': 'Basic Finish Date',
        'workorder_ids': 'Production Operations / Routings',
        'qty_producing': 'Confirmed Quantity',
        'movement_type_issue': 'Movement Type - Issue (BWART 261)',
        'movement_type_receipt': 'Movement Type - Receipt (BWART 101)',
    },
    'mrp.bom': {
        'product_tmpl_id': 'Header Material Master',
        'code': 'Alternative BOM / Reference',
        'product_qty': 'Base Quantity',
        'bom_line_ids': 'Components / BOM Line Items',
        'operation_ids': 'Production Routing Operations',
    },
    'mrp.workcenter': {
        'name': 'Work Center Description',
        'code': 'Work Center Code (ARBPL)',
        'costs_hour': 'Cost Center Activity Rate / Rate per Unit',
        'time_start': 'Standard Setup Time (RUEZT)',
        'time_stop': 'Standard Teardown / Cleanup Time',
        'oee_target': 'OEE Target Ratio (%)',
        'oee': 'Overall Equipment Effectiveness (OEE)',
    },
    # Human Resources & SuccessFactors (HCM / HRM)
    'hr.employee': {
        'name': 'Personnel Name / Employee',
        'department_id': 'Organizational Unit (OrgUnit)',
        'job_id': 'Position / Job Role',
        'parent_id': 'Direct Supervisor / Line Manager',
        'coach_id': 'Mentor / Functional Coach',
        'work_email': 'Corporate E-Mail Address',
        'work_phone': 'Office Telephone',
        'mobile_phone': 'Cellular Mobile',
        'identification_id': 'National ID / Citizen Identity (CCCD)',
        'passport_id': 'Passport Number',
        'birthday': 'Date of Birth',
        'marital': 'Marital Status',
        'contract_type_id': 'Employment Category / Work Agreement Type',
        'date_version': 'Personnel Master Effective Date',
        'wage': 'Basic Remuneration Rate',
    },
    'hr.department': {
        'name': 'Organizational Unit Name',
        'parent_id': 'Parent Organizational Unit',
        'manager_id': 'Head of Organizational Unit',
    },
    'hr.job': {
        'name': 'Position / Job Role Title',
        'department_id': 'Assigned Organizational Unit',
        'no_of_recruitment': 'Open Requisitions / Vacancies',
        'expected_employees': 'Planned Headcount (Target)',
        'no_of_employee': 'Active Headcount',
    },
    'hr.version': {
        'name': 'Work Agreement / Contract Title',
        'employee_id': 'Personnel Master (Employee)',
        'department_id': 'Organizational Unit',
        'job_id': 'Position / Job Role',
        'wage': 'Basic Remuneration Rate',
        'contract_date_start': 'Work Agreement Start Date',
        'contract_date_end': 'Work Agreement Expiration Date',
        'date_version': 'Contract Version Effective Date',
        'structure_type_id': 'Payroll Salary Structure Category',
        'resource_calendar_id': 'Work Schedule Rule',
    },
    'hr.contract.type': {
        'name': 'Work Agreement Category Name',
    },
    'hr.payslip': {
        'name': 'Remuneration Statement Description',
        'employee_id': 'Personnel Master (Employee)',
        'date_from': 'Remuneration Period Start Date',
        'date_to': 'Remuneration Period End Date',
        'basic_wage': 'Basic Remuneration Rate',
        'gross_wage': 'Gross Remuneration Amount',
        'net_wage': 'Net Paid Remuneration',
        'state': 'Payroll Processing Status',
        'line_ids': 'Remuneration Wage Type Items',
        'version_id': 'Associated Personnel Contract',
    },
    'hr.payslip.run': {
        'name': 'Payroll Run Description',
        'date_start': 'Payroll Period Start Date',
        'date_end': 'Payroll Period End Date',
        'state': 'Payroll Run Status',
        'slip_ids': 'Processed Remuneration Statements',
    },
    'hr.salary.rule': {
        'name': 'Wage Type Description (Lohnart)',
        'code': 'Wage Type Code (LGART)',
        'category_id': 'Wage Type Category',
        'sequence': 'Calculation Sequence',
    },
    'hr.salary.rule.category': {
        'name': 'Wage Type Category Name',
        'code': 'Category Code',
        'parent_id': 'Parent Wage Type Category',
    },
    'hr.salary.attachment': {
        'description': 'Garnishment / Recurring Deduction Note',
        'employee_ids': 'Affected Personnel',
        'monthly_amount': 'Monthly Recurring Deduction Amount',
        'date_start': 'Deduction Effective Start Date',
        'date_end': 'Deduction Effective End Date',
    },
    'hr.applicant': {
        'partner_name': 'Candidate / Applicant Name',
        'email_from': 'Candidate E-Mail',
        'partner_phone': 'Candidate Telephone',
        'job_id': 'Target Position / Job Role',
        'department_id': 'Target Organizational Unit',
        'stage_id': 'Candidate Selection Stage',
        'user_id': 'Lead Recruiter / Talent Acquisition',
        'salary_expected': 'Expected Remuneration',
        'salary_proposed': 'Proposed Remuneration',
    },
    'hr.recruitment.stage': {
        'name': 'Selection Stage Name',
        'sequence': 'Stage Sequence',
    },
    # Plant Maintenance (SAP PM)
    'maintenance.equipment': {
        'name': 'Technical Equipment Description',
        'serial_no': 'Manufacturer Serial Number (SERNR)',
        'category_id': 'Equipment Class / Category',
        'maintenance_team_id': 'Maintenance Planner Group / Work Center',
        'technician_user_id': 'Assigned Maintenance Technician',
        'owner_user_id': 'Equipment Custodian / Operating Owner',
        'effective_date': 'Commissioning / In-Service Date',
        'assign_date': 'Installation / Assignment Date',
        'cost': 'Equipment Acquisition Cost',
        'location_id': 'Functional Location / Plant Area',
    },
    'maintenance.request': {
        'name': 'Maintenance Order Description / Subject',
        'equipment_id': 'Technical Equipment (IE01)',
        'category_id': 'Equipment Class',
        'maintenance_team_id': 'Maintenance Planner Group / Work Center',
        'owner_user_id': 'Notification Reporter (Created By)',
        'user_ids': 'Assigned Maintenance Technicians',
        'stage_id': 'Order / Notification Status',
        'priority': 'Order Priority Level',
        'schedule_date': 'Basic Start Date / Scheduled Maintenance',
        'close_date': 'Technical Completion Date (TECO)',
        'duration': 'Actual Work Duration (Hours)',
        'maintenance_type': 'Maintenance Order Type (Corrective / Preventive)',
    },
    'maintenance.team': {
        'name': 'Maintenance Planner Group / Work Center Name',
        'member_ids': 'Assigned Maintenance Technicians',
    },
    'maintenance.stage': {
        'name': 'Maintenance Order Status Name',
        'sequence': 'Sequence',
        'fold': 'Folded in Kanban',
    },
    'maintenance.equipment.category': {
        'name': 'Equipment Class Description',
        'technician_user_id': 'Lead Maintenance Technician',
    },
    # Project Systems (SAP PS)
    'project.project': {
        'name': 'PS Project Definition Name',
        'user_id': 'Project Manager / Responsible Person',
        'partner_id': 'Project Customer / Sold-to Party (BP)',
        'stage_id': 'Project Lifecycle Status',
        'date_start': 'Basic Start Date',
        'date': 'Basic Finish Date / Target Date',
        'allocated_hours': 'Budgeted Work (Planned Hours)',
        'effective_hours': 'Actual Recorded Work (Hours)',
        'tag_ids': 'Project Indicators / Tags',
        'privacy_visibility': 'Project Security / Access Classification',
    },
    'project.task': {
        'name': 'WBS Element / Activity Description',
        'project_id': 'PS Project Definition',
        'parent_id': 'Superior WBS Element',
        'child_ids': 'Sub-WBS Elements / Sub-Activities',
        'milestone_id': 'Assigned Project Milestone',
        'user_ids': 'Assigned Network Activity Resources',
        'stage_id': 'WBS Activity Execution Stage',
        'planned_date_begin': 'Scheduled Start Date',
        'date_deadline': 'Scheduled Finish Date / Deadline',
        'allocated_hours': 'Planned Work Duration (Hours)',
        'effective_hours': 'Actual Recorded Work (Hours)',
        'progress': 'Physical Progress Percentage (%)',
        'priority': 'Activity Priority',
    },
    'project.milestone': {
        'name': 'Milestone Description',
        'project_id': 'PS Project Definition',
        'deadline': 'Scheduled Milestone Date',
        'reached_date': 'Actual Milestone Achievement Date',
        'is_reached': 'Milestone Reached Indicator',
    },
    'project.task.type': {
        'name': 'WBS Activity Execution Stage Name',
        'sequence': 'Sequence',
    },
    # Quality Management (SAP QM)
    'quality.point': {
        'name': 'Inspection Plan Reference',
        'title': 'Inspection Characteristic Title',
        'product_ids': 'Header Material Masters (MM)',
        'picking_type_ids': 'Inspection Movement Types / Operations',
        'operation_id': 'Routing Operation Step',
        'test_type_id': 'Inspection Method / Test Type',
        'measure_frequency_type': 'Inspection Sampling Frequency',
        'team_id': 'Quality Planner Group / Inspection Team',
        'user_id': 'Quality Inspector / Responsible',
        'norm': 'Nominal Target Value / Target Norm',
        'tolerance_min': 'Lower Specification Limit (LSL)',
        'tolerance_max': 'Upper Specification Limit (USL)',
    },
    'quality.check': {
        'name': 'Inspection Lot Reference (Prüflos)',
        'title': 'Characteristic Inspection Description',
        'point_id': 'Inspection Plan / Characteristic Reference',
        'product_id': 'Inspected Material Master (MM)',
        'lot_ids': 'Batch / Material Lot Number',
        'picking_id': 'Associated Goods Movement / Delivery',
        'quality_state': 'Inspection Usage Decision (Pass/Fail)',
        'measure': 'Recorded Inspection Result Value',
        'tolerance_min': 'Lower Specification Limit (LSL)',
        'tolerance_max': 'Upper Specification Limit (USL)',
        'team_id': 'Quality Inspection Team',
        'user_id': 'Quality Inspector',
    },
    'quality.alert': {
        'name': 'Quality Notification Number (QM-QEL)',
        'title': 'Defect Summary / Subject',
        'check_id': 'Originating Inspection Lot (QA01)',
        'product_tmpl_id': 'Affected Material Master (MM)',
        'lot_ids': 'Defective Material Lot / Batch',
        'reason_id': 'Defect Code / Root Cause',
        'team_id': 'Quality Notification Handling Team',
        'user_id': 'Quality Action Coordinator',
        'priority': 'Defect Severity / Priority',
        'stage_id': 'Notification Processing Status',
        'action_corrective': 'Immediate Corrective Action (CAPA)',
        'action_preventive': 'Preventive Action / Mitigation',
    },
    'quality.alert.stage': {
        'name': 'Notification Stage Name',
        'sequence': 'Stage Sequence',
        'done': 'Notification Resolved / Closed',
    },
    'quality.alert.team': {
        'name': 'Quality Planner Group / Inspection Team Name',
    },
}



class Base(models.AbstractModel):
    _inherit = 'base'

    def _register_hook(self):
        super()._register_hook()
        desc = SAP_MODEL_DESCRIPTIONS.get(self._name)
        if desc:
            type(self)._description = desc

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Harmonize field labels to SAP Enterprise Lexicon."""
        res = super().fields_get(allfields=allfields, attributes=attributes)
        model_overrides = SAP_FIELD_STRINGS.get(self._name)
        if model_overrides and res:
            for field_name, new_string in model_overrides.items():
                if field_name in res and isinstance(res[field_name], dict):
                    res[field_name]['string'] = new_string
        return res

    @api.model
    def get_views(self, views, options=None):
        """Harmonize model description and field strings in view metadata to SAP conventions."""
        res = super().get_views(views, options=options)
        sap_desc = SAP_MODEL_DESCRIPTIONS.get(self._name)
        if sap_desc and isinstance(res, dict) and 'models' in res:
            if self._name in res['models'] and isinstance(res['models'][self._name], dict):
                res['models'][self._name]['description'] = sap_desc
                model_overrides = SAP_FIELD_STRINGS.get(self._name)
                if model_overrides and 'fields' in res['models'][self._name]:
                    fields_dict = res['models'][self._name]['fields']
                    for field_name, new_string in model_overrides.items():
                        if field_name in fields_dict and isinstance(fields_dict[field_name], dict):
                            fields_dict[field_name]['string'] = new_string
        return res


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def update_sap_menus(self):
        """Safely updates top-level menus to SAP Enterprise Lexicon."""
        SAP_MENUS = {
            'contacts.menu_contacts': 'Business Partner (BP)',
            'sale.sale_menu_root': 'Sales & Distribution (SD)',
            'purchase.menu_purchase_root': 'Materials Management (MM)',
            'stock.menu_stock_root': 'Logistics & Inventory (MM-IM)',
            'account.menu_finance': 'Financials & Controlling (FI/CO)',
            'mrp.menu_mrp_root': 'Production Planning (PP)',
            'hr.menu_hr_root': 'Human Resources & SuccessFactors (HCM)',
            'hr_recruitment.menu_hr_recruitment_root': 'E-Recruiting & Talent Acquisition',
            'maintenance.menu_maintenance_title': 'Plant Maintenance (SAP PM)',
            'project.menu_main_pm': 'Project Systems (SAP PS)',
            'quality_control.menu_quality_root': 'Quality Management (SAP QM)',
            'spreadsheet_dashboard.spreadsheet_dashboard_menu_root': 'Executive Analytics',
            'mail.menu_root_discuss': 'Enterprise Collaboration',
        }
        for xml_id, sap_name in SAP_MENUS.items():
            try:
                menu = self.env.ref(xml_id, raise_if_not_found=False)
                if menu:
                    menu.name = sap_name
            except Exception as e:
                _logger.warning("Could not rename menu %s: %s", xml_id, e)
        return True

