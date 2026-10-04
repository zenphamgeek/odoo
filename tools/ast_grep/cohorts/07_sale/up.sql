-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 07: SALES & ORDERS
-- Target: sale.order      -> order.header (Table: order_header)
--         sale.order.line -> order.line   (Table: order_line)
-- Standard: IBM Sterling Order Management System (OMS)
-- =============================================================================

BEGIN;

-- Phase 1: Physical Table & Sequence Renames
ALTER TABLE sale_order RENAME TO order_header;
ALTER SEQUENCE IF EXISTS sale_order_id_seq RENAME TO order_header_id_seq;

ALTER TABLE sale_order_line RENAME TO order_line;
ALTER SEQUENCE IF EXISTS sale_order_line_id_seq RENAME TO order_line_id_seq;

-- Phase 2: Updatable Backward-Compatibility Views
CREATE OR REPLACE VIEW sale_order AS
    SELECT * FROM order_header;

CREATE OR REPLACE VIEW sale_order_line AS
    SELECT * FROM order_line;

-- Phase 3: M2M Relation Updatable Views
-- 3.1 account_tax_sale_order_line_rel (columns: sale_order_line_id, account_tax_id)
CREATE OR REPLACE VIEW account_tax_order_line_rel AS
    SELECT sale_order_line_id AS order_line_id, account_tax_id 
    FROM account_tax_sale_order_line_rel;

CREATE OR REPLACE VIEW order_line_account_tax_rel AS
    SELECT sale_order_line_id AS order_line_id, account_tax_id 
    FROM account_tax_sale_order_line_rel;

-- 3.2 sale_order_line_invoice_rel (columns: invoice_line_id, order_line_id)
CREATE OR REPLACE VIEW invoice_line_order_line_rel AS
    SELECT invoice_line_id, order_line_id 
    FROM sale_order_line_invoice_rel;

CREATE OR REPLACE VIEW order_line_invoice_rel AS
    SELECT order_line_id, invoice_line_id 
    FROM sale_order_line_invoice_rel;

-- 3.3 sale_order_line_accrual_move_rel (columns: order_line_id, move_id)
CREATE OR REPLACE VIEW order_line_accrual_move_rel AS
    SELECT order_line_id, move_id 
    FROM sale_order_line_accrual_move_rel;

-- 3.4 product_template_attribute_value_sale_order_line_rel (columns: sale_order_line_id, product_template_attribute_value_id)
CREATE OR REPLACE VIEW order_line_product_template_attribute_value_rel AS
    SELECT sale_order_line_id AS order_line_id, product_template_attribute_value_id 
    FROM product_template_attribute_value_sale_order_line_rel;

CREATE OR REPLACE VIEW product_template_attribute_value_order_line_rel AS
    SELECT product_template_attribute_value_id, sale_order_line_id AS order_line_id 
    FROM product_template_attribute_value_sale_order_line_rel;

-- 3.5 sale_order_line_stock_route_rel (columns: sale_order_line_id, stock_route_id)
CREATE OR REPLACE VIEW order_line_stock_route_rel AS
    SELECT sale_order_line_id AS order_line_id, stock_route_id 
    FROM sale_order_line_stock_route_rel;

CREATE OR REPLACE VIEW stock_route_order_line_rel AS
    SELECT stock_route_id, sale_order_line_id AS order_line_id 
    FROM sale_order_line_stock_route_rel;

-- 3.6 sale_order_line_product_document_rel (columns: sale_order_line_id, product_document_id)
CREATE OR REPLACE VIEW order_line_product_document_rel AS
    SELECT sale_order_line_id AS order_line_id, product_document_id 
    FROM sale_order_line_product_document_rel;

-- 3.7 sale_order_transaction_rel (columns: transaction_id, sale_order_id)
CREATE OR REPLACE VIEW order_header_transaction_rel AS
    SELECT sale_order_id AS order_header_id, transaction_id 
    FROM sale_order_transaction_rel;

CREATE OR REPLACE VIEW transaction_order_header_rel AS
    SELECT transaction_id, sale_order_id AS order_header_id 
    FROM sale_order_transaction_rel;

-- 3.8 sale_order_tag_rel (columns: order_id, tag_id)
CREATE OR REPLACE VIEW order_header_tag_rel AS
    SELECT order_id AS order_header_id, tag_id 
    FROM sale_order_tag_rel;

CREATE OR REPLACE VIEW tag_order_header_rel AS
    SELECT tag_id, order_id AS order_header_id 
    FROM sale_order_tag_rel;

-- 3.9 sale_order_starred_user_rel (columns: order_id, user_id)
CREATE OR REPLACE VIEW order_header_starred_user_rel AS
    SELECT order_id AS order_header_id, user_id 
    FROM sale_order_starred_user_rel;

CREATE OR REPLACE VIEW res_users_order_header_rel AS
    SELECT user_id, order_id AS order_header_id 
    FROM sale_order_starred_user_rel;

-- 3.10 loyalty_card_sale_order_rel (columns: sale_order_id, loyalty_card_id)
CREATE OR REPLACE VIEW loyalty_card_order_header_rel AS
    SELECT loyalty_card_id, sale_order_id AS order_header_id 
    FROM loyalty_card_sale_order_rel;

CREATE OR REPLACE VIEW order_header_loyalty_card_rel AS
    SELECT sale_order_id AS order_header_id, loyalty_card_id 
    FROM loyalty_card_sale_order_rel;

-- 3.11 loyalty_rule_sale_order_rel (columns: sale_order_id, loyalty_rule_id)
CREATE OR REPLACE VIEW loyalty_rule_order_header_rel AS
    SELECT loyalty_rule_id, sale_order_id AS order_header_id 
    FROM loyalty_rule_sale_order_rel;

CREATE OR REPLACE VIEW order_header_loyalty_rule_rel AS
    SELECT sale_order_id AS order_header_id, loyalty_rule_id 
    FROM loyalty_rule_sale_order_rel;

-- 3.12 quotation_document_sale_order_rel (columns: sale_order_id, quotation_document_id)
CREATE OR REPLACE VIEW order_header_quotation_document_rel AS
    SELECT sale_order_id AS order_header_id, quotation_document_id 
    FROM quotation_document_sale_order_rel;

CREATE OR REPLACE VIEW quotation_document_order_header_rel AS
    SELECT quotation_document_id, sale_order_id AS order_header_id 
    FROM quotation_document_sale_order_rel;

-- 3.13 sale_advance_payment_inv_sale_order_rel (columns: sale_advance_payment_inv_id, sale_order_id)
CREATE OR REPLACE VIEW order_header_sale_advance_payment_inv_rel AS
    SELECT sale_order_id AS order_header_id, sale_advance_payment_inv_id 
    FROM sale_advance_payment_inv_sale_order_rel;

CREATE OR REPLACE VIEW sale_advance_payment_inv_order_header_rel AS
    SELECT sale_advance_payment_inv_id, sale_order_id AS order_header_id 
    FROM sale_advance_payment_inv_sale_order_rel;

-- 3.14 sale_order_mass_cancel_wizard_rel (columns: sale_mass_cancel_orders_id, sale_order_id)
CREATE OR REPLACE VIEW order_header_sale_mass_cancel_orders_rel AS
    SELECT sale_order_id AS order_header_id, sale_mass_cancel_orders_id 
    FROM sale_order_mass_cancel_wizard_rel;

-- 3.15 sale_order_disabled_auto_rewards_rel (columns: sale_order_id, loyalty_reward_id)
CREATE OR REPLACE VIEW order_header_disabled_auto_rewards_rel AS
    SELECT sale_order_id AS order_header_id, loyalty_reward_id 
    FROM sale_order_disabled_auto_rewards_rel;

-- Phase 4: Model Metadata Mirroring in ir_model
INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'order.header', '{"en_US": "Order Header (IBM Sterling OMS)"}'::jsonb, 'base', 'Sovereign Order Header definition for sale.order', 'date_order desc, id desc'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'order.header');

INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'order.line', '{"en_US": "Order Line Item"}'::jsonb, 'base', 'Sovereign Order Line definition for sale.order.line', 'order_id, sequence, id'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'order.line');

-- Phase 5: Mirror Sequence for order.header
INSERT INTO ir_sequence (name, code, implementation, prefix, padding, number_next, number_increment, company_id)
SELECT 'Order Header', 'order.header', implementation, prefix, padding, number_next, number_increment, company_id
FROM ir_sequence WHERE code = 'sale.order'
AND NOT EXISTS (SELECT 1 FROM ir_sequence WHERE code = 'order.header');

COMMIT;
