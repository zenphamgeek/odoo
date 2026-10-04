-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 4: res.partner -> party.master
-- IBM Enterprise Data Architecture Standard (Party Master / Involved Party)
-- Phase 1 (The Bridge): Physical Table Rename + Updatable View Facade
-- Phase 2 (Metadata Injection): Pre-Boot ORM Metamodel Synchronization
-- =============================================================================

BEGIN;

-- 1. Physical Table & Sequence Rename to IBM Canonical party_master
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'res_partner' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE res_partner RENAME TO party_master;
        ALTER SEQUENCE res_partner_id_seq RENAME TO party_master_id_seq;
        ALTER TABLE party_master ALTER COLUMN id SET DEFAULT nextval('party_master_id_seq'::regclass);
    END IF;
END $$;

-- 2. Updatable Compatibility View Facade (Zero-Downtime Bridge)
-- In PostgreSQL 9.3+, simple views are automatically updatable.
-- INSERT, UPDATE, and DELETE pass through directly to underlying tables.
CREATE OR REPLACE VIEW res_partner AS 
    SELECT * FROM party_master;

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
        WHERE table_name LIKE '%res_partner%rel%' AND table_type = 'BASE TABLE'
    LOOP
        v_new_table := replace(r.table_name, 'res_partner', 'party_master');
        SELECT column_name INTO v_col1 FROM information_schema.columns WHERE table_name = r.table_name ORDER BY ordinal_position LIMIT 1;
        SELECT column_name INTO v_col2 FROM information_schema.columns WHERE table_name = r.table_name ORDER BY ordinal_position OFFSET 1 LIMIT 1;
        
        IF v_col1 = 'res_partner_id' THEN
            EXECUTE format('CREATE OR REPLACE VIEW %I AS SELECT res_partner_id AS party_master_id, %I FROM %I', v_new_table, v_col2, r.table_name);
        ELSIF v_col2 = 'res_partner_id' THEN
            EXECUTE format('CREATE OR REPLACE VIEW %I AS SELECT %I, res_partner_id AS party_master_id FROM %I', v_new_table, v_col1, r.table_name);
        ELSIF v_col1 = 'partner_id' THEN
            EXECUTE format('CREATE OR REPLACE VIEW %I AS SELECT partner_id AS party_master_id, %I FROM %I', v_new_table, v_col2, r.table_name);
        ELSIF v_col2 = 'partner_id' THEN
            EXECUTE format('CREATE OR REPLACE VIEW %I AS SELECT %I, partner_id AS party_master_id FROM %I', v_new_table, v_col1, r.table_name);
        ELSE
            EXECUTE format('CREATE OR REPLACE VIEW %I AS SELECT * FROM %I', v_new_table, r.table_name);
        END IF;
    END LOOP;
END $$;

-- 3. Pre-Boot ORM Metamodel Injection
UPDATE ir_model 
SET model = 'party.master' 
WHERE model = 'res.partner';

UPDATE ir_model_fields 
SET model = 'party.master' 
WHERE model = 'res.partner';

UPDATE ir_model_fields 
SET relation = 'party.master' 
WHERE relation = 'res.partner';

UPDATE ir_ui_view 
SET model = 'party.master' 
WHERE model = 'res.partner';

UPDATE ir_act_window 
SET res_model = 'party.master' 
WHERE res_model = 'res.partner';

UPDATE ir_model_data 
SET model = 'party.master' 
WHERE model = 'res.partner';

COMMIT;
