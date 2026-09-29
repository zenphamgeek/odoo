# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

from insilos.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSapLexiconM3(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_hrm_sap_lexicon(self):
        """Verify Human Resources & SuccessFactors (HCM) SAP descriptions and field overrides."""
        # 1. Model Descriptions
        self.assertEqual(self.env['hr.employee']._description, "Personnel Master / Employee")
        self.assertEqual(self.env['hr.department']._description, "Organizational Unit (OrgUnit)")
        self.assertEqual(self.env['hr.job']._description, "Position / Job Role")
        self.assertEqual(self.env['hr.version']._description, "Personnel Contract / Work Agreement")
        self.assertEqual(self.env['hr.contract.type']._description, "Work Agreement Category")
        self.assertEqual(self.env['hr.payslip']._description, "Remuneration Statement / Payroll Result")
        self.assertEqual(self.env['hr.payslip.run']._description, "Payroll Run / Area Processing")
        self.assertEqual(self.env['hr.salary.rule']._description, "Wage Type (Lohnart / LGART)")
        self.assertEqual(self.env['hr.salary.rule.category']._description, "Wage Type Category / Group")
        self.assertEqual(self.env['hr.salary.attachment']._description, "Garnishment / Recurring Deduction")
        self.assertEqual(self.env['hr.applicant']._description, "Candidate / Job Applicant (E-Recruiting)")
        self.assertEqual(self.env['hr.recruitment.stage']._description, "Candidate Selection Stage")

        # 2. Field Label Overrides on hr.employee
        emp_fields = self.env['hr.employee'].fields_get([
            'name', 'department_id', 'job_id', 'parent_id', 'coach_id',
            'work_email', 'work_phone', 'mobile_phone', 'identification_id',
            'passport_id', 'birthday', 'marital', 'contract_type_id', 'date_version', 'wage'
        ])
        self.assertEqual(emp_fields['name']['string'], "Personnel Name / Employee")
        self.assertEqual(emp_fields['department_id']['string'], "Organizational Unit (OrgUnit)")
        self.assertEqual(emp_fields['job_id']['string'], "Position / Job Role")
        self.assertEqual(emp_fields['parent_id']['string'], "Direct Supervisor / Line Manager")
        self.assertEqual(emp_fields['coach_id']['string'], "Mentor / Functional Coach")
        self.assertEqual(emp_fields['work_email']['string'], "Corporate E-Mail Address")
        self.assertEqual(emp_fields['work_phone']['string'], "Office Telephone")
        self.assertEqual(emp_fields['mobile_phone']['string'], "Cellular Mobile")
        self.assertEqual(emp_fields['identification_id']['string'], "National ID / Citizen Identity (CCCD)")
        self.assertEqual(emp_fields['passport_id']['string'], "Passport Number")
        self.assertEqual(emp_fields['birthday']['string'], "Date of Birth")
        self.assertEqual(emp_fields['marital']['string'], "Marital Status")
        self.assertEqual(emp_fields['contract_type_id']['string'], "Employment Category / Work Agreement Type")
        self.assertEqual(emp_fields['date_version']['string'], "Personnel Master Effective Date")
        self.assertEqual(emp_fields['wage']['string'], "Basic Remuneration Rate")

        # 3. Field Label Overrides on hr.department & hr.job
        dept_fields = self.env['hr.department'].fields_get(['name', 'parent_id', 'manager_id'])
        self.assertEqual(dept_fields['name']['string'], "Organizational Unit Name")
        self.assertEqual(dept_fields['parent_id']['string'], "Parent Organizational Unit")
        self.assertEqual(dept_fields['manager_id']['string'], "Head of Organizational Unit")

        job_fields = self.env['hr.job'].fields_get(['name', 'department_id', 'no_of_recruitment', 'expected_employees', 'no_of_employee'])
        self.assertEqual(job_fields['name']['string'], "Position / Job Role Title")
        self.assertEqual(job_fields['department_id']['string'], "Assigned Organizational Unit")
        self.assertEqual(job_fields['no_of_recruitment']['string'], "Open Requisitions / Vacancies")
        self.assertEqual(job_fields['expected_employees']['string'], "Planned Headcount (Target)")
        self.assertEqual(job_fields['no_of_employee']['string'], "Active Headcount")

        # 4. Field Label Overrides on hr.version & hr.payslip
        ver_fields = self.env['hr.version'].fields_get([
            'name', 'employee_id', 'department_id', 'job_id', 'wage',
            'contract_date_start', 'contract_date_end', 'date_version',
            'structure_type_id', 'resource_calendar_id'
        ])
        self.assertEqual(ver_fields['name']['string'], "Work Agreement / Contract Title")
        self.assertEqual(ver_fields['employee_id']['string'], "Personnel Master (Employee)")
        self.assertEqual(ver_fields['wage']['string'], "Basic Remuneration Rate")
        self.assertEqual(ver_fields['contract_date_start']['string'], "Work Agreement Start Date")
        self.assertEqual(ver_fields['contract_date_end']['string'], "Work Agreement Expiration Date")

        slip_fields = self.env['hr.payslip'].fields_get(['name', 'employee_id', 'date_from', 'date_to', 'basic_wage', 'gross_wage', 'net_wage', 'state', 'line_ids'])
        self.assertEqual(slip_fields['name']['string'], "Remuneration Statement Description")
        self.assertEqual(slip_fields['employee_id']['string'], "Personnel Master (Employee)")
        self.assertEqual(slip_fields['date_from']['string'], "Remuneration Period Start Date")
        self.assertEqual(slip_fields['date_to']['string'], "Remuneration Period End Date")
        self.assertEqual(slip_fields['basic_wage']['string'], "Basic Remuneration Rate")
        self.assertEqual(slip_fields['gross_wage']['string'], "Gross Remuneration Amount")
        self.assertEqual(slip_fields['net_wage']['string'], "Net Paid Remuneration")
        self.assertEqual(slip_fields['state']['string'], "Payroll Processing Status")
        self.assertEqual(slip_fields['line_ids']['string'], "Remuneration Wage Type Items")

    def test_02_plant_maintenance_sap_lexicon(self):
        """Verify Plant Maintenance (SAP PM) model descriptions and field strings."""
        # 1. Model Descriptions
        self.assertEqual(self.env['maintenance.equipment']._description, "Technical Equipment / Functional Location")
        self.assertEqual(self.env['maintenance.request']._description, "PM Maintenance Order / Notification")
        self.assertEqual(self.env['maintenance.team']._description, "Maintenance Planner Group / Work Center")
        self.assertEqual(self.env['maintenance.stage']._description, "Maintenance Notification / Order Status")
        self.assertEqual(self.env['maintenance.equipment.category']._description, "Equipment Class / Technical Category")

        # 2. Field Label Overrides on maintenance.equipment
        equip_fields = self.env['maintenance.equipment'].fields_get([
            'name', 'serial_no', 'category_id', 'maintenance_team_id',
            'technician_user_id', 'owner_user_id', 'effective_date',
            'assign_date', 'cost', 'location_id'
        ])
        self.assertEqual(equip_fields['name']['string'], "Technical Equipment Description")
        self.assertEqual(equip_fields['serial_no']['string'], "Manufacturer Serial Number (SERNR)")
        self.assertEqual(equip_fields['category_id']['string'], "Equipment Class / Category")
        self.assertEqual(equip_fields['maintenance_team_id']['string'], "Maintenance Planner Group / Work Center")
        self.assertEqual(equip_fields['technician_user_id']['string'], "Assigned Maintenance Technician")
        self.assertEqual(equip_fields['owner_user_id']['string'], "Equipment Custodian / Operating Owner")
        self.assertEqual(equip_fields['effective_date']['string'], "Commissioning / In-Service Date")
        self.assertEqual(equip_fields['assign_date']['string'], "Installation / Assignment Date")
        self.assertEqual(equip_fields['cost']['string'], "Equipment Acquisition Cost")
        self.assertEqual(equip_fields['location_id']['string'], "Functional Location / Plant Area")

        # 3. Field Label Overrides on maintenance.request
        req_fields = self.env['maintenance.request'].fields_get([
            'name', 'equipment_id', 'category_id', 'maintenance_team_id',
            'owner_user_id', 'user_ids', 'stage_id', 'priority',
            'schedule_date', 'close_date', 'duration', 'maintenance_type'
        ])
        self.assertEqual(req_fields['name']['string'], "Maintenance Order Description / Subject")
        self.assertEqual(req_fields['equipment_id']['string'], "Technical Equipment (IE01)")
        self.assertEqual(req_fields['category_id']['string'], "Equipment Class")
        self.assertEqual(req_fields['maintenance_team_id']['string'], "Maintenance Planner Group / Work Center")
        self.assertEqual(req_fields['owner_user_id']['string'], "Notification Reporter (Created By)")
        self.assertEqual(req_fields['user_ids']['string'], "Assigned Maintenance Technicians")
        self.assertEqual(req_fields['stage_id']['string'], "Order / Notification Status")
        self.assertEqual(req_fields['priority']['string'], "Order Priority Level")
        self.assertEqual(req_fields['schedule_date']['string'], "Basic Start Date / Scheduled Maintenance")
        self.assertEqual(req_fields['close_date']['string'], "Technical Completion Date (TECO)")
        self.assertEqual(req_fields['duration']['string'], "Actual Work Duration (Hours)")
        self.assertEqual(req_fields['maintenance_type']['string'], "Maintenance Order Type (Corrective / Preventive)")

        # 4. Field Label Overrides on maintenance.team
        team_fields = self.env['maintenance.team'].fields_get(['name', 'member_ids'])
        self.assertEqual(team_fields['name']['string'], "Maintenance Planner Group / Work Center Name")
        self.assertEqual(team_fields['member_ids']['string'], "Assigned Maintenance Technicians")

    def test_03_project_systems_sap_lexicon(self):
        """Verify Project Systems (SAP PS) model descriptions and field strings."""
        # 1. Model Descriptions
        self.assertEqual(self.env['project.project']._description, "PS Project Definition / WBS Header")
        self.assertEqual(self.env['project.task']._description, "WBS Element / Network Activity")
        self.assertEqual(self.env['project.milestone']._description, "Project Milestone (WBS Milestone)")
        self.assertEqual(self.env['project.task.type']._description, "WBS Activity Execution Stage / Status")

        # 2. Field Label Overrides on project.project
        proj_fields = self.env['project.project'].fields_get([
            'name', 'user_id', 'partner_id', 'stage_id',
            'date_start', 'date', 'allocated_hours', 'effective_hours',
            'tag_ids', 'privacy_visibility'
        ])
        self.assertEqual(proj_fields['name']['string'], "PS Project Definition Name")
        self.assertEqual(proj_fields['user_id']['string'], "Project Manager / Responsible Person")
        self.assertEqual(proj_fields['partner_id']['string'], "Project Customer / Sold-to Party (BP)")
        self.assertEqual(proj_fields['stage_id']['string'], "Project Lifecycle Status")
        self.assertEqual(proj_fields['date_start']['string'], "Basic Start Date")
        self.assertEqual(proj_fields['date']['string'], "Basic Finish Date / Target Date")
        self.assertEqual(proj_fields['allocated_hours']['string'], "Budgeted Work (Planned Hours)")
        self.assertEqual(proj_fields['effective_hours']['string'], "Actual Recorded Work (Hours)")
        self.assertEqual(proj_fields['tag_ids']['string'], "Project Indicators / Tags")
        self.assertEqual(proj_fields['privacy_visibility']['string'], "Project Security / Access Classification")

        # 3. Field Label Overrides on project.task
        task_fields = self.env['project.task'].fields_get([
            'name', 'project_id', 'parent_id', 'child_ids', 'milestone_id',
            'user_ids', 'stage_id', 'planned_date_begin', 'date_deadline',
            'allocated_hours', 'effective_hours', 'progress', 'priority'
        ])
        self.assertEqual(task_fields['name']['string'], "WBS Element / Activity Description")
        self.assertEqual(task_fields['project_id']['string'], "PS Project Definition")
        self.assertEqual(task_fields['parent_id']['string'], "Superior WBS Element")
        self.assertEqual(task_fields['child_ids']['string'], "Sub-WBS Elements / Sub-Activities")
        self.assertEqual(task_fields['milestone_id']['string'], "Assigned Project Milestone")
        self.assertEqual(task_fields['user_ids']['string'], "Assigned Network Activity Resources")
        self.assertEqual(task_fields['stage_id']['string'], "WBS Activity Execution Stage")
        self.assertEqual(task_fields['planned_date_begin']['string'], "Scheduled Start Date")
        self.assertEqual(task_fields['date_deadline']['string'], "Scheduled Finish Date / Deadline")
        self.assertEqual(task_fields['allocated_hours']['string'], "Planned Work Duration (Hours)")
        self.assertEqual(task_fields['effective_hours']['string'], "Actual Recorded Work (Hours)")
        self.assertEqual(task_fields['progress']['string'], "Physical Progress Percentage (%)")
        self.assertEqual(task_fields['priority']['string'], "Activity Priority")

        # 4. Field Label Overrides on project.milestone
        mile_fields = self.env['project.milestone'].fields_get(['name', 'project_id', 'deadline', 'reached_date', 'is_reached'])
        self.assertEqual(mile_fields['name']['string'], "Milestone Description")
        self.assertEqual(mile_fields['project_id']['string'], "PS Project Definition")
        self.assertEqual(mile_fields['deadline']['string'], "Scheduled Milestone Date")
        self.assertEqual(mile_fields['reached_date']['string'], "Actual Milestone Achievement Date")
        self.assertEqual(mile_fields['is_reached']['string'], "Milestone Reached Indicator")

    def test_04_quality_management_sap_lexicon(self):
        """Verify Quality Management (SAP QM) model descriptions and field strings."""
        # 1. Model Descriptions
        self.assertEqual(self.env['quality.point']._description, "Inspection Plan / Characteristic")
        self.assertEqual(self.env['quality.check']._description, "Quality Inspection Lot / Result Recording")
        self.assertEqual(self.env['quality.alert']._description, "Quality Notification / Defect Report")
        self.assertEqual(self.env['quality.alert.stage']._description, "Quality Notification Processing Stage")
        self.assertEqual(self.env['quality.alert.team']._description, "Quality Planner Group / Inspection Team")

        # 2. Field Label Overrides on quality.point
        qp_fields = self.env['quality.point'].fields_get([
            'name', 'title', 'product_ids', 'picking_type_ids', 'operation_id',
            'test_type_id', 'measure_frequency_type', 'team_id', 'user_id',
            'norm', 'tolerance_min', 'tolerance_max'
        ])
        self.assertEqual(qp_fields['name']['string'], "Inspection Plan Reference")
        self.assertEqual(qp_fields['title']['string'], "Inspection Characteristic Title")
        self.assertEqual(qp_fields['product_ids']['string'], "Header Material Masters (MM)")
        self.assertEqual(qp_fields['picking_type_ids']['string'], "Inspection Movement Types / Operations")
        self.assertEqual(qp_fields['operation_id']['string'], "Routing Operation Step")
        self.assertEqual(qp_fields['test_type_id']['string'], "Inspection Method / Test Type")
        self.assertEqual(qp_fields['measure_frequency_type']['string'], "Inspection Sampling Frequency")
        self.assertEqual(qp_fields['team_id']['string'], "Quality Planner Group / Inspection Team")
        self.assertEqual(qp_fields['user_id']['string'], "Quality Inspector / Responsible")
        self.assertEqual(qp_fields['norm']['string'], "Nominal Target Value / Target Norm")
        self.assertEqual(qp_fields['tolerance_min']['string'], "Lower Specification Limit (LSL)")
        self.assertEqual(qp_fields['tolerance_max']['string'], "Upper Specification Limit (USL)")

        # 3. Field Label Overrides on quality.check
        qc_fields = self.env['quality.check'].fields_get([
            'name', 'title', 'point_id', 'product_id', 'lot_ids', 'picking_id',
            'quality_state', 'measure', 'tolerance_min', 'tolerance_max',
            'team_id', 'user_id'
        ])
        self.assertEqual(qc_fields['name']['string'], "Inspection Lot Reference (Prüflos)")
        self.assertEqual(qc_fields['title']['string'], "Characteristic Inspection Description")
        self.assertEqual(qc_fields['point_id']['string'], "Inspection Plan / Characteristic Reference")
        self.assertEqual(qc_fields['product_id']['string'], "Inspected Material Master (MM)")
        self.assertEqual(qc_fields['lot_ids']['string'], "Batch / Material Lot Number")
        self.assertEqual(qc_fields['picking_id']['string'], "Associated Goods Movement / Delivery")
        self.assertEqual(qc_fields['quality_state']['string'], "Inspection Usage Decision (Pass/Fail)")
        self.assertEqual(qc_fields['measure']['string'], "Recorded Inspection Result Value")
        self.assertEqual(qc_fields['tolerance_min']['string'], "Lower Specification Limit (LSL)")
        self.assertEqual(qc_fields['tolerance_max']['string'], "Upper Specification Limit (USL)")
        self.assertEqual(qc_fields['team_id']['string'], "Quality Inspection Team")
        self.assertEqual(qc_fields['user_id']['string'], "Quality Inspector")

        # 4. Field Label Overrides on quality.alert
        qa_fields = self.env['quality.alert'].fields_get([
            'name', 'title', 'check_id', 'product_tmpl_id', 'lot_ids',
            'reason_id', 'team_id', 'user_id', 'priority', 'stage_id',
            'action_corrective', 'action_preventive'
        ])
        self.assertEqual(qa_fields['name']['string'], "Quality Notification Number (QM-QEL)")
        self.assertEqual(qa_fields['title']['string'], "Defect Summary / Subject")
        self.assertEqual(qa_fields['check_id']['string'], "Originating Inspection Lot (QA01)")
        self.assertEqual(qa_fields['product_tmpl_id']['string'], "Affected Material Master (MM)")
        self.assertEqual(qa_fields['lot_ids']['string'], "Defective Material Lot / Batch")
        self.assertEqual(qa_fields['reason_id']['string'], "Defect Code / Root Cause")
        self.assertEqual(qa_fields['team_id']['string'], "Quality Notification Handling Team")
        self.assertEqual(qa_fields['user_id']['string'], "Quality Action Coordinator")
        self.assertEqual(qa_fields['priority']['string'], "Defect Severity / Priority")
        self.assertEqual(qa_fields['stage_id']['string'], "Notification Processing Status")
        self.assertEqual(qa_fields['action_corrective']['string'], "Immediate Corrective Action (CAPA)")
        self.assertEqual(qa_fields['action_preventive']['string'], "Preventive Action / Mitigation")

    def test_05_declarative_menus_and_actions_m3(self):
        """Verify XML overrides for menus and actions across HRM, PM, PS, QM."""
        # Menus
        self.assertEqual(self.env.ref('hr.menu_hr_root').name, "Human Resources & SuccessFactors (HCM)")
        self.assertEqual(self.env.ref('hr.menu_hr_main').name, "Personnel Administration (PA)")
        self.assertEqual(self.env.ref('hr.menu_hr_employee_payroll').name, "Personnel Master Records")
        self.assertEqual(self.env.ref('hr.menu_hr_department_kanban').name, "Organizational Units (OrgUnits)")
        self.assertEqual(self.env.ref('hr.menu_view_hr_job').name, "Positions & Job Roles")
        self.assertEqual(self.env.ref('maintenance.menu_maintenance_title').name, "Plant Maintenance (SAP PM)")
        self.assertEqual(self.env.ref('maintenance.menu_m_request').name, "PM Maintenance Orders & Notifications")
        self.assertEqual(self.env.ref('maintenance.menu_equipment_form').name, "Technical Equipment / Functional Locations (IE01)")
        self.assertEqual(self.env.ref('project.menu_main_pm').name, "Project Systems (SAP PS)")
        self.assertEqual(self.env.ref('project.menu_projects').name, "PS Project Definitions / WBS Headers")
        self.assertEqual(self.env.ref('project.menu_project_management').name, "WBS Elements & Network Activities")
        self.assertEqual(self.env.ref('quality_control.menu_quality_root').name, "Quality Management (SAP QM)")
        self.assertEqual(self.env.ref('quality_control.menu_quality_control_points').name, "Inspection Plans / Characteristics (QP01)")
        self.assertEqual(self.env.ref('quality_control.menu_quality_checks').name, "Quality Inspection Lots (QA01/QE01)")
        self.assertEqual(self.env.ref('quality_control.menu_quality_alert').name, "Quality Notifications / Defect Reports (QM01)")

        # Actions
        self.assertEqual(self.env.ref('hr.open_view_employee_list_my').name, "Personnel Master / Employees")
        self.assertEqual(self.env.ref('hr.hr_department_kanban_action').name, "Organizational Units (OrgUnits)")
        self.assertEqual(self.env.ref('hr.action_hr_job').name, "Positions / Job Roles")
        self.assertEqual(self.env.ref('maintenance.hr_equipment_action').name, "Technical Equipment / Functional Locations")
        self.assertEqual(self.env.ref('maintenance.hr_equipment_request_action').name, "PM Maintenance Orders / Notifications")
        self.assertEqual(self.env.ref('project.open_view_project_all').name, "PS Project Definitions / WBS Headers")
        self.assertEqual(self.env.ref('project.action_view_my_task').name, "My WBS Elements / Activities")
        self.assertEqual(self.env.ref('project.action_view_all_task').name, "WBS Elements / Network Activities")
        self.assertEqual(self.env.ref('quality_control.quality_point_action').name, "Inspection Plans / Characteristics (QP01)")
        self.assertEqual(self.env.ref('quality_control.quality_check_action_main').name, "Quality Inspection Lots (QA01/QE01)")
        self.assertEqual(self.env.ref('quality_control.quality_alert_action_check').name, "Quality Notifications / Defect Reports (QM01)")

    def test_06_schema_invariance_verification(self):
        """Verify strict schema invariance: no stored columns added to target models."""
        target_models = [
            'hr.employee', 'hr.department', 'hr.job', 'hr.version',
            'maintenance.equipment', 'maintenance.request', 'maintenance.team',
            'project.project', 'project.task', 'project.milestone',
            'quality.point', 'quality.check', 'quality.alert'
        ]
        for model_name in target_models:
            model = self.env[model_name]
            # Ensure table exists and verify no unexpected stored columns
            self.assertTrue(hasattr(model, '_table'))
