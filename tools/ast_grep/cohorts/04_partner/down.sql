-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 4: ROLLBACK SCRIPT
-- Revert: party.master -> res.partner (Table: res_partner)
-- =============================================================================

BEGIN;

-- 1. Drop Updatable View Facade
DROP VIEW IF EXISTS res_partner CASCADE;

-- 2. Restore Physical Table & Sequence
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'party_master' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE party_master RENAME TO res_partner;
        ALTER SEQUENCE party_master_id_seq RENAME TO res_partner_id_seq;
        ALTER TABLE res_partner ALTER COLUMN id SET DEFAULT nextval('res_partner_id_seq'::regclass);
    END IF;
END $$;

-- 3. Revert Metamodel Injection
UPDATE ir_model 
SET model = 'res.partner' 
WHERE model = 'party.master';

UPDATE ir_model_fields 
SET model = 'res.partner' 
WHERE model = 'party.master';

UPDATE ir_model_fields 
SET relation = 'res.partner' 
WHERE relation = 'party.master';

UPDATE ir_ui_view 
SET model = 'res.partner' 
WHERE model = 'party.master';

UPDATE ir_act_window 
SET res_model = 'res.partner' 
WHERE res_model = 'party.master';

UPDATE ir_model_data 
SET model = 'res.partner' 
WHERE model = 'party.master';

COMMIT;
