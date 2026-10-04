-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 08: LOGISTICS & INVENTORY (ROLLBACK)
-- Target: logistics.transfer -> stock.picking (Table: stock_picking)
--         logistics.movement -> stock.move    (Table: stock_move)
-- =============================================================================

BEGIN;

-- Drop M2M Compatibility Views
DROP VIEW IF EXISTS account_analytic_line_logistics_movement_rel CASCADE;
DROP VIEW IF EXISTS logistics_movement_account_analytic_line_rel CASCADE;
DROP VIEW IF EXISTS expiry_picking_confirmation_logistics_transfer_rel CASCADE;
DROP VIEW IF EXISTS logistics_transfer_expiry_picking_confirmation_rel CASCADE;
DROP VIEW IF EXISTS helpdesk_ticket_logistics_transfer_rel CASCADE;
DROP VIEW IF EXISTS logistics_transfer_helpdesk_ticket_rel CASCADE;
DROP VIEW IF EXISTS mrp_finished_product_label_layout_logistics_movement_rel CASCADE;
DROP VIEW IF EXISTS logistics_movement_mrp_finished_product_label_layout_rel CASCADE;
DROP VIEW IF EXISTS mrp_mps_forecast_details_logistics_movement_rel CASCADE;
DROP VIEW IF EXISTS logistics_movement_mrp_mps_forecast_details_rel CASCADE;
DROP VIEW IF EXISTS picking_label_type_logistics_transfer_rel CASCADE;
DROP VIEW IF EXISTS logistics_transfer_picking_label_type_rel CASCADE;
DROP VIEW IF EXISTS product_label_layout_logistics_movement_rel CASCADE;
DROP VIEW IF EXISTS logistics_movement_product_label_layout_rel CASCADE;
DROP VIEW IF EXISTS stock_add_to_wave_logistics_transfer_rel CASCADE;
DROP VIEW IF EXISTS logistics_transfer_stock_add_to_wave_rel CASCADE;
DROP VIEW IF EXISTS logistics_movement_created_purchase_line_rel CASCADE;
DROP VIEW IF EXISTS created_purchase_line_logistics_movement_rel CASCADE;
DROP VIEW IF EXISTS logistics_movement_movement_rel CASCADE;
DROP VIEW IF EXISTS logistics_movement_stock_scrap_reason_tag_rel CASCADE;
DROP VIEW IF EXISTS stock_scrap_reason_tag_logistics_movement_rel CASCADE;
DROP VIEW IF EXISTS stock_package_history_logistics_transfer_rel CASCADE;
DROP VIEW IF EXISTS logistics_transfer_stock_package_history_rel CASCADE;
DROP VIEW IF EXISTS logistics_transfer_backorder_rel CASCADE;
DROP VIEW IF EXISTS stock_backorder_confirmation_logistics_transfer_rel CASCADE;
DROP VIEW IF EXISTS logistics_transfer_sms_rel CASCADE;
DROP VIEW IF EXISTS confirm_stock_sms_logistics_transfer_rel CASCADE;
DROP VIEW IF EXISTS logistics_transfer_stock_zero_demand_confirmation_rel CASCADE;
DROP VIEW IF EXISTS stock_zero_demand_confirmation_logistics_transfer_rel CASCADE;
DROP VIEW IF EXISTS template_attribute_value_logistics_movement_rel CASCADE;
DROP VIEW IF EXISTS logistics_movement_template_attribute_value_rel CASCADE;

-- Drop Compatibility Views
DROP VIEW IF EXISTS stock_picking CASCADE;
DROP VIEW IF EXISTS stock_move CASCADE;

-- Rename Back Physical Tables & Sequences
ALTER TABLE logistics_transfer RENAME TO stock_picking;
ALTER SEQUENCE IF EXISTS logistics_transfer_id_seq RENAME TO stock_picking_id_seq;

ALTER TABLE logistics_movement RENAME TO stock_move;
ALTER SEQUENCE IF EXISTS logistics_movement_id_seq RENAME TO stock_move_id_seq;

-- Remove Metadata & Sequence Mirrors
DELETE FROM ir_model WHERE model IN ('logistics.transfer', 'logistics.movement');
DELETE FROM ir_sequence WHERE code = 'logistics.transfer';

COMMIT;
