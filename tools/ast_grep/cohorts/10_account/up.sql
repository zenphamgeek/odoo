-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 10: FINANCIAL ACCOUNTING
-- Target: account.move      -> finance.journal.entry (Table: finance_journal_entry)
--         account.move.line -> finance.journal.line  (Table: finance_journal_line)
-- Standard: IBM Banking & Financial Markets Data Warehouse (BDW)
-- =============================================================================

BEGIN;

-- Phase 1: Physical Table & Sequence Renames
ALTER TABLE account_move RENAME TO finance_journal_entry;
ALTER SEQUENCE IF EXISTS account_move_id_seq RENAME TO finance_journal_entry_id_seq;

ALTER TABLE account_move_line RENAME TO finance_journal_line;
ALTER SEQUENCE IF EXISTS account_move_line_id_seq RENAME TO finance_journal_line_id_seq;

-- Phase 2: Updatable Backward-Compatibility Views
CREATE OR REPLACE VIEW account_move AS
    SELECT * FROM finance_journal_entry;

CREATE OR REPLACE VIEW account_move_line AS
    SELECT * FROM finance_journal_line;

-- Phase 3: M2M Relation Updatable Views
-- 3.1 account_account_tag_account_move_line_rel (account_move_line_id, account_account_tag_id)
CREATE OR REPLACE VIEW account_account_tag_finance_journal_line_rel AS
    SELECT account_move_line_id AS finance_journal_line_id, account_account_tag_id 
    FROM account_account_tag_account_move_line_rel;

CREATE OR REPLACE VIEW finance_journal_line_account_account_tag_rel AS
    SELECT account_move_line_id AS finance_journal_line_id, account_account_tag_id 
    FROM account_account_tag_account_move_line_rel;

-- 3.2 account_auto_reconcile_wizard_account_move_line_rel (account_auto_reconcile_wizard_id, account_move_line_id)
CREATE OR REPLACE VIEW account_auto_reconcile_wizard_finance_journal_line_rel AS
    SELECT account_auto_reconcile_wizard_id, account_move_line_id AS finance_journal_line_id 
    FROM account_auto_reconcile_wizard_account_move_line_rel;

CREATE OR REPLACE VIEW finance_journal_line_account_auto_reconcile_wizard_rel AS
    SELECT account_move_line_id AS finance_journal_line_id, account_auto_reconcile_wizard_id 
    FROM account_auto_reconcile_wizard_account_move_line_rel;

-- 3.3 account_automatic_entry_wizard_account_move_line_rel (account_automatic_entry_wizard_id, account_move_line_id)
CREATE OR REPLACE VIEW account_automatic_entry_wizard_finance_journal_line_rel AS
    SELECT account_automatic_entry_wizard_id, account_move_line_id AS finance_journal_line_id 
    FROM account_automatic_entry_wizard_account_move_line_rel;

CREATE OR REPLACE VIEW finance_journal_line_account_automatic_entry_wizard_rel AS
    SELECT account_move_line_id AS finance_journal_line_id, account_automatic_entry_wizard_id 
    FROM account_automatic_entry_wizard_account_move_line_rel;

-- 3.4 account_import_summary_account_move_rel (account_import_summary_id, account_move_id)
CREATE OR REPLACE VIEW account_import_summary_finance_journal_entry_rel AS
    SELECT account_import_summary_id, account_move_id AS finance_journal_entry_id 
    FROM account_import_summary_account_move_rel;

CREATE OR REPLACE VIEW finance_journal_entry_account_import_summary_rel AS
    SELECT account_move_id AS finance_journal_entry_id, account_import_summary_id 
    FROM account_import_summary_account_move_rel;

-- 3.5 account_move_account_move_send_batch_wizard_rel (account_move_send_batch_wizard_id, account_move_id)
CREATE OR REPLACE VIEW finance_journal_entry_account_move_send_batch_wizard_rel AS
    SELECT account_move_id AS finance_journal_entry_id, account_move_send_batch_wizard_id 
    FROM account_move_account_move_send_batch_wizard_rel;

CREATE OR REPLACE VIEW account_move_send_batch_wizard_finance_journal_entry_rel AS
    SELECT account_move_send_batch_wizard_id, account_move_id AS finance_journal_entry_id 
    FROM account_move_account_move_send_batch_wizard_rel;

-- 3.6 account_move_account_peppol_rejection_wizard_rel (account_peppol_rejection_wizard_id, account_move_id)
CREATE OR REPLACE VIEW finance_journal_entry_account_peppol_rejection_wizard_rel AS
    SELECT account_move_id AS finance_journal_entry_id, account_peppol_rejection_wizard_id 
    FROM account_move_account_peppol_rejection_wizard_rel;

CREATE OR REPLACE VIEW account_peppol_rejection_wizard_finance_journal_entry_rel AS
    SELECT account_peppol_rejection_wizard_id, account_move_id AS finance_journal_entry_id 
    FROM account_move_account_peppol_rejection_wizard_rel;

-- 3.7 account_move_account_resequence_wizard_rel (account_resequence_wizard_id, account_move_id)
CREATE OR REPLACE VIEW finance_journal_entry_account_resequence_wizard_rel AS
    SELECT account_move_id AS finance_journal_entry_id, account_resequence_wizard_id 
    FROM account_move_account_resequence_wizard_rel;

CREATE OR REPLACE VIEW account_resequence_wizard_finance_journal_entry_rel AS
    SELECT account_resequence_wizard_id, account_move_id AS finance_journal_entry_id 
    FROM account_move_account_resequence_wizard_rel;

-- 3.8 account_move_asset_modify_rel (asset_modify_id, account_move_id)
CREATE OR REPLACE VIEW finance_journal_entry_asset_modify_rel AS
    SELECT account_move_id AS finance_journal_entry_id, asset_modify_id 
    FROM account_move_asset_modify_rel;

CREATE OR REPLACE VIEW asset_modify_finance_journal_entry_rel AS
    SELECT asset_modify_id, account_move_id AS finance_journal_entry_id 
    FROM account_move_asset_modify_rel;

-- 3.9 account_move_deferred_rel (original_move_id, deferred_move_id)
CREATE OR REPLACE VIEW finance_journal_entry_deferred_rel AS
    SELECT original_move_id, deferred_move_id 
    FROM account_move_deferred_rel;

-- 3.10 account_move_helpdesk_ticket_rel (helpdesk_ticket_id, account_move_id)
CREATE OR REPLACE VIEW finance_journal_entry_helpdesk_ticket_rel AS
    SELECT account_move_id AS finance_journal_entry_id, helpdesk_ticket_id 
    FROM account_move_helpdesk_ticket_rel;

CREATE OR REPLACE VIEW helpdesk_ticket_finance_journal_entry_rel AS
    SELECT helpdesk_ticket_id, account_move_id AS finance_journal_entry_id 
    FROM account_move_helpdesk_ticket_rel;

-- 3.11 account_move_line_account_payment_rel (account_move_line_id, account_payment_id)
CREATE OR REPLACE VIEW finance_journal_line_account_payment_rel AS
    SELECT account_move_line_id AS finance_journal_line_id, account_payment_id 
    FROM account_move_line_account_payment_rel;

CREATE OR REPLACE VIEW account_payment_finance_journal_line_rel AS
    SELECT account_payment_id, account_move_line_id AS finance_journal_line_id 
    FROM account_move_line_account_payment_rel;

-- 3.12 account_move_line_account_reconcile_wizard_rel (account_reconcile_wizard_id, account_move_line_id)
CREATE OR REPLACE VIEW finance_journal_line_account_reconcile_wizard_rel AS
    SELECT account_move_line_id AS finance_journal_line_id, account_reconcile_wizard_id 
    FROM account_move_line_account_reconcile_wizard_rel;

CREATE OR REPLACE VIEW account_reconcile_wizard_finance_journal_line_rel AS
    SELECT account_reconcile_wizard_id, account_move_line_id AS finance_journal_line_id 
    FROM account_move_line_account_reconcile_wizard_rel;

-- 3.13 account_move_line_account_tax_rel (account_tax_id, account_move_line_id)
CREATE OR REPLACE VIEW finance_journal_line_account_tax_rel AS
    SELECT account_move_line_id AS finance_journal_line_id, account_tax_id 
    FROM account_move_line_account_tax_rel;

CREATE OR REPLACE VIEW account_tax_finance_journal_line_rel AS
    SELECT account_tax_id, account_move_line_id AS finance_journal_line_id 
    FROM account_move_line_account_tax_rel;

-- 3.14 account_move_line_asset_modify_rel (asset_modify_id, account_move_line_id)
CREATE OR REPLACE VIEW finance_journal_line_asset_modify_rel AS
    SELECT account_move_line_id AS finance_journal_line_id, asset_modify_id 
    FROM account_move_line_asset_modify_rel;

CREATE OR REPLACE VIEW asset_modify_finance_journal_line_rel AS
    SELECT asset_modify_id, account_move_line_id AS finance_journal_line_id 
    FROM account_move_line_asset_modify_rel;

-- 3.15 account_move_line_l10n_us_1099_wizard_rel (l10n_us_1099_wizard_id, account_move_line_id)
CREATE OR REPLACE VIEW finance_journal_line_l10n_us_1099_wizard_rel AS
    SELECT account_move_line_id AS finance_journal_line_id, l10n_us_1099_wizard_id 
    FROM account_move_line_l10n_us_1099_wizard_rel;

CREATE OR REPLACE VIEW l10n_us_1099_wizard_finance_journal_line_rel AS
    SELECT l10n_us_1099_wizard_id, account_move_line_id AS finance_journal_line_id 
    FROM account_move_line_l10n_us_1099_wizard_rel;

-- 3.16 account_move_procurement_order_rel (procurement_order_id, account_move_id)
CREATE OR REPLACE VIEW finance_journal_entry_procurement_order_rel AS
    SELECT account_move_id AS finance_journal_entry_id, procurement_order_id 
    FROM account_move_procurement_order_rel;

CREATE OR REPLACE VIEW procurement_order_finance_journal_entry_rel AS
    SELECT procurement_order_id, account_move_id AS finance_journal_entry_id 
    FROM account_move_procurement_order_rel;

-- 3.17 account_move_validate_account_move_rel (validate_account_move_id, account_move_id)
CREATE OR REPLACE VIEW finance_journal_entry_validate_finance_journal_entry_rel AS
    SELECT account_move_id AS finance_journal_entry_id, validate_account_move_id 
    FROM account_move_validate_account_move_rel;

-- Phase 4: Model Metadata Mirroring in ir_model
INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'finance.journal.entry', '{"en_US": "Journal Entry (IBM BDW)"}'::jsonb, 'base', 'Sovereign Journal Entry definition for account.move', 'date desc, name desc, invoice_date desc, id desc'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'finance.journal.entry');

INSERT INTO ir_model (model, name, state, info, "order")
SELECT 'finance.journal.line', '{"en_US": "Journal Item (IBM BDW)"}'::jsonb, 'base', 'Sovereign Journal Line definition for account.move.line', 'date desc, move_name desc, id'
WHERE NOT EXISTS (SELECT 1 FROM ir_model WHERE model = 'finance.journal.line');

COMMIT;
