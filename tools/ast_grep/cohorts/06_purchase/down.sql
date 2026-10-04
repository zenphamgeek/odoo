-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 06: PROCUREMENT & SCM (ROLLBACK)
-- =============================================================================

DO $$
BEGIN
    -- Drop M2M Views
    DROP VIEW IF EXISTS procurement_order_stock_picking_rel CASCADE;
    DROP VIEW IF EXISTS stock_picking_procurement_order_rel CASCADE;
    DROP VIEW IF EXISTS account_tax_procurement_order_line_rel CASCADE;
    DROP VIEW IF EXISTS procurement_order_line_account_tax_rel CASCADE;
    DROP VIEW IF EXISTS account_move_procurement_order_rel CASCADE;
    DROP VIEW IF EXISTS procurement_order_account_move_rel CASCADE;
    DROP VIEW IF EXISTS procurement_order_line_accrual_move_rel CASCADE;
    DROP VIEW IF EXISTS procurement_order_line_product_template_attribute_value_rel CASCADE;
    DROP VIEW IF EXISTS product_template_attribute_value_procurement_order_line_rel CASCADE;
    DROP VIEW IF EXISTS mrp_mps_forecast_details_procurement_order_line_rel CASCADE;
    DROP VIEW IF EXISTS procurement_order_line_mrp_mps_forecast_details_rel CASCADE;

    -- Drop Compatibility Views if they are views
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'purchase_order') THEN
        DROP VIEW purchase_order CASCADE;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'purchase_order_line') THEN
        DROP VIEW purchase_order_line CASCADE;
    END IF;

    -- Revert Physical Table & Sequence Renames if they are tables
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'procurement_order' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE procurement_order RENAME TO purchase_order;
        ALTER SEQUENCE IF EXISTS procurement_order_id_seq RENAME TO purchase_order_id_seq;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'procurement_order_line' AND table_type = 'BASE TABLE') THEN
        ALTER TABLE procurement_order_line RENAME TO purchase_order_line;
        ALTER SEQUENCE IF EXISTS procurement_order_line_id_seq RENAME TO purchase_order_line_id_seq;
    END IF;

    -- Remove Mirrored Model Metadata
    DELETE FROM ir_model WHERE model IN ('procurement.order', 'procurement.order.line');
    DELETE FROM ir_sequence WHERE code = 'procurement.order';
END $$;
