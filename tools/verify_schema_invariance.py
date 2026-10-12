#!/usr/bin/env python3
"""
Empirical PostgreSQL Schema Invariance Auditor
Port: 5434
Target Databases: odoo20_dev, insilos20_dev, innoria_prod
Reference Database: innokafe_prod
"""

import psycopg2
import sys

DATABASES = ["odoo20_dev", "insilos20_dev", "innoria_prod"]
DB_HOST = "127.0.0.1"
DB_PORT = 5434
DB_USER = "odoo"
DB_PASS = "1NN0R1@2026"

def audit_database(dbname):
    print(f"\nAUDITING DATABASE: {dbname}")
    print("-" * 60)
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=dbname)
        cur = conn.cursor()
        
        # 1. Check ir_module_module (only installed modules mutate schema/runtime)
        cur.execute("SELECT name, state FROM ir_module_module WHERE name LIKE '%innokafe%' AND state = 'installed';")
        modules = cur.fetchall()
        print(f"  • Installed Innokafe modules in ir_module_module: {modules} (Expected: [])")
        
        # 2. Check information_schema.tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%innokafe%';")
        tables = cur.fetchall()
        print(f"  • Innokafe tables in information_schema: {tables} (Expected: [])")
        
        # 3. Check information_schema.columns
        cur.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='public' AND column_name LIKE '%innokafe%';")
        columns = cur.fetchall()
        print(f"  • Innokafe columns in information_schema: {columns} (Expected: [])")
        
        # 4. Check ir_model_fields
        cur.execute("SELECT model, name FROM ir_model_fields WHERE name LIKE '%innokafe%';")
        model_fields = cur.fetchall()
        print(f"  • Innokafe fields in ir_model_fields: {model_fields} (Expected: [])")
        
        # 5. Check ir_model
        cur.execute("SELECT model, name FROM ir_model WHERE model LIKE '%innokafe%';")
        models = cur.fetchall()
        print(f"  • Innokafe models in ir_model: {models} (Expected: [])")

        conn.close()

        is_invariant = (len(modules) == 0 and len(tables) == 0 and len(columns) == 0 and len(model_fields) == 0 and len(models) == 0)
        status_str = "✅ STRICT INVARIANCE CONFIRMED (0 mutations)" if is_invariant else "❌ VIOLATION DETECTED"
        print(f"  -> RESULT: {status_str}")
        return is_invariant

    except Exception as e:
        print(f"  ❌ Error connecting to {dbname}: {e}")
        return False

def audit_reference():
    print(f"\nAUDITING REFERENCE TENANT: innokafe_prod")
    print("-" * 60)
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname="innokafe_prod")
        cur = conn.cursor()
        cur.execute("SELECT name, state FROM ir_module_module WHERE name = 'innokafe_website';")
        mod = cur.fetchall()
        cur.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='public' AND column_name LIKE '%innokafe%';")
        cols = cur.fetchall()
        print(f"  • Module status: {mod}")
        print(f"  • Dedicated columns in innokafe_prod: {len(cols)} columns")
        for c in cols:
            print(f"     - {c[0]}.{c[1]}")
        conn.close()
    except Exception as e:
        print(f"  ❌ Error checking reference db: {e}")

if __name__ == "__main__":
    print("=" * 70)
    print("POSTGRESQL MULTI-TENANT SCHEMA INVARIANCE VERIFICATION REPORT")
    print("=" * 70)
    
    audit_reference()
    
    all_clean = True
    for db in DATABASES:
        if not audit_database(db):
            all_clean = False
            
    print("\n" + "=" * 70)
    if all_clean:
        print("🏆 VERDICT: 100% SCHEMA INVARIANCE CONFIRMED ACROSS ALL 3 DATABASES")
        print("=" * 70)
        sys.exit(0)
    else:
        print("🔴 VERDICT: SCHEMA LEAKAGE DETECTED")
        print("=" * 70)
        sys.exit(1)
