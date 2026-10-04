-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 2: system.attachment -> ir.attachment (ROLLBACK)
-- Reversible Rollback to Legacy Genesis Schema
-- =============================================================================

BEGIN;

-- 1. Safely Drop Updatable Compatibility View if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'ir_attachment') THEN
        EXECUTE 'DROP VIEW ir_attachment CASCADE';
    END IF;
END $$;

-- 2. Restore Physical Table & Sequence if renamed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'system_attachment' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE system_attachment RENAME TO ir_attachment;
        ALTER SEQUENCE system_attachment_id_seq RENAME TO ir_attachment_id_seq;
        ALTER TABLE ir_attachment ALTER COLUMN id SET DEFAULT nextval('ir_attachment_id_seq'::regclass);
    END IF;
END $$;

-- 3. Restore ORM Metamodel Entries
UPDATE ir_model 
SET model = 'ir.attachment' 
WHERE model = 'system.attachment';

UPDATE ir_model_fields 
SET model = 'ir.attachment' 
WHERE model = 'system.attachment';

UPDATE ir_model_fields 
SET relation = 'ir.attachment' 
WHERE relation = 'system.attachment';

UPDATE ir_ui_view 
SET model = 'ir.attachment' 
WHERE model = 'system.attachment';

UPDATE ir_act_window 
SET res_model = 'ir.attachment' 
WHERE res_model = 'system.attachment';

UPDATE ir_model_data 
SET model = 'ir.attachment' 
WHERE model = 'system.attachment';

COMMIT;
