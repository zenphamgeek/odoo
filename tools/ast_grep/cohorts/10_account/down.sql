-- =============================================================================
-- INSILOS SOVEREIGN HARD FORK — COHORT 10: FINANCIAL ACCOUNTING (ROLLBACK)
-- Target: finance.journal.entry -> account.move      (Table: account_move)
--         finance.journal.line  -> account.move.line (Table: account_move_line)
-- =============================================================================

BEGIN;

-- Drop M2M Compatibility Views
DROP VIEW IF EXISTS account_account_tag_finance_journal_line_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_line_account_account_tag_rel CASCADE;
DROP VIEW IF EXISTS account_auto_reconcile_wizard_finance_journal_line_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_line_account_auto_reconcile_wizard_rel CASCADE;
DROP VIEW IF EXISTS account_automatic_entry_wizard_finance_journal_line_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_line_account_automatic_entry_wizard_rel CASCADE;
DROP VIEW IF EXISTS account_import_summary_finance_journal_entry_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_entry_account_import_summary_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_entry_account_move_send_batch_wizard_rel CASCADE;
DROP VIEW IF EXISTS account_move_send_batch_wizard_finance_journal_entry_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_entry_account_peppol_rejection_wizard_rel CASCADE;
DROP VIEW IF EXISTS account_peppol_rejection_wizard_finance_journal_entry_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_entry_account_resequence_wizard_rel CASCADE;
DROP VIEW IF EXISTS account_resequence_wizard_finance_journal_entry_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_entry_asset_modify_rel CASCADE;
DROP VIEW IF EXISTS asset_modify_finance_journal_entry_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_entry_deferred_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_entry_helpdesk_ticket_rel CASCADE;
DROP VIEW IF EXISTS helpdesk_ticket_finance_journal_entry_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_line_account_payment_rel CASCADE;
DROP VIEW IF EXISTS account_payment_finance_journal_line_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_line_account_reconcile_wizard_rel CASCADE;
DROP VIEW IF EXISTS account_reconcile_wizard_finance_journal_line_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_line_account_tax_rel CASCADE;
DROP VIEW IF EXISTS account_tax_finance_journal_line_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_line_asset_modify_rel CASCADE;
DROP VIEW IF EXISTS asset_modify_finance_journal_line_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_line_l10n_us_1099_wizard_rel CASCADE;
DROP VIEW IF EXISTS l10n_us_1099_wizard_finance_journal_line_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_entry_procurement_order_rel CASCADE;
DROP VIEW IF EXISTS procurement_order_finance_journal_entry_rel CASCADE;
DROP VIEW IF EXISTS finance_journal_entry_validate_finance_journal_entry_rel CASCADE;

-- Drop Compatibility Views
DROP VIEW IF EXISTS account_move CASCADE;
DROP VIEW IF EXISTS account_move_line CASCADE;

-- Rename Back Physical Tables & Sequences
ALTER TABLE finance_journal_entry RENAME TO account_move;
ALTER SEQUENCE IF EXISTS finance_journal_entry_id_seq RENAME TO account_move_id_seq;

ALTER TABLE finance_journal_line RENAME TO account_move_line;
ALTER SEQUENCE IF EXISTS finance_journal_line_id_seq RENAME TO account_move_line_id_seq;

-- Remove Metadata Mirrors
DELETE FROM ir_model WHERE model IN ('finance.journal.entry', 'finance.journal.line');

COMMIT;
