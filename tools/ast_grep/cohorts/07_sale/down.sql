-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 07: SALES & ORDERS (ROLLBACK)
-- =============================================================================

DO $$
BEGIN
    -- Drop M2M Views
    DROP VIEW IF EXISTS account_tax_order_line_rel CASCADE;
    DROP VIEW IF EXISTS order_line_account_tax_rel CASCADE;
    DROP VIEW IF EXISTS invoice_line_order_line_rel CASCADE;
    DROP VIEW IF EXISTS order_line_invoice_rel CASCADE;
    DROP VIEW IF EXISTS order_line_accrual_move_rel CASCADE;
    DROP VIEW IF EXISTS order_line_product_template_attribute_value_rel CASCADE;
    DROP VIEW IF EXISTS product_template_attribute_value_order_line_rel CASCADE;
    DROP VIEW IF EXISTS order_line_stock_route_rel CASCADE;
    DROP VIEW IF EXISTS stock_route_order_line_rel CASCADE;
    DROP VIEW IF EXISTS order_line_product_document_rel CASCADE;
    DROP VIEW IF EXISTS order_header_transaction_rel CASCADE;
    DROP VIEW IF EXISTS transaction_order_header_rel CASCADE;
    DROP VIEW IF EXISTS order_header_tag_rel CASCADE;
    DROP VIEW IF EXISTS tag_order_header_rel CASCADE;
    DROP VIEW IF EXISTS order_header_starred_user_rel CASCADE;
    DROP VIEW IF EXISTS res_users_order_header_rel CASCADE;
    DROP VIEW IF EXISTS loyalty_card_order_header_rel CASCADE;
    DROP VIEW IF EXISTS order_header_loyalty_card_rel CASCADE;
    DROP VIEW IF EXISTS loyalty_rule_order_header_rel CASCADE;
    DROP VIEW IF EXISTS order_header_loyalty_rule_rel CASCADE;
    DROP VIEW IF EXISTS order_header_quotation_document_rel CASCADE;
    DROP VIEW IF EXISTS quotation_document_order_header_rel CASCADE;
    DROP VIEW IF EXISTS order_header_sale_advance_payment_inv_rel CASCADE;
    DROP VIEW IF EXISTS sale_advance_payment_inv_order_header_rel CASCADE;
    DROP VIEW IF EXISTS order_header_sale_mass_cancel_orders_rel CASCADE;
    DROP VIEW IF EXISTS order_header_disabled_auto_rewards_rel CASCADE;

    -- Drop Compatibility Views if they are views
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'sale_order') THEN
        DROP VIEW sale_order CASCADE;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'sale_order_line') THEN
        DROP VIEW sale_order_line CASCADE;
    END IF;

    -- Revert Physical Table & Sequence Renames if they are tables
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'order_header' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE order_header RENAME TO sale_order;
        ALTER SEQUENCE IF EXISTS order_header_id_seq RENAME TO sale_order_id_seq;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'order_line' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE order_line RENAME TO sale_order_line;
        ALTER SEQUENCE IF EXISTS order_line_id_seq RENAME TO sale_order_line_id_seq;
    END IF;

    -- Remove Mirrored Model Metadata
    DELETE FROM ir_model WHERE model IN ('order.header', 'order.line');
    DELETE FROM ir_sequence WHERE code = 'order.header';
END $$;
