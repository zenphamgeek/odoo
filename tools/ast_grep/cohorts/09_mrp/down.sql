-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 09: MANUFACTURING & MES (ROLLBACK)
-- Target: manufacturing.order -> mrp.production (Table: mrp_production)
--         manufacturing.bom   -> mrp.bom        (Table: mrp_bom)
-- =============================================================================

BEGIN;

-- Drop M2M Compatibility Views
DROP VIEW IF EXISTS account_analytic_account_manufacturing_bom_rel CASCADE;
DROP VIEW IF EXISTS manufacturing_bom_account_analytic_account_rel CASCADE;
DROP VIEW IF EXISTS account_analytic_account_manufacturing_order_rel CASCADE;
DROP VIEW IF EXISTS manufacturing_order_account_analytic_account_rel CASCADE;
DROP VIEW IF EXISTS expiry_picking_confirmation_manufacturing_order_rel CASCADE;
DROP VIEW IF EXISTS manufacturing_order_expiry_picking_confirmation_rel CASCADE;
DROP VIEW IF EXISTS mrp_account_wip_accounting_manufacturing_order_rel CASCADE;
DROP VIEW IF EXISTS manufacturing_order_mrp_account_wip_accounting_rel CASCADE;
DROP VIEW IF EXISTS manufacturing_bom_stock_replenishment_info_rel CASCADE;
DROP VIEW IF EXISTS stock_replenishment_info_manufacturing_bom_rel CASCADE;
DROP VIEW IF EXISTS manufacturing_order_mrp_consumption_warning_rel CASCADE;
DROP VIEW IF EXISTS mrp_consumption_warning_manufacturing_order_rel CASCADE;
DROP VIEW IF EXISTS manufacturing_order_mrp_production_backorder_rel CASCADE;
DROP VIEW IF EXISTS mrp_production_backorder_manufacturing_order_rel CASCADE;
DROP VIEW IF EXISTS manufacturing_order_picking_label_type_rel CASCADE;
DROP VIEW IF EXISTS picking_label_type_manufacturing_order_rel CASCADE;
DROP VIEW IF EXISTS manufacturing_order_stock_lot_rel CASCADE;
DROP VIEW IF EXISTS stock_lot_manufacturing_order_rel CASCADE;
DROP VIEW IF EXISTS manufacturing_order_template_attribute_value_rel CASCADE;
DROP VIEW IF EXISTS template_attribute_value_manufacturing_order_rel CASCADE;

-- Drop Compatibility Views
DROP VIEW IF EXISTS mrp_production CASCADE;
DROP VIEW IF EXISTS mrp_bom CASCADE;

-- Rename Back Physical Tables & Sequences
ALTER TABLE manufacturing_order RENAME TO mrp_production;
ALTER SEQUENCE IF EXISTS manufacturing_order_id_seq RENAME TO mrp_production_id_seq;

ALTER TABLE manufacturing_bom RENAME TO mrp_bom;
ALTER SEQUENCE IF EXISTS manufacturing_bom_id_seq RENAME TO mrp_bom_id_seq;

-- Remove Metadata Mirrors
DELETE FROM ir_model WHERE model IN ('manufacturing.order', 'manufacturing.bom');

COMMIT;
