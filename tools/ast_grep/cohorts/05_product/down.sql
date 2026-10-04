-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 05 ROLLBACK SCRIPT
-- =============================================================================

-- Drop M2M Compatibility Views
DROP VIEW IF EXISTS mrp_finished_product_label_layout_catalog_sku_rel CASCADE;
DROP VIEW IF EXISTS product_label_layout_catalog_sku_rel CASCADE;
DROP VIEW IF EXISTS product_fetch_image_wizard_catalog_sku_rel CASCADE;
DROP VIEW IF EXISTS product_pricing_catalog_sku_rel CASCADE;
DROP VIEW IF EXISTS loyalty_rule_catalog_sku_rel CASCADE;
DROP VIEW IF EXISTS loyalty_reward_catalog_sku_rel CASCADE;
DROP VIEW IF EXISTS event_type_ticket_catalog_sku_rel CASCADE;
DROP VIEW IF EXISTS event_event_ticket_catalog_sku_rel CASCADE;
DROP VIEW IF EXISTS product_tag_catalog_sku_rel CASCADE;
DROP VIEW IF EXISTS catalog_sku_product_tag_rel CASCADE;

DROP VIEW IF EXISTS mrp_finished_product_label_layout_catalog_item_rel CASCADE;
DROP VIEW IF EXISTS product_label_layout_catalog_item_rel CASCADE;
DROP VIEW IF EXISTS product_public_category_catalog_item_rel CASCADE;
DROP VIEW IF EXISTS helpdesk_sla_catalog_item_rel CASCADE;
DROP VIEW IF EXISTS account_account_tag_catalog_item_rel CASCADE;
DROP VIEW IF EXISTS pos_category_catalog_item_rel CASCADE;
DROP VIEW IF EXISTS pos_config_catalog_item_rel CASCADE;
DROP VIEW IF EXISTS product_tag_catalog_item_rel CASCADE;
DROP VIEW IF EXISTS catalog_item_product_tag_rel CASCADE;

-- Revert Base Tables & Views idempotently
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_schema = 'public' AND table_name = 'product_product') THEN
        DROP VIEW product_product CASCADE;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'catalog_sku') THEN
        ALTER TABLE catalog_sku RENAME TO product_product;
        ALTER SEQUENCE IF EXISTS catalog_sku_id_seq RENAME TO product_product_id_seq;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_schema = 'public' AND table_name = 'product_template') THEN
        DROP VIEW product_template CASCADE;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'catalog_item') THEN
        ALTER TABLE catalog_item RENAME TO product_template;
        ALTER SEQUENCE IF EXISTS catalog_item_id_seq RENAME TO product_template_id_seq;
    END IF;
END $$;

-- Cleanup Model Metadata
DELETE FROM ir_model WHERE model IN ('catalog.item', 'catalog.sku');
