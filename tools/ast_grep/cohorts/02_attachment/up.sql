-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 2: ir.attachment -> system.attachment
-- IBM Enterprise Data Architecture Standard (Digital Asset & Document Foundation)
-- Phase 1 (The Bridge): Physical Table Rename + Updatable View Facade
-- Phase 2 (Metadata Injection): Pre-Boot ORM Metamodel Synchronization
-- =============================================================================

BEGIN;

-- 1. Physical Table & Sequence Rename to IBM Canonical system_attachment
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ir_attachment' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE ir_attachment RENAME TO system_attachment;
        ALTER SEQUENCE ir_attachment_id_seq RENAME TO system_attachment_id_seq;
        ALTER TABLE system_attachment ALTER COLUMN id SET DEFAULT nextval('system_attachment_id_seq'::regclass);
    END IF;
END $$;

-- 2. Updatable Compatibility View Facade (Zero-Downtime Bridge)
-- In PostgreSQL 9.3+, simple views are automatically updatable.
-- INSERT, UPDATE, and DELETE pass through directly to underlying tables.
CREATE OR REPLACE VIEW ir_attachment AS 
    SELECT * FROM system_attachment;

-- 3. Pre-Boot ORM Metamodel Injection
UPDATE ir_model 
SET model = 'system.attachment' 
WHERE model = 'ir.attachment';

UPDATE ir_model_fields 
SET model = 'system.attachment' 
WHERE model = 'ir.attachment';

UPDATE ir_model_fields 
SET relation = 'system.attachment' 
WHERE relation = 'ir.attachment';

UPDATE ir_ui_view 
SET model = 'system.attachment' 
WHERE model = 'ir.attachment';

UPDATE ir_act_window 
SET res_model = 'system.attachment' 
WHERE res_model = 'ir.attachment';

UPDATE ir_model_data 
SET model = 'system.attachment' 
WHERE model = 'ir.attachment';

COMMIT;
