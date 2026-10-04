-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 3: ROLLBACK SCRIPT
-- Revert: organization.unit -> res.company (Table: res_company)
-- =============================================================================

BEGIN;

-- 1. Drop Updatable View Facade
DROP VIEW IF EXISTS res_company CASCADE;

-- 2. Restore Physical Table & Sequence
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'organization_unit' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE organization_unit RENAME TO res_company;
        ALTER SEQUENCE organization_unit_id_seq RENAME TO res_company_id_seq;
        ALTER TABLE res_company ALTER COLUMN id SET DEFAULT nextval('res_company_id_seq'::regclass);
    END IF;
END $$;

-- 3. Revert Metamodel Injection
UPDATE ir_model 
SET model = 'res.company' 
WHERE model = 'organization.unit';

UPDATE ir_model_fields 
SET model = 'res.company' 
WHERE model = 'organization.unit';

UPDATE ir_model_fields 
SET relation = 'res.company' 
WHERE relation = 'organization.unit';

UPDATE ir_ui_view 
SET model = 'res.company' 
WHERE model = 'organization.unit';

UPDATE ir_act_window 
SET res_model = 'res.company' 
WHERE res_model = 'organization.unit';

UPDATE ir_model_data 
SET model = 'res.company' 
WHERE model = 'organization.unit';

COMMIT;
