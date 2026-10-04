-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 3: res.company -> organization.unit
-- IBM Enterprise Data Architecture Standard (Operating Unit / Legal Entity)
-- Phase 1 (The Bridge): Physical Table Rename + Updatable View Facade
-- Phase 2 (Metadata Injection): Pre-Boot ORM Metamodel Synchronization
-- =============================================================================

BEGIN;

-- 1. Physical Table & Sequence Rename to IBM Canonical organization_unit
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'res_company' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE res_company RENAME TO organization_unit;
        ALTER SEQUENCE res_company_id_seq RENAME TO organization_unit_id_seq;
        ALTER TABLE organization_unit ALTER COLUMN id SET DEFAULT nextval('organization_unit_id_seq'::regclass);
    END IF;
END $$;

-- 2. Updatable Compatibility View Facade (Zero-Downtime Bridge)
-- In PostgreSQL 9.3+, simple views are automatically updatable.
-- INSERT, UPDATE, and DELETE pass through directly to underlying tables.
CREATE OR REPLACE VIEW res_company AS 
    SELECT * FROM organization_unit;

-- 3. Pre-Boot ORM Metamodel Injection
UPDATE ir_model 
SET model = 'organization.unit' 
WHERE model = 'res.company';

UPDATE ir_model_fields 
SET model = 'organization.unit' 
WHERE model = 'res.company';

UPDATE ir_model_fields 
SET relation = 'organization.unit' 
WHERE relation = 'res.company';

UPDATE ir_ui_view 
SET model = 'organization.unit' 
WHERE model = 'res.company';

UPDATE ir_act_window 
SET res_model = 'organization.unit' 
WHERE res_model = 'res.company';

UPDATE ir_model_data 
SET model = 'organization.unit' 
WHERE model = 'res.company';

COMMIT;
