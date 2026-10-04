-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 05: CATALOG & MATERIALS
-- Target: product.template -> catalog.item (Table: catalog_item)
--         product.product  -> catalog.sku  (Table: catalog_sku)
-- Standard: IBM Maximo Item Master & IBM Sterling PIM
-- =============================================================================

-- Phase 1: Physical Table & Sequence Renames
ALTER TABLE product_template RENAME TO catalog_item;
ALTER SEQUENCE IF EXISTS product_template_id_seq RENAME TO catalog_item_id_seq;

ALTER TABLE product_product RENAME TO catalog_sku;
ALTER SEQUENCE IF EXISTS product_product_id_seq RENAME TO catalog_sku_id_seq;

-- Phase 2: Updatable Backward-Compatibility Views
CREATE OR REPLACE VIEW product_template AS
    SELECT * FROM catalog_item;

CREATE OR REPLACE VIEW product_product AS
    SELECT * FROM catalog_sku;

-- Phase 3: M2M Relation Updatable Views
-- For catalog_item M2M relations:
CREATE OR REPLACE VIEW catalog_item_pos_category_rel AS
    SELECT product_template_id AS catalog_item_id, pos_category_id FROM pos_category_product_template_rel;

CREATE OR REPLACE VIEW pos_category_catalog_item_rel AS
    SELECT pos_category_id, product_template_id AS catalog_item_id FROM pos_category_product_template_rel;

CREATE OR REPLACE VIEW catalog_item_product_combo_rel AS
    SELECT product_template_id AS catalog_item_id, product_combo_id FROM product_combo_product_template_rel;

CREATE OR REPLACE VIEW catalog_item_uom_uom_rel AS
    SELECT product_template_id AS catalog_item_id, uom_uom_id FROM product_template_uom_uom_rel;

CREATE OR REPLACE VIEW catalog_item_pos_config_rel AS
    SELECT product_template_id AS catalog_item_id, pos_config_id FROM pos_config_product_template_rel;

CREATE OR REPLACE VIEW pos_config_catalog_item_rel AS
    SELECT pos_config_id, product_template_id AS catalog_item_id FROM pos_config_product_template_rel;

CREATE OR REPLACE VIEW catalog_item_pos_delivery_provider_rel AS
    SELECT product_template_id AS catalog_item_id, pos_delivery_provider_id FROM pos_delivery_provider_product_template_rel;

CREATE OR REPLACE VIEW account_account_tag_catalog_item_rel AS
    SELECT account_account_tag_id, product_template_id AS catalog_item_id FROM account_account_tag_product_template_rel;

CREATE OR REPLACE VIEW catalog_item_product_tag_rel AS
    SELECT product_template_id AS catalog_item_id, product_tag_id FROM product_tag_product_template_rel;

CREATE OR REPLACE VIEW product_tag_catalog_item_rel AS
    SELECT product_template_id AS catalog_item_id, product_tag_id FROM product_tag_product_template_rel;

CREATE OR REPLACE VIEW helpdesk_sla_catalog_item_rel AS
    SELECT helpdesk_sla_id, product_template_id AS catalog_item_id FROM helpdesk_sla_product_template_rel;

CREATE OR REPLACE VIEW product_public_category_catalog_item_rel AS
    SELECT product_public_category_id, product_template_id AS catalog_item_id FROM product_public_category_product_template_rel;

CREATE OR REPLACE VIEW product_label_layout_catalog_item_rel AS
    SELECT product_label_layout_id, product_template_id AS catalog_item_id FROM product_label_layout_product_template_rel;

CREATE OR REPLACE VIEW mrp_finished_product_label_layout_catalog_item_rel AS
    SELECT mrp_finished_product_label_layout_id, product_template_id AS catalog_item_id FROM mrp_finished_product_label_layout_product_template_rel;

-- For catalog_sku M2M relations:
CREATE OR REPLACE VIEW catalog_sku_uom_uom_rel AS
    SELECT product_product_id AS catalog_sku_id, uom_uom_id FROM product_product_uom_uom_rel;

CREATE OR REPLACE VIEW catalog_sku_product_tag_rel AS
    SELECT product_product_id AS catalog_sku_id, product_tag_id FROM product_tag_product_product_rel;

CREATE OR REPLACE VIEW product_tag_catalog_sku_rel AS
    SELECT product_product_id AS catalog_sku_id, product_tag_id FROM product_tag_product_product_rel;

CREATE OR REPLACE VIEW event_event_ticket_catalog_sku_rel AS
    SELECT event_event_ticket_id, product_product_id AS catalog_sku_id FROM event_event_ticket_product_product_rel;

CREATE OR REPLACE VIEW event_type_ticket_catalog_sku_rel AS
    SELECT event_type_ticket_id, product_product_id AS catalog_sku_id FROM event_type_ticket_product_product_rel;

CREATE OR REPLACE VIEW loyalty_reward_catalog_sku_rel AS
    SELECT loyalty_reward_id, product_product_id AS catalog_sku_id FROM loyalty_reward_product_product_rel;

CREATE OR REPLACE VIEW loyalty_rule_catalog_sku_rel AS
    SELECT loyalty_rule_id, product_product_id AS catalog_sku_id FROM loyalty_rule_product_product_rel;

CREATE OR REPLACE VIEW product_pricing_catalog_sku_rel AS
    SELECT product_pricing_id, product_product_id AS catalog_sku_id FROM product_pricing_product_product_rel;

CREATE OR REPLACE VIEW product_fetch_image_wizard_catalog_sku_rel AS
    SELECT product_fetch_image_wizard_id, product_product_id AS catalog_sku_id FROM product_fetch_image_wizard_product_product_rel;

CREATE OR REPLACE VIEW product_label_layout_catalog_sku_rel AS
    SELECT product_label_layout_id, product_product_id AS catalog_sku_id FROM product_label_layout_product_product_rel;

CREATE OR REPLACE VIEW mrp_finished_product_label_layout_catalog_sku_rel AS
    SELECT mrp_finished_product_label_layout_id, product_product_id AS catalog_sku_id FROM mrp_finished_product_label_layout_product_product_rel;

-- Phase 4: Model Metadata Mirroring in ir_model
INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'catalog.item', '{"en_US": "Catalog Item (IBM Maximo Item Master)"}'::jsonb, 'base', 'Sovereign Catalog Item definition for product.template', 'is_favorite desc, name'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'catalog.item');

INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'catalog.sku', '{"en_US": "Catalog SKU (Stock Keeping Unit)"}'::jsonb, 'base', 'Sovereign Catalog SKU definition for product.product', 'default_code, name, id'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'catalog.sku');
