-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 09: MANUFACTURING & MES
-- Target: mrp.production -> manufacturing.order (Table: manufacturing_order)
--         mrp.bom        -> manufacturing.bom   (Table: manufacturing_bom)
-- Standard: IBM Maximo Manufacturing Assets & Shop Floor Control
-- =============================================================================

BEGIN;

-- Phase 1: Physical Table & Sequence Renames
ALTER TABLE mrp_production RENAME TO manufacturing_order;
ALTER SEQUENCE IF EXISTS mrp_production_id_seq RENAME TO manufacturing_order_id_seq;

ALTER TABLE mrp_bom RENAME TO manufacturing_bom;
ALTER SEQUENCE IF EXISTS mrp_bom_id_seq RENAME TO manufacturing_bom_id_seq;

-- Phase 2: Updatable Backward-Compatibility Views
CREATE OR REPLACE VIEW mrp_production AS
    SELECT * FROM manufacturing_order;

CREATE OR REPLACE VIEW mrp_bom AS
    SELECT * FROM manufacturing_bom;

-- Phase 3: M2M Relation Updatable Views
-- 3.1 account_analytic_account_mrp_bom_rel (account_analytic_account_id, mrp_bom_id)
CREATE OR REPLACE VIEW account_analytic_account_manufacturing_bom_rel AS
    SELECT account_analytic_account_id, mrp_bom_id AS manufacturing_bom_id 
    FROM account_analytic_account_mrp_bom_rel;

CREATE OR REPLACE VIEW manufacturing_bom_account_analytic_account_rel AS
    SELECT mrp_bom_id AS manufacturing_bom_id, account_analytic_account_id 
    FROM account_analytic_account_mrp_bom_rel;

-- 3.2 account_analytic_account_mrp_production_rel (account_analytic_account_id, mrp_production_id)
CREATE OR REPLACE VIEW account_analytic_account_manufacturing_order_rel AS
    SELECT account_analytic_account_id, mrp_production_id AS manufacturing_order_id 
    FROM account_analytic_account_mrp_production_rel;

CREATE OR REPLACE VIEW manufacturing_order_account_analytic_account_rel AS
    SELECT mrp_production_id AS manufacturing_order_id, account_analytic_account_id 
    FROM account_analytic_account_mrp_production_rel;

-- 3.3 expiry_picking_confirmation_mrp_production_rel (expiry_picking_confirmation_id, mrp_production_id)
CREATE OR REPLACE VIEW expiry_picking_confirmation_manufacturing_order_rel AS
    SELECT expiry_picking_confirmation_id, mrp_production_id AS manufacturing_order_id 
    FROM expiry_picking_confirmation_mrp_production_rel;

CREATE OR REPLACE VIEW manufacturing_order_expiry_picking_confirmation_rel AS
    SELECT mrp_production_id AS manufacturing_order_id, expiry_picking_confirmation_id 
    FROM expiry_picking_confirmation_mrp_production_rel;

-- 3.4 mrp_account_wip_accounting_mrp_production_rel (mrp_account_wip_accounting_id, mrp_production_id)
CREATE OR REPLACE VIEW mrp_account_wip_accounting_manufacturing_order_rel AS
    SELECT mrp_account_wip_accounting_id, mrp_production_id AS manufacturing_order_id 
    FROM mrp_account_wip_accounting_mrp_production_rel;

CREATE OR REPLACE VIEW manufacturing_order_mrp_account_wip_accounting_rel AS
    SELECT mrp_production_id AS manufacturing_order_id, mrp_account_wip_accounting_id 
    FROM mrp_account_wip_accounting_mrp_production_rel;

-- 3.5 mrp_bom_stock_replenishment_info_rel (stock_replenishment_info_id, mrp_bom_id)
CREATE OR REPLACE VIEW manufacturing_bom_stock_replenishment_info_rel AS
    SELECT mrp_bom_id AS manufacturing_bom_id, stock_replenishment_info_id 
    FROM mrp_bom_stock_replenishment_info_rel;

CREATE OR REPLACE VIEW stock_replenishment_info_manufacturing_bom_rel AS
    SELECT stock_replenishment_info_id, mrp_bom_id AS manufacturing_bom_id 
    FROM mrp_bom_stock_replenishment_info_rel;

-- 3.6 mrp_consumption_warning_mrp_production_rel (mrp_consumption_warning_id, mrp_production_id)
CREATE OR REPLACE VIEW manufacturing_order_mrp_consumption_warning_rel AS
    SELECT mrp_production_id AS manufacturing_order_id, mrp_consumption_warning_id 
    FROM mrp_consumption_warning_mrp_production_rel;

CREATE OR REPLACE VIEW mrp_consumption_warning_manufacturing_order_rel AS
    SELECT mrp_consumption_warning_id, mrp_production_id AS manufacturing_order_id 
    FROM mrp_consumption_warning_mrp_production_rel;

-- 3.7 mrp_production_mrp_production_backorder_rel (mrp_production_backorder_id, mrp_production_id)
CREATE OR REPLACE VIEW manufacturing_order_mrp_production_backorder_rel AS
    SELECT mrp_production_id AS manufacturing_order_id, mrp_production_backorder_id 
    FROM mrp_production_mrp_production_backorder_rel;

CREATE OR REPLACE VIEW mrp_production_backorder_manufacturing_order_rel AS
    SELECT mrp_production_backorder_id, mrp_production_id AS manufacturing_order_id 
    FROM mrp_production_mrp_production_backorder_rel;

-- 3.8 mrp_production_picking_label_type_rel (picking_label_type_id, mrp_production_id)
CREATE OR REPLACE VIEW manufacturing_order_picking_label_type_rel AS
    SELECT mrp_production_id AS manufacturing_order_id, picking_label_type_id 
    FROM mrp_production_picking_label_type_rel;

CREATE OR REPLACE VIEW picking_label_type_manufacturing_order_rel AS
    SELECT picking_label_type_id, mrp_production_id AS manufacturing_order_id 
    FROM mrp_production_picking_label_type_rel;

-- 3.9 mrp_production_stock_lot_rel (mrp_production_id, stock_lot_id)
CREATE OR REPLACE VIEW manufacturing_order_stock_lot_rel AS
    SELECT mrp_production_id AS manufacturing_order_id, stock_lot_id 
    FROM mrp_production_stock_lot_rel;

CREATE OR REPLACE VIEW stock_lot_manufacturing_order_rel AS
    SELECT stock_lot_id, mrp_production_id AS manufacturing_order_id 
    FROM mrp_production_stock_lot_rel;

-- 3.10 template_attribute_value_mrp_production_rel (production_id, template_attribute_value_id)
CREATE OR REPLACE VIEW manufacturing_order_template_attribute_value_rel AS
    SELECT production_id AS manufacturing_order_id, template_attribute_value_id 
    FROM template_attribute_value_mrp_production_rel;

CREATE OR REPLACE VIEW template_attribute_value_manufacturing_order_rel AS
    SELECT template_attribute_value_id, production_id AS manufacturing_order_id 
    FROM template_attribute_value_mrp_production_rel;

-- Phase 4: Model Metadata Mirroring in ir_model
INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'manufacturing.order', '{"en_US": "Manufacturing Order (IBM MES)"}'::jsonb, 'base', 'Sovereign Manufacturing Order definition for mrp.production', 'priority desc, date_start asc, id'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'manufacturing.order');

INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'manufacturing.bom', '{"en_US": "Bill of Materials"}'::jsonb, 'base', 'Sovereign BOM definition for mrp.bom', 'sequence, id'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'manufacturing.bom');

COMMIT;
