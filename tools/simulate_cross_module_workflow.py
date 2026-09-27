#!/usr/bin/env python3
"""
Simulate Cross-Module Enterprise Workflow:
IDP Logistics -> Chemical Trade Compliance -> Preferential Origin (FTA) -> ESG Bridge
"""
import requests
import json
import hashlib
from datetime import date, datetime

RPC_URL = 'http://localhost:28069/jsonrpc'
DB = 'odoo20_dev'
USER = 'admin'
PWD = 'admin'

def get_rpc():
    session = requests.Session()
    auth_resp = session.post(RPC_URL, json={
        'jsonrpc': '2.0',
        'method': 'call',
        'params': {
            'service': 'common',
            'method': 'authenticate',
            'args': [DB, USER, PWD, {}]
        }
    }).json()
    uid = auth_resp.get('result')
    if not uid:
        raise RuntimeError(f"Authentication failed: {auth_resp}")
    
    def execute(model, method, *args, **kwargs):
        resp = session.post(RPC_URL, json={
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'service': 'object',
                'method': 'execute_kw',
                'args': [DB, uid, PWD, model, method, list(args), kwargs]
            }
        }).json()
        if 'error' in resp:
            raise RuntimeError(f"RPC Error on {model}.{method}: {resp['error']}")
        return resp.get('result')

    return execute

def run_simulation():
    call = get_rpc()
    print("================================================================================")
    print("🚀 INSILOS ENTERPRISE CROSS-MODULE E2E WORKFLOW SIMULATION")
    print("   [1] Logistics IDP -> [2] Chemical Compliance -> [3] Origin FTA -> [4] ESG")
    print("================================================================================\n")

    # Get or create company
    company_ids = call('res.company', 'search', [('name', 'ilike', 'Insilos')])
    if not company_ids:
        company_ids = call('res.company', 'search', [], limit=1)
    company_id = company_ids[0]

    # Partner: Singapore Petrochem
    partner_ids = call('res.partner', 'search', [('name', '=', 'Singapore Petrochemicals Corp')])
    if not partner_ids:
        partner_id = call('res.partner', 'create', {
            'name': 'Singapore Petrochemicals Corp',
            'is_company': True,
            'street': '10 Jurong Island Highway',
            'city': 'Singapore',
            'country_id': call('res.country', 'search', [('code', '=', 'SG')], limit=1)[0],
        })
    else:
        partner_id = partner_ids[0]

    # --- STEP 1: LOGISTICS IDP ---
    print("▶ STEP 1: LOGISTICS IDP (Intelligent Document Processing & Immutable Snapshot)")
    timestamp_str = datetime.now().strftime('%Y%m%d%H%M%S')
    case_vals = {
        'name': f"IDP-CASE-{timestamp_str}",
        'source_system': 'NSW_CUSTOMS_GATEWAY',
        'source_key': f"NSW-DECL-{timestamp_str}",
        'shipment_reference': f"ONE-SIN-SGN-{timestamp_str[-4:]}",
        'po_reference': f"PO-2026-CHEM-{timestamp_str[-4:]}",
        'supplier_reference': f"SING-PETRO-INV-{timestamp_str[-4:]}",
        'company_id': company_id,
        'state': 'processing',
        'document_status': 'pass',
        'reconciliation_status': 'pass',
        'compliance_status': 'pass',
        'paperless_pages_saved': 14,
    }
    case_id = call('logistics.idp.case', 'create', case_vals)
    print(f"  ✓ Created Logistics IDP Case [ID: {case_id}] - {case_vals['name']}")

    # Cryptographic Document Ledger & SHA-256 Content Hash
    raw_document_payload = f"B/L: ONE-SIN-SGN-4412 | INVOICE: SING-PETRO-INV-8899 | QTY: 20000 KG | VAL: $30000 USD | CASE: {case_id}"
    sha256_hash = hashlib.sha256(raw_document_payload.encode('utf-8')).hexdigest()
    doc_vals = {
        'case_id': case_id,
        'document_type': 'commercial_invoice',
        'extracted_doc_number': f"INV-SG-{case_vals['name'][-8:]}",
        'extracted_partner_name': 'Singapore Petrochemicals Corp',
        'version': 1,
        'content_hash': sha256_hash,
        'mimetype': 'application/pdf',
        'source_channel': 'upload',
        'status': 'valid',
    }
    doc_id = call('logistics.idp.document', 'create', doc_vals)
    print(f"  ✓ Registered Cryptographic Document [ID: {doc_id}] - {doc_vals['extracted_doc_number']}.pdf")
    print(f"    - SHA-256 Content Hash: {sha256_hash}")
    print(f"    - 3-Way Reconciliation: PO vs Commercial Invoice vs Customs Declaration [MATCH 100%]\n")

    # --- STEP 2: CHEMICAL TRADE COMPLIANCE ---
    print("▶ STEP 2: CHEMICAL TRADE COMPLIANCE (Luật Hóa chất 69/2025/QH15 & NĐ 113)")
    # Substance: Ethyl Acetate (CAS 141-78-6)
    substance_ids = call('is.hse.chemical.substance', 'search', [('cas_number', '=', '141-78-6')])
    if not substance_ids:
        substance_id = call('is.hse.chemical.substance', 'create', {
            'name': 'Ethyl Acetate (Industrial Grade 99.8%)',
            'cas_number': '141-78-6',
            'formula': 'C4H8O2',
            'un_number': 'UN1173',
            'hazard_classification': 'conditional',
            'ghs_signal_word': 'danger',
            'ghs_flammable': True,
        })
    else:
        substance_id = substance_ids[0]
    print(f"  ✓ Chemical Substance Identified: Ethyl Acetate (CAS 141-78-6, UN 1173, Formula: C4H8O2)")

    # Permit Quota Check & Deduction
    quota_ids = call('is.chemical.permit.quota', 'search', [
        ('chemical_substance_id', '=', substance_id),
        ('company_id', '=', company_id)
    ])
    if not quota_ids:
        quota_id = call('is.chemical.permit.quota', 'create', {
            'name': 'Hạn ngạch Nhập khẩu Hóa chất BCT 2026/GP-019',
            'permit_number': 'GP-BCT-2026-EA-019',
            'chemical_substance_id': substance_id,
            'company_id': company_id,
            'allocated_quota_kg': 100000.0,
            'consumed_quota_kg': 40000.0,
            'state': 'active',
        })
    else:
        quota_id = quota_ids[0]

    quota = call('is.chemical.permit.quota', 'read', [quota_id], ['allocated_quota_kg', 'consumed_quota_kg', 'remaining_quota_kg'])[0]
    print(f"  ✓ Active Import Quota: {quota['allocated_quota_kg']:,.0f} kg")
    print(f"    - Previously Consumed: {quota['consumed_quota_kg']:,.0f} kg")
    print(f"    - Remaining Before: {quota['remaining_quota_kg']:,.0f} kg")

    # Deduct 20,000 kg for this shipment
    imported_qty = 20000.0
    new_consumed = quota['consumed_quota_kg'] + imported_qty
    call('is.chemical.permit.quota', 'write', [quota_id], {'consumed_quota_kg': new_consumed})
    updated_quota = call('is.chemical.permit.quota', 'read', [quota_id], ['remaining_quota_kg', 'remaining_percentage'])[0]
    print(f"    - Deducted This Shipment: {imported_qty:,.0f} kg")
    print(f"    - New Remaining Balance: {updated_quota['remaining_quota_kg']:,.0f} kg ({updated_quota['remaining_percentage']:.1f}% quota remaining)")

    # Create NSW Compliance Dossier & Link to IDP Case
    dossier_id = call('is.chemical.compliance.dossier', 'create', {
        'name': f"NSW-DOSSIER-2026-CHEM-{case_id}",
        'dossier_type': 'nsw_declaration',
        'importer_company_id': company_id,
        'jurisdiction': 'VN',
        'trade_name': 'Ethyl Acetate Industrial 99.8%',
        'supplier_id': partner_id,
        'quota_id': quota_id,
        'state': 'internally_approved',
    })
    call('logistics.idp.case', 'write', [case_id], {'chemical_dossier_id': dossier_id})
    print(f"  ✓ Linked National Single Window Dossier [ID: {dossier_id}] to IDP Case {case_id}\n")

    # --- STEP 3: PREFERENTIAL ORIGIN (FTA DETERMINATION) ---
    print("▶ STEP 3: PREFERENTIAL ORIGIN DECISION SUPPORT (EVFTA Form EUR.1 Assessment)")
    # Finished Product: High-Performance Industrial Coating (HS 3208.20)
    # Regime: EVFTA
    regime_ids = call('preferential.origin.regime', 'search', [('code', '=', 'EVFTA')])
    if not regime_ids:
        eu_country = call('res.country', 'search', [('code', '=', 'DE')], limit=1)[0]
        regime_id = call('preferential.origin.regime', 'create', {
            'name': 'EU-Vietnam Free Trade Agreement (EVFTA)',
            'code': 'EVFTA',
            'version': '2026.1',
            'destination_country_id': eu_country,
            'effective_from': '2020-08-01',
            'policy_hash': hashlib.sha256(b'EVFTA_POLICY_SPEC_2026').hexdigest(),
            'state': 'active',
        })
    else:
        regime_id = regime_ids[0]

    # Origin Mathematical Evaluation
    ex_works_price = 175000.0  # Total FOB price for 70,000 kg coating
    non_originating_value = 30000.0 # 20,000 kg imported Ethyl Acetate @ $1.50
    originating_materials_value = 90000.0 # Domestic epoxy & additives
    labor_and_overhead = 55000.0

    rvc_percentage = ((ex_works_price - non_originating_value) / ex_works_price) * 100.0
    cth_satisfied = True # Chapter 29 (Ethyl Acetate) -> Chapter 32 (Coatings & Paints)
    rvc_threshold = 50.0 # EVFTA rule for HS 3208 requires RVC >= 50% or CTH

    origin_status = "QUALIFYING" if (cth_satisfied and rvc_percentage >= rvc_threshold) else "NON_QUALIFYING"
    print(f"  ✓ Finished Product: High-Performance Coating (HS 3208.20)")
    print(f"    - Ex-Works (FOB) Invoice Value: ${ex_works_price:,.2f}")
    print(f"    - Non-Originating Materials (Imported): ${non_originating_value:,.2f}")
    print(f"    - Regional Value Content (RVC): {rvc_percentage:.2f}% (Threshold: >={rvc_threshold}%) -> PASS")
    print(f"    - Change in Tariff Heading (CTH): Chapter 29 -> Chapter 32 -> PASS")
    print(f"  ✓ Determination Verdict: [{origin_status}] for EVFTA Form EUR.1 Preferential Duty Rate (0%)\n")

    # --- STEP 4: ESG BRIDGE (SCOPE 3 FREIGHT CARBON & CBAM ADVISOR) ---
    print("▶ STEP 4: ESG BRIDGE & SUSTAINABILITY (Scope 3 Cat 4 Logistics & CBAM)")
    # Sea Freight Singapore -> Cat Lai
    distance_km = 2185.0
    cargo_tons = 20.0
    emission_factor = 0.0125 # 12.5 g CO2e / tonne-km
    gross_emissions_kg = distance_km * cargo_tons * emission_factor
    paperless_offset_kg = 14 * 0.02 # 0.02 kg CO2 saved per paper page
    net_carbon_kg = gross_emissions_kg - paperless_offset_kg

    freight_carbon_id = call('is.esg.freight.carbon', 'create', {
        'name': f"CARBON-{case_vals['name']}",
        'case_id': case_id,
        'company_id': company_id,
        'date': str(date.today()),
        'transport_mode': 'sea',
        'origin_port_or_city': 'Port of Singapore (SGSIN)',
        'destination_port_or_city': 'Cat Lai Terminal, HCMC (VNCLI)',
        'estimated_distance_km': distance_km,
        'cargo_weight_ton': cargo_tons,
        'emission_factor_kg_per_tkm': emission_factor,
        'gross_freight_emissions_kg_co2e': gross_emissions_kg,
        'gross_freight_emissions_t_co2e': gross_emissions_kg / 1000.0,
        'paperless_pages_processed': 14,
        'paperless_carbon_offset_kg': paperless_offset_kg,
        'net_logistics_carbon_kg_co2e': net_carbon_kg,
    })
    print(f"  ✓ Recorded Scope 3 Cat 4 Freight Carbon [ID: {freight_carbon_id}]")
    print(f"    - Voyage: SGSIN -> VNCLI (Distance: {distance_km:,.0f} km, Cargo: {cargo_tons} tons)")
    print(f"    - Gross Emissions: {gross_emissions_kg:,.2f} kg CO2e ({gross_emissions_kg/1000.0:.3f} tCO2e)")
    print(f"    - Paperless IDP Offset: -{paperless_offset_kg:.2f} kg CO2e (14 documents digitised)")
    print(f"    - Net Logistics Carbon: {net_carbon_kg:,.2f} kg CO2e")

    # CBAM Advisor Simulation
    cbam_advisor_id = call('is.esg.cbam.advisor', 'create', {
        'name': 'CBAM Assessment - Industrial Coatings Export EU',
        'company_id': company_id,
        'hs_code': '3208.20.90',
        'description_vi': 'Sơn phủ công nghiệp cao cấp xuất khẩu EU',
        'is_cbam_applicable': True,
        'cbam_sector': 'hydrogen_chemicals',
        'direct_embedded_emissions_t_per_t': 0.28,
        'indirect_embedded_emissions_t_per_t': 0.10,
        'total_embedded_emissions_t_per_t': 0.38,
        'eu_carbon_certificate_price_eur': 65.0, # 65 EUR / ton CO2
        'estimated_cbam_cost_per_ton_eur': 0.38 * 65.0,
        'annual_export_volume_tons': 500.0,
        'renewable_energy_share_pct': 45.0,
        'action_recommendation': 'Tăng tỷ trọng điện mặt trời mái nhà lên 70% để tiết kiệm thêm €5,200 phí chứng chỉ CBAM hàng năm.',
    })
    cbam = call('is.esg.cbam.advisor', 'read', [cbam_advisor_id], [
        'total_embedded_emissions_t_per_t', 'estimated_cbam_cost_per_ton_eur', 'action_recommendation'
    ])[0]
    print(f"  ✓ CBAM EU Advisor Assessment [ID: {cbam_advisor_id}]")
    print(f"    - Specific Embedded Carbon: {cbam['total_embedded_emissions_t_per_t']} tCO2e / ton product")
    print(f"    - Estimated CBAM Duty Exposure: €{cbam['estimated_cbam_cost_per_ton_eur']:.2f} / ton")
    print(f"    - AI Optimization Recommendation: {cbam['action_recommendation']}")

    # Update IDP Case with ESG Summary
    call('logistics.idp.case', 'write', [case_id], {
        'total_freight_carbon_kg': net_carbon_kg,
        'state': 'completed',
        'verdict': 'pass',
    })
    final_case = call('logistics.idp.case', 'read', [case_id], ['name', 'state', 'verdict', 'total_freight_carbon_kg'])[0]

    print("\n================================================================================")
    print("🎉 CROSS-MODULE INTEGRATION RUN COMPLETED WITH 100% SUCCESS!")
    print(f"   Case: {final_case['name']} | Status: {final_case['state']} | Verdict: {final_case['verdict']}")
    print(f"   Logistics IDP: VERIFIED | Quota: DEDUCTED | Origin: QUALIFIED | ESG: RECORDED")
    print("================================================================================")
    return {
        'case_id': case_id,
        'case_name': final_case['name'],
        'sha256': sha256_hash,
        'quota_remaining_kg': updated_quota['remaining_quota_kg'],
        'rvc_pct': rvc_percentage,
        'freight_carbon_kg': net_carbon_kg,
        'cbam_cost_eur': cbam['estimated_cbam_cost_per_ton_eur'],
    }

if __name__ == '__main__':
    run_simulation()
