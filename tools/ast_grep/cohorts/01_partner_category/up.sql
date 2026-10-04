-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 1: res.partner.category -> party.classification
-- IBM Enterprise Data Architecture Standard (Party Classification)
-- Phase 1 (The Bridge): Physical Table Rename + Updatable View Facade
-- Phase 2 (Metadata Injection): Pre-Boot ORM Metamodel Synchronization
-- =============================================================================

BEGIN;

-- 1. Physical Table & Sequence Rename to IBM Canonical party_classification
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'res_partner_category' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE res_partner_category RENAME TO party_classification;
        ALTER SEQUENCE res_partner_category_id_seq RENAME TO party_classification_id_seq;
        ALTER TABLE party_classification ALTER COLUMN id SET DEFAULT nextval('party_classification_id_seq'::regclass);
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'insilos_partner_category' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE insilos_partner_category RENAME TO party_classification;
        ALTER SEQUENCE insilos_partner_category_id_seq RENAME TO party_classification_id_seq;
        ALTER TABLE party_classification ALTER COLUMN id SET DEFAULT nextval('party_classification_id_seq'::regclass);
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'res_partner_res_partner_category_rel' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE res_partner_res_partner_category_rel RENAME TO party_classification_rel;
    ELSIF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'insilos_partner_category_rel' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE insilos_partner_category_rel RENAME TO party_classification_rel;
    END IF;
END $$;

-- 2. Updatable Compatibility View Facades (Zero-Downtime Bridge)
-- In PostgreSQL 9.3+, simple views are automatically updatable.
-- INSERT, UPDATE, and DELETE pass through directly to underlying tables.
CREATE OR REPLACE VIEW res_partner_category AS 
    SELECT * FROM party_classification;

CREATE OR REPLACE VIEW insilos_partner_category AS 
    SELECT * FROM party_classification;

CREATE OR REPLACE VIEW res_partner_res_partner_category_rel AS 
    SELECT * FROM party_classification_rel;

CREATE OR REPLACE VIEW insilos_partner_category_rel AS 
    SELECT * FROM party_classification_rel;

-- 3. Pre-Boot ORM Metamodel Injection
UPDATE ir_model 
SET model = 'party.classification' 
WHERE model IN ('res.partner.category', 'insilos.partner.category');

UPDATE ir_model_fields 
SET model = 'party.classification' 
WHERE model IN ('res.partner.category', 'insilos.partner.category');

UPDATE ir_model_fields 
SET relation = 'party.classification' 
WHERE relation IN ('res.partner.category', 'insilos.partner.category');

UPDATE ir_ui_view 
SET model = 'party.classification' 
WHERE model IN ('res.partner.category', 'insilos.partner.category');

UPDATE ir_act_window 
SET res_model = 'party.classification' 
WHERE res_model IN ('res.partner.category', 'insilos.partner.category');

UPDATE ir_model_data 
SET model = 'party.classification' 
WHERE model IN ('res.partner.category', 'insilos.partner.category');

COMMIT;
