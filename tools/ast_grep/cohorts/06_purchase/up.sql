-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 06: PROCUREMENT & SCM
-- Target: purchase.order      -> procurement.order      (Table: procurement_order)
--         purchase.order.line -> procurement.order.line (Table: procurement_order_line)
-- Standard: IBM Sterling SCM & IBM Maximo Purchasing Module
-- =============================================================================

BEGIN;

-- Phase 1: Physical Table & Sequence Renames
ALTER TABLE purchase_order RENAME TO procurement_order;
ALTER SEQUENCE IF EXISTS purchase_order_id_seq RENAME TO procurement_order_id_seq;

ALTER TABLE purchase_order_line RENAME TO procurement_order_line;
ALTER SEQUENCE IF EXISTS purchase_order_line_id_seq RENAME TO procurement_order_line_id_seq;

-- Phase 2: Updatable Backward-Compatibility Views
CREATE OR REPLACE VIEW purchase_order AS
    SELECT * FROM procurement_order;

CREATE OR REPLACE VIEW purchase_order_line AS
    SELECT * FROM procurement_order_line;

-- Phase 3: M2M Relation Updatable Views
-- 3.1 purchase_order_stock_picking_rel (columns: purchase_order_id, stock_picking_id)
CREATE OR REPLACE VIEW procurement_order_stock_picking_rel AS
    SELECT purchase_order_id AS procurement_order_id, stock_picking_id 
    FROM purchase_order_stock_picking_rel;

CREATE OR REPLACE VIEW stock_picking_procurement_order_rel AS
    SELECT stock_picking_id, purchase_order_id AS procurement_order_id 
    FROM purchase_order_stock_picking_rel;

-- 3.2 account_tax_purchase_order_line_rel (columns: account_tax_id, purchase_order_line_id)
CREATE OR REPLACE VIEW account_tax_procurement_order_line_rel AS
    SELECT account_tax_id, purchase_order_line_id AS procurement_order_line_id 
    FROM account_tax_purchase_order_line_rel;

CREATE OR REPLACE VIEW procurement_order_line_account_tax_rel AS
    SELECT purchase_order_line_id AS procurement_order_line_id, account_tax_id 
    FROM account_tax_purchase_order_line_rel;

-- 3.3 account_move_purchase_order_rel (columns: purchase_order_id, account_move_id)
CREATE OR REPLACE VIEW account_move_procurement_order_rel AS
    SELECT purchase_order_id AS procurement_order_id, account_move_id 
    FROM account_move_purchase_order_rel;

CREATE OR REPLACE VIEW procurement_order_account_move_rel AS
    SELECT purchase_order_id AS procurement_order_id, account_move_id 
    FROM account_move_purchase_order_rel;

-- 3.4 purchase_order_line_accrual_move_rel (columns: order_line_id, move_id)
CREATE OR REPLACE VIEW procurement_order_line_accrual_move_rel AS
    SELECT order_line_id, move_id 
    FROM purchase_order_line_accrual_move_rel;

-- 3.5 product_template_attribute_value_purchase_order_line_rel
CREATE OR REPLACE VIEW procurement_order_line_product_template_attribute_value_rel AS
    SELECT purchase_order_line_id AS procurement_order_line_id, product_template_attribute_value_id 
    FROM product_template_attribute_value_purchase_order_line_rel;

CREATE OR REPLACE VIEW product_template_attribute_value_procurement_order_line_rel AS
    SELECT product_template_attribute_value_id, purchase_order_line_id AS procurement_order_line_id 
    FROM product_template_attribute_value_purchase_order_line_rel;

-- 3.6 mrp_mps_forecast_details_purchase_order_line_rel
CREATE OR REPLACE VIEW mrp_mps_forecast_details_procurement_order_line_rel AS
    SELECT mrp_mps_forecast_details_id, purchase_order_line_id AS procurement_order_line_id 
    FROM mrp_mps_forecast_details_purchase_order_line_rel;

CREATE OR REPLACE VIEW procurement_order_line_mrp_mps_forecast_details_rel AS
    SELECT purchase_order_line_id AS procurement_order_line_id, mrp_mps_forecast_details_id 
    FROM mrp_mps_forecast_details_purchase_order_line_rel;

-- Phase 4: Model Metadata Mirroring in ir_model
INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'procurement.order', '{"en_US": "Procurement Order (IBM Sterling SCM)"}'::jsonb, 'base', 'Sovereign Procurement Order definition for purchase.order', 'priority desc, id desc'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'procurement.order');

INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'procurement.order.line', '{"en_US": "Procurement Order Line Item"}'::jsonb, 'base', 'Sovereign Procurement Order Line definition for purchase.order.line', 'order_id, sequence, id'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'procurement.order.line');

-- Phase 5: Mirror Sequence for procurement.order
INSERT INTO ir_sequence (name, code, implementation, prefix, padding, number_next, number_increment, company_id)
SELECT 'Procurement Order', 'procurement.order', implementation, prefix, padding, number_next, number_increment, company_id
FROM ir_sequence WHERE code = 'purchase.order'
AND NOT EXISTS (SELECT 1 FROM ir_sequence WHERE code = 'procurement.order');

COMMIT;
