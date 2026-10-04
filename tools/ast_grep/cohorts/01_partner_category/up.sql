-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 1: res.partner.category
-- Phase 1 (The Bridge): Physical Table Rename + Updatable View Facade
-- Phase 2 (Metadata Injection): Pre-Boot ORM Metamodel Synchronization
-- =============================================================================

BEGIN;

-- 1. Physical Table & Sequence Rename
ALTER TABLE res_partner_category RENAME TO insilos_partner_category;
ALTER SEQUENCE res_partner_category_id_seq RENAME TO insilos_partner_category_id_seq;
ALTER TABLE insilos_partner_category ALTER COLUMN id SET DEFAULT nextval('insilos_partner_category_id_seq'::regclass);

-- 2. Many2Many Relation Table Rename
ALTER TABLE res_partner_res_partner_category_rel RENAME TO insilos_partner_category_rel;

-- 3. Updatable Compatibility View Facades (Zero-Downtime Bridge)
-- In PostgreSQL 9.3+, simple views are automatically updatable.
-- INSERT, UPDATE, and DELETE pass through directly to underlying tables.
CREATE OR REPLACE VIEW res_partner_category AS 
    SELECT * FROM insilos_partner_category;

CREATE OR REPLACE VIEW res_partner_res_partner_category_rel AS 
    SELECT * FROM insilos_partner_category_rel;

-- 4. Pre-Boot ORM Metamodel Injection
UPDATE ir_model 
SET model = 'insilos.partner.category' 
WHERE model = 'res.partner.category';

UPDATE ir_model_fields 
SET model = 'insilos.partner.category' 
WHERE model = 'res.partner.category';

UPDATE ir_model_fields 
SET relation = 'insilos.partner.category' 
WHERE relation = 'res.partner.category';

UPDATE ir_ui_view 
SET model = 'insilos.partner.category' 
WHERE model = 'res.partner.category';

UPDATE ir_act_window 
SET res_model = 'insilos.partner.category' 
WHERE res_model = 'res.partner.category';

UPDATE ir_model_data 
SET model = 'insilos.partner.category' 
WHERE model = 'res.partner.category';

COMMIT;
