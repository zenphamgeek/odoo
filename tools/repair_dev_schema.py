#!/usr/bin/env python3
"""Database schema bridge for insilos20_dev relation tables (AL2C-NEW-002).
Creates bi-directional views/rules so ORM operations succeed under both legacy and refactored table names.
"""
import sys
import psycopg2

DB_CONFIG = {
    "dbname": "insilos20_dev",
    "user": "odoo",
    "host": "127.0.0.1",
    "port": 5434
}

BRIDGES = [
    {
        "view": "catalog_sku_loyalty_rule_rel",
        "underlying": "loyalty_rule_catalog_sku_rel",
        "cols": ("catalog_sku_id", "loyalty_rule_id"),
        "rule_ins": "catalog_sku_loyalty_rule_ins",
        "rule_del": "catalog_sku_loyalty_rule_del",
    },
    {
        "view": "catalog_sku_loyalty_reward_rel",
        "underlying": "loyalty_reward_catalog_sku_rel",
        "cols": ("catalog_sku_id", "loyalty_reward_id"),
        "rule_ins": "catalog_sku_loyalty_reward_ins",
        "rule_del": "catalog_sku_loyalty_reward_del",
    },
    {
        "view": "documents_document_system_attachment_rel",
        "underlying": "documents_document_ir_attachment_rel",
        "cols": ("documents_document_id", "system_attachment_id"),
        "underlying_cols": ("documents_document_id", "ir_attachment_id"),
        "rule_ins": "doc_sys_att_ins",
        "rule_del": "doc_sys_att_del",
    },
    {
        "view": "catalog_item_helpdesk_sla_rel",
        "underlying": "helpdesk_sla_catalog_item_rel",
        "cols": ("catalog_item_id", "helpdesk_sla_id"),
        "rule_ins": "cat_item_hd_sla_ins",
        "rule_del": "cat_item_hd_sla_del",
    }
]

def check(conn):
    with conn.cursor() as cur:
        for b in BRIDGES:
            cur.execute("SELECT to_regclass(%s)", (b["view"],))
            res = cur.fetchone()[0]
            if not res:
                print(f"[FAIL] Missing view {b['view']}")
                return False
            print(f"[PASS] Bridge view {b['view']} -> {b['underlying']} exists")
        cur.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'sign_request_completed_document_rel' AND column_name = 'system_attachment_id';
        """)
        if not cur.fetchone():
            print("[FAIL] Missing column system_attachment_id on sign_request_completed_document_rel")
            return False
        print("[PASS] Column system_attachment_id on sign_request_completed_document_rel exists")
    return True

def apply(conn):
    with conn.cursor() as cur:
        for b in BRIDGES:
            view = b["view"]
            underlying = b["underlying"]
            c1, c2 = b["cols"]
            uc1, uc2 = b.get("underlying_cols", b["cols"])
            
            # Check if underlying table exists
            cur.execute("SELECT to_regclass(%s)", (underlying,))
            if not cur.fetchone()[0]:
                print(f"[SKIP] Underlying table {underlying} does not exist")
                continue
                
            cur.execute(f"""
                CREATE OR REPLACE VIEW {view} AS 
                SELECT {uc1} AS {c1}, {uc2} AS {c2} FROM {underlying};
            """)
            
            cur.execute(f"""
                CREATE OR REPLACE RULE {b['rule_ins']} AS ON INSERT TO {view}
                DO INSTEAD INSERT INTO {underlying} ({uc1}, {uc2}) VALUES (NEW.{c1}, NEW.{c2});
            """)
            
            cur.execute(f"""
                CREATE OR REPLACE RULE {b['rule_del']} AS ON DELETE TO {view}
                DO INSTEAD DELETE FROM {underlying} WHERE {uc1} = OLD.{c1} AND {uc2} = OLD.{c2};
            """)
            print(f"[OK] Applied bridge for {view} -> {underlying}")

        cur.execute("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sign_request_completed_document_rel') THEN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sign_request_completed_document_rel' AND column_name = 'system_attachment_id') THEN
                        ALTER TABLE sign_request_completed_document_rel ADD COLUMN system_attachment_id integer;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sign_request_completed_document_rel' AND column_name = 'ir_attachment_id') THEN
                            UPDATE sign_request_completed_document_rel SET system_attachment_id = ir_attachment_id;
                        END IF;
                    END IF;
                END IF;
            END $$;
        """)
        print("[OK] Verified system_attachment_id column on sign_request_completed_document_rel")
    conn.commit()

def main():
    check_mode = "--check" in sys.argv
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
        
    if check_mode:
        ok = check(conn)
        conn.close()
        sys.exit(0 if ok else 1)
    else:
        apply(conn)
        ok = check(conn)
        conn.close()
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
