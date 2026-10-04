# Sovereign Hard Fork Architecture: No-Forbidden-Zone PDCA

**Author**: lthn.Ariana (Chief Enterprise Architect)
**Status**: Calibrated & Hardened
**Target**: Insilos Enterprise Platform v20.0 (Odoo Core)

## 1. Adversarial Critique & Pitfall Analysis

Renaming core physical tables (e.g., `res_partner` -> `insilos_partner`) and models while relying on PostgreSQL Updatable Views and AST-Grep introduces several critical failure modes:

### a) PostgreSQL Sequences and Default Values
- **The Trap**: `SERIAL` columns create implicit sequences (`res_partner_id_seq`). Renaming the table does **not** automatically rename the sequence.
- **The Failure**: If the sequence is renamed but the column's `DEFAULT` expression isn't updated, inserts via the new table name will crash. Conversely, if Odoo ORM explicitly queries `nextval('res_partner_id_seq')` (which it sometimes does for fast bulk inserts), it will throw a `Relation not found` error.
- **The Fix**: The sequence must be explicitly renamed, and the `DEFAULT` constraint on the new table explicitly rebound.

### b) Foreign Key Constraints (Odoo's `-u` Schema Upgrader)
- **The Trap**: PostgreSQL manages FKs by OID, meaning a rename doesn't break DB-level integrity.
- **The Failure**: Odoo's registry initialization (`odoo/schema.py`) queries `pg_constraint` by *name* (e.g., `res_users_partner_id_fkey`). If Odoo starts up and expects `insilos_users_partner_id_fkey` but finds the old name, it will attempt a `DROP CONSTRAINT` and `ADD CONSTRAINT`. On a multi-million row table, this triggers a heavy `ACCESS EXCLUSIVE` lock, taking down production.
- **The Fix**: Raw DDL must rename all related constraints and indexes to match Odoo's deterministic naming algorithm.

### c) ORM System Metadata (The True Forbidden Zone)
- **The Trap**: Changing `_name = 'insilos.partner'` in Python without prepping the database.
- **The Failure**: Odoo will perceive `insilos.partner` as a completely new model. It will create an empty `insilos_partner` table. The entire `ir_model`, `ir_model_fields`, `ir_model_data`, and `ir_ui_view` ecosystem will fracture, leaving legacy records orphaned.
- **The Fix**: Pre-boot SQL injection. The metadata must be rewritten (`UPDATE ir_model SET model = 'insilos.partner'`) *before* the Odoo WSGI server boots.

### d) Dynamic QWeb XPath & XML IDs
- **The Trap**: Downstream or custom modules using `<xpath expr="//field[@name='parent_id']" position="after">` based on the old view structure, or `<record id="base.view_partner_form">`.
- **The Failure**: Changing the `_name` forces changing the XML `<record model="insilos.partner">`. If the XML ID is renamed, `base.view_partner_form` becomes `base.view_insilos_partner_form`. Downstream `xpath` targeting the old ID will throw an `AssertionError: Element not found`.
- **The Fix**: Dual XML-ID aliasing. We inject proxy `ir_model_data` records pointing to the same `res_id`.

### e) OWL 3 Service Dependencies
- **The Trap**: JavaScript `this.env.services.orm.call('res.partner', 'method')`.
- **The Failure**: AST-Grep can easily miss dynamic string interpolations (e.g., `const model = 'res.' + type; orm.call(model)`).
- **The Fix**: Strict regex fallbacks and JS AST-Grep rules specifically targeting `useService("orm")` invocations.

---

## 2. Plan Calibration (Topological Order)

The PDCA cycle MUST adopt a **Database-First, Dual-Name Aliasing** approach. DB Views must precede ORM changes.

**Phase 1: DB Infrastructure (The Bridge)**
1. Enter maintenance mode.
2. Execute Raw SQL Migration: Rename table, indexes, constraints, sequences.
3. Establish Updatable View Facade (`CREATE VIEW res_partner AS SELECT * FROM insilos_partner`).
4. Update ORM Metadata (`ir_model`, `ir_ui_view`, etc.).

**Phase 2: Codebase AST-Grep (The Fork)**
1. ORM Layer: `_name`, `_inherit`, `self.env[...]`.
2. QWeb Layer: `<record model="...">`, `<field name="relation">`.
3. OWL Layer: JS ORM calls.

**Phase 3: Cleanup (The Severance)**
1. After 1 release cycle confirming zero legacy traffic, drop the Updatable Views.

### Hardened SQL Pattern
```sql
BEGIN;
-- 1. Rename Table & Sequence
ALTER TABLE res_partner RENAME TO insilos_partner;
ALTER SEQUENCE res_partner_id_seq RENAME TO insilos_partner_id_seq;

-- 2. Update Default Expression
ALTER TABLE insilos_partner ALTER COLUMN id SET DEFAULT nextval('insilos_partner_id_seq'::regclass);

-- 3. Create Updatable View (Facade)
CREATE OR REPLACE VIEW res_partner AS SELECT * FROM insilos_partner;

-- 4. Rewrite Core ORM Metadata
UPDATE ir_model SET model = 'insilos.partner' WHERE model = 'res.partner';
UPDATE ir_model_fields SET model = 'insilos.partner' WHERE model = 'res.partner';
UPDATE ir_model_fields SET relation = 'insilos.partner' WHERE relation = 'res.partner';
UPDATE ir_ui_view SET model = 'insilos.partner' WHERE model = 'res.partner';
UPDATE ir_actions_act_window SET res_model = 'insilos.partner' WHERE res_model = 'res.partner';

-- 5. Alias ir_model_data (Preserve XML IDs for downstream modules)
-- Not changing the name, just pointing the existing XML ID to the new model string
UPDATE ir_model_data SET model = 'insilos.partner' WHERE model = 'res.partner';
COMMIT;
```

---

## 3. Cohort 1: First Bounded Experimental Trial

**Recommendation**: `res.partner.category` (to become `insilos.partner.category`).

**Why?**
- `ir.attachment` is too deeply embedded in binary storage, file streaming, and raw SQL queries (high risk).
- `res.partner` is the flagship and has the most complex foreign key web and OWL dependencies (fatal risk for Cohort 1).
- `res.partner.category` (Partner Tags) is lightweight, has a standard `many2many` cross-table (`res_partner_res_partner_category_rel`), and minimal OWL footprint. It perfectly isolates the ORM Metadata and M2M table renaming logic.

### Cohort 1 Blueprint

**1. AST-Grep Rules (`rules/orm/rename_category.yml`)**
```yaml
id: rename-res-partner-category
language: python
rule:
  pattern: 'res.partner.category'
fix: 'insilos.partner.category'
```

**2. SQL Migration (`up.sql`)**
```sql
BEGIN;
ALTER TABLE res_partner_category RENAME TO insilos_partner_category;
ALTER SEQUENCE res_partner_category_id_seq RENAME TO insilos_partner_category_id_seq;
ALTER TABLE insilos_partner_category ALTER COLUMN id SET DEFAULT nextval('insilos_partner_category_id_seq'::regclass);

-- Rename M2M relation table
ALTER TABLE res_partner_res_partner_category_rel RENAME TO insilos_partner_category_rel;

-- Updatable Views
CREATE OR REPLACE VIEW res_partner_category AS SELECT * FROM insilos_partner_category;
CREATE OR REPLACE VIEW res_partner_res_partner_category_rel AS SELECT * FROM insilos_partner_category_rel;

-- Metadata Update
UPDATE ir_model SET model = 'insilos.partner.category' WHERE model = 'res.partner.category';
UPDATE ir_model_fields SET model = 'insilos.partner.category' WHERE model = 'res.partner.category';
UPDATE ir_model_fields SET relation = 'insilos.partner.category' WHERE relation = 'res.partner.category';
COMMIT;
```

**3. Reversible Rollback (`down.sql`)**
```sql
BEGIN;
DROP VIEW res_partner_category;
DROP VIEW res_partner_res_partner_category_rel;

ALTER TABLE insilos_partner_category RENAME TO res_partner_category;
ALTER SEQUENCE insilos_partner_category_id_seq RENAME TO res_partner_category_id_seq;
ALTER TABLE res_partner_category ALTER COLUMN id SET DEFAULT nextval('res_partner_category_id_seq'::regclass);

ALTER TABLE insilos_partner_category_rel RENAME TO res_partner_res_partner_category_rel;

UPDATE ir_model SET model = 'res.partner.category' WHERE model = 'insilos.partner.category';
UPDATE ir_model_fields SET model = 'res.partner.category' WHERE model = 'insilos.partner.category';
UPDATE ir_model_fields SET relation = 'res.partner.category' WHERE relation = 'insilos.partner.category';
COMMIT;
```

**4. Automated Check Criteria (PDCA 'Check')**
- **Test 1**: Verify `SELECT * FROM res_partner_category` still returns data (View Integrity).
- **Test 2**: Run `odoo-bin -i base -u base --stop-after-init`. If Odoo attempts to execute `CREATE TABLE insilos_partner_category` or logs `DROP CONSTRAINT`, the DB Phase failed.
- **Test 3**: Create a new tag via the UI. Ensure `insilos_partner_category` sequence increments correctly and no ORM traceback occurs.
