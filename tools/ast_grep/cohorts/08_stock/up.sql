-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 08: LOGISTICS & INVENTORY
-- Target: stock.picking -> logistics.transfer (Table: logistics_transfer)
--         stock.move    -> logistics.movement (Table: logistics_movement)
-- Standard: IBM Sterling Inventory Visibility & Logistics Integration Platform
-- =============================================================================

BEGIN;

-- Phase 1: Physical Table & Sequence Renames
ALTER TABLE stock_picking RENAME TO logistics_transfer;
ALTER SEQUENCE IF EXISTS stock_picking_id_seq RENAME TO logistics_transfer_id_seq;

ALTER TABLE stock_move RENAME TO logistics_movement;
ALTER SEQUENCE IF EXISTS stock_move_id_seq RENAME TO logistics_movement_id_seq;

-- Phase 2: Updatable Backward-Compatibility Views
CREATE OR REPLACE VIEW stock_picking AS
    SELECT * FROM logistics_transfer;

CREATE OR REPLACE VIEW stock_move AS
    SELECT * FROM logistics_movement;

-- Phase 3: M2M Relation Updatable Views
-- 3.1 account_analytic_line_stock_move_rel (columns: stock_move_id, account_analytic_line_id)
CREATE OR REPLACE VIEW account_analytic_line_logistics_movement_rel AS
    SELECT stock_move_id AS logistics_movement_id, account_analytic_line_id 
    FROM account_analytic_line_stock_move_rel;

CREATE OR REPLACE VIEW logistics_movement_account_analytic_line_rel AS
    SELECT stock_move_id AS logistics_movement_id, account_analytic_line_id 
    FROM account_analytic_line_stock_move_rel;

-- 3.2 expiry_picking_confirmation_stock_picking_rel (columns: expiry_picking_confirmation_id, stock_picking_id)
CREATE OR REPLACE VIEW expiry_picking_confirmation_logistics_transfer_rel AS
    SELECT expiry_picking_confirmation_id, stock_picking_id AS logistics_transfer_id 
    FROM expiry_picking_confirmation_stock_picking_rel;

CREATE OR REPLACE VIEW logistics_transfer_expiry_picking_confirmation_rel AS
    SELECT stock_picking_id AS logistics_transfer_id, expiry_picking_confirmation_id 
    FROM expiry_picking_confirmation_stock_picking_rel;

-- 3.3 helpdesk_ticket_stock_picking_rel (columns: helpdesk_ticket_id, stock_picking_id)
CREATE OR REPLACE VIEW helpdesk_ticket_logistics_transfer_rel AS
    SELECT helpdesk_ticket_id, stock_picking_id AS logistics_transfer_id 
    FROM helpdesk_ticket_stock_picking_rel;

CREATE OR REPLACE VIEW logistics_transfer_helpdesk_ticket_rel AS
    SELECT stock_picking_id AS logistics_transfer_id, helpdesk_ticket_id 
    FROM helpdesk_ticket_stock_picking_rel;

-- 3.4 mrp_finished_product_label_layout_stock_move_rel (columns: mrp_finished_product_label_layout_id, stock_move_id)
CREATE OR REPLACE VIEW mrp_finished_product_label_layout_logistics_movement_rel AS
    SELECT mrp_finished_product_label_layout_id, stock_move_id AS logistics_movement_id 
    FROM mrp_finished_product_label_layout_stock_move_rel;

CREATE OR REPLACE VIEW logistics_movement_mrp_finished_product_label_layout_rel AS
    SELECT stock_move_id AS logistics_movement_id, mrp_finished_product_label_layout_id 
    FROM mrp_finished_product_label_layout_stock_move_rel;

-- 3.5 mrp_mps_forecast_details_stock_move_rel (columns: mrp_mps_forecast_details_id, stock_move_id)
CREATE OR REPLACE VIEW mrp_mps_forecast_details_logistics_movement_rel AS
    SELECT mrp_mps_forecast_details_id, stock_move_id AS logistics_movement_id 
    FROM mrp_mps_forecast_details_stock_move_rel;

CREATE OR REPLACE VIEW logistics_movement_mrp_mps_forecast_details_rel AS
    SELECT stock_move_id AS logistics_movement_id, mrp_mps_forecast_details_id 
    FROM mrp_mps_forecast_details_stock_move_rel;

-- 3.6 picking_label_type_stock_picking_rel (columns: picking_label_type_id, stock_picking_id)
CREATE OR REPLACE VIEW picking_label_type_logistics_transfer_rel AS
    SELECT picking_label_type_id, stock_picking_id AS logistics_transfer_id 
    FROM picking_label_type_stock_picking_rel;

CREATE OR REPLACE VIEW logistics_transfer_picking_label_type_rel AS
    SELECT stock_picking_id AS logistics_transfer_id, picking_label_type_id 
    FROM picking_label_type_stock_picking_rel;

-- 3.7 product_label_layout_stock_move_rel (columns: product_label_layout_id, stock_move_id)
CREATE OR REPLACE VIEW product_label_layout_logistics_movement_rel AS
    SELECT product_label_layout_id, stock_move_id AS logistics_movement_id 
    FROM product_label_layout_stock_move_rel;

CREATE OR REPLACE VIEW logistics_movement_product_label_layout_rel AS
    SELECT stock_move_id AS logistics_movement_id, product_label_layout_id 
    FROM product_label_layout_stock_move_rel;

-- 3.8 stock_add_to_wave_stock_picking_rel (columns: stock_add_to_wave_id, stock_picking_id)
CREATE OR REPLACE VIEW stock_add_to_wave_logistics_transfer_rel AS
    SELECT stock_add_to_wave_id, stock_picking_id AS logistics_transfer_id 
    FROM stock_add_to_wave_stock_picking_rel;

CREATE OR REPLACE VIEW logistics_transfer_stock_add_to_wave_rel AS
    SELECT stock_picking_id AS logistics_transfer_id, stock_add_to_wave_id 
    FROM stock_add_to_wave_stock_picking_rel;

-- 3.9 stock_move_created_purchase_line_rel (columns: created_purchase_line_id, move_id)
CREATE OR REPLACE VIEW logistics_movement_created_purchase_line_rel AS
    SELECT created_purchase_line_id, move_id AS logistics_movement_id 
    FROM stock_move_created_purchase_line_rel;

CREATE OR REPLACE VIEW created_purchase_line_logistics_movement_rel AS
    SELECT move_id AS logistics_movement_id, created_purchase_line_id 
    FROM stock_move_created_purchase_line_rel;

-- 3.10 stock_move_move_rel (columns: move_orig_id, move_dest_id)
CREATE OR REPLACE VIEW logistics_movement_movement_rel AS
    SELECT move_orig_id, move_dest_id 
    FROM stock_move_move_rel;

-- 3.11 stock_move_stock_scrap_reason_tag_rel (columns: stock_move_id, stock_scrap_reason_tag_id)
CREATE OR REPLACE VIEW logistics_movement_stock_scrap_reason_tag_rel AS
    SELECT stock_move_id AS logistics_movement_id, stock_scrap_reason_tag_id 
    FROM stock_move_stock_scrap_reason_tag_rel;

CREATE OR REPLACE VIEW stock_scrap_reason_tag_logistics_movement_rel AS
    SELECT stock_scrap_reason_tag_id, stock_move_id AS logistics_movement_id 
    FROM stock_move_stock_scrap_reason_tag_rel;

-- 3.12 stock_package_history_stock_picking_rel (columns: stock_package_history_id, stock_picking_id)
CREATE OR REPLACE VIEW stock_package_history_logistics_transfer_rel AS
    SELECT stock_package_history_id, stock_picking_id AS logistics_transfer_id 
    FROM stock_package_history_stock_picking_rel;

CREATE OR REPLACE VIEW logistics_transfer_stock_package_history_rel AS
    SELECT stock_picking_id AS logistics_transfer_id, stock_package_history_id 
    FROM stock_package_history_stock_picking_rel;

-- 3.13 stock_picking_backorder_rel (columns: stock_backorder_confirmation_id, stock_picking_id)
CREATE OR REPLACE VIEW logistics_transfer_backorder_rel AS
    SELECT stock_backorder_confirmation_id, stock_picking_id AS logistics_transfer_id 
    FROM stock_picking_backorder_rel;

CREATE OR REPLACE VIEW stock_backorder_confirmation_logistics_transfer_rel AS
    SELECT stock_picking_id AS logistics_transfer_id, stock_backorder_confirmation_id 
    FROM stock_picking_backorder_rel;

-- 3.14 stock_picking_sms_rel (columns: confirm_stock_sms_id, stock_picking_id)
CREATE OR REPLACE VIEW logistics_transfer_sms_rel AS
    SELECT confirm_stock_sms_id, stock_picking_id AS logistics_transfer_id 
    FROM stock_picking_sms_rel;

CREATE OR REPLACE VIEW confirm_stock_sms_logistics_transfer_rel AS
    SELECT stock_picking_id AS logistics_transfer_id, confirm_stock_sms_id 
    FROM stock_picking_sms_rel;

-- 3.15 stock_picking_stock_zero_demand_confirmation_rel (columns: stock_zero_demand_confirmation_id, stock_picking_id)
CREATE OR REPLACE VIEW logistics_transfer_stock_zero_demand_confirmation_rel AS
    SELECT stock_zero_demand_confirmation_id, stock_picking_id AS logistics_transfer_id 
    FROM stock_picking_stock_zero_demand_confirmation_rel;

CREATE OR REPLACE VIEW stock_zero_demand_confirmation_logistics_transfer_rel AS
    SELECT stock_picking_id AS logistics_transfer_id, stock_zero_demand_confirmation_id 
    FROM stock_picking_stock_zero_demand_confirmation_rel;

-- 3.16 template_attribute_value_stock_move_rel (columns: move_id, template_attribute_value_id)
CREATE OR REPLACE VIEW template_attribute_value_logistics_movement_rel AS
    SELECT move_id AS logistics_movement_id, template_attribute_value_id 
    FROM template_attribute_value_stock_move_rel;

CREATE OR REPLACE VIEW logistics_movement_template_attribute_value_rel AS
    SELECT template_attribute_value_id, move_id AS logistics_movement_id 
    FROM template_attribute_value_stock_move_rel;

-- 3.17 purchase_order_stock_picking_rel (logistics_transfer <-> procurement_order)
CREATE OR REPLACE VIEW logistics_transfer_procurement_order_rel AS
    SELECT stock_picking_id AS logistics_transfer_id, purchase_order_id AS procurement_order_id
    FROM purchase_order_stock_picking_rel;

CREATE OR REPLACE VIEW procurement_order_logistics_transfer_rel AS
    SELECT purchase_order_id AS procurement_order_id, stock_picking_id AS logistics_transfer_id
    FROM purchase_order_stock_picking_rel;

-- 3.18 stock_move_created_purchase_line_rel (logistics_movement <-> procurement_order_line)
CREATE OR REPLACE VIEW logistics_movement_procurement_order_line_rel AS
    SELECT move_id AS logistics_movement_id, created_purchase_line_id AS procurement_order_line_id
    FROM stock_move_created_purchase_line_rel;

CREATE OR REPLACE VIEW procurement_order_line_logistics_movement_rel AS
    SELECT created_purchase_line_id AS procurement_order_line_id, move_id AS logistics_movement_id
    FROM stock_move_created_purchase_line_rel;

-- Phase 4: Model Metadata Mirroring in ir_model
INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'logistics.transfer', '{"en_US": "Logistics Transfer (IBM Sterling Inventory)"}'::jsonb, 'base', 'Sovereign Logistics Transfer definition for stock.picking', 'priority desc, scheduled_date asc, id desc'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'logistics.transfer');

INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'logistics.movement', '{"en_US": "Logistics Movement Item"}'::jsonb, 'base', 'Sovereign Logistics Movement definition for stock.move', 'sequence, id'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'logistics.movement');

-- Phase 5: Mirror Sequence for logistics.transfer
INSERT INTO ir_sequence (name, code, implementation, prefix, padding, number_next, number_increment, company_id)
SELECT 'Logistics Transfer', 'logistics.transfer', implementation, prefix, padding, number_next, number_increment, company_id
FROM ir_sequence WHERE code = 'stock.picking'
AND NOT EXISTS (SELECT 1 FROM ir_sequence WHERE code = 'logistics.transfer');

COMMIT;
