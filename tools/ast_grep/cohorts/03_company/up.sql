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

-- 2.1 M2M Relation Updatable Views
DO $$
DECLARE
    r RECORD;
    v_new_table TEXT;
    v_col1 TEXT;
    v_col2 TEXT;
BEGIN
    FOR r IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%res_company%rel%' AND table_type = 'BASE TABLE'
    LOOP
        v_new_table := replace(r.table_name, 'res_company', 'organization_unit');
        SELECT column_name INTO v_col1 FROM information_schema.columns WHERE table_name = r.table_name ORDER BY ordinal_position LIMIT 1;
        SELECT column_name INTO v_col2 FROM information_schema.columns WHERE table_name = r.table_name ORDER BY ordinal_position OFFSET 1 LIMIT 1;
        
        IF v_col1 = 'res_company_id' THEN
            EXECUTE format('CREATE OR REPLACE VIEW %I AS SELECT res_company_id AS organization_unit_id, %I FROM %I', v_new_table, v_col2, r.table_name);
        ELSIF v_col2 = 'res_company_id' THEN
            EXECUTE format('CREATE OR REPLACE VIEW %I AS SELECT %I, res_company_id AS organization_unit_id FROM %I', v_new_table, v_col1, r.table_name);
        ELSE
            EXECUTE format('CREATE OR REPLACE VIEW %I AS SELECT * FROM %I', v_new_table, r.table_name);
        END IF;
    END LOOP;
END $$;

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
