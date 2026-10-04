-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 1: res.partner.category (ROLLBACK)
-- Reversible Rollback to Legacy Genesis Schema
-- =============================================================================

BEGIN;

-- 1. Safely Drop Updatable Compatibility Views if they exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'res_partner_category') THEN
        EXECUTE 'DROP VIEW res_partner_category CASCADE';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'res_partner_res_partner_category_rel') THEN
        EXECUTE 'DROP VIEW res_partner_res_partner_category_rel CASCADE';
    END IF;
END $$;

-- 2. Restore Physical Tables & Sequences if renamed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'insilos_partner_category' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE insilos_partner_category RENAME TO res_partner_category;
        ALTER SEQUENCE insilos_partner_category_id_seq RENAME TO res_partner_category_id_seq;
        ALTER TABLE res_partner_category ALTER COLUMN id SET DEFAULT nextval('res_partner_category_id_seq'::regclass);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'insilos_partner_category_rel' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE insilos_partner_category_rel RENAME TO res_partner_res_partner_category_rel;
    END IF;
END $$;

-- 3. Restore ORM Metamodel Entries
UPDATE ir_model 
SET model = 'res.partner.category' 
WHERE model = 'insilos.partner.category';

UPDATE ir_model_fields 
SET model = 'res.partner.category' 
WHERE model = 'insilos.partner.category';

UPDATE ir_model_fields 
SET relation = 'res.partner.category' 
WHERE relation = 'insilos.partner.category';

UPDATE ir_ui_view 
SET model = 'res.partner.category' 
WHERE model = 'insilos.partner.category';

UPDATE ir_act_window 
SET res_model = 'res.partner.category' 
WHERE res_model = 'insilos.partner.category';

UPDATE ir_model_data 
SET model = 'res.partner.category' 
WHERE model = 'insilos.partner.category';

COMMIT;
