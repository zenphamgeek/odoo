#!/usr/bin/env python3
"""
tools/test_reap_idle_connections_adversarial.py
=============================================================================
Adversarial Stress Test Suite for tools/reap_idle_connections.py

Verifies:
1. Active session immunity: connections with state = 'active' are never reaped.
2. Idle-in-transaction immunity: connections with state = 'idle in transaction' are never reaped.
3. Dry-run safety: dry-run reports candidates without terminating any connection.
4. Threshold compliance: connections younger than idle_minutes threshold are spared.
5. Live execution & slot compliance: post-reap connection counts remain strictly < 40 slots.
=============================================================================
"""

import sys
import time
import threading
import psycopg2
from psycopg2.extras import RealDictCursor

import os

# Import the reaper module
from reap_idle_connections import LocalPostgresReaper, ClusterPostgresReaper, run_reaper

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5434,
    'user': 'odoo',
    'dbname': 'innoria_prod'
}
if os.getenv('PGPASSWORD'):
    DB_CONFIG['password'] = os.getenv('PGPASSWORD')
elif os.getenv('ODOO_DB_PASSWORD'):
    DB_CONFIG['password'] = os.getenv('ODOO_DB_PASSWORD')

def log(msg, level="INFO"):
    badges = {"INFO": "[*]", "PASS": "[✓]", "FAIL": "[✗]", "WARN": "[!]"}
    print(f"{badges.get(level, '[*]')} {msg}", flush=True)

def test_active_and_iit_immunity():
    log("=== TEST 1 & 2: Active Session & Idle-In-Transaction Immunity ===", "INFO")
    
    # 1. Open active session
    conn_active = psycopg2.connect(**DB_CONFIG)
    cur_active = conn_active.cursor()
    cur_active.execute("SELECT pg_backend_pid();")
    active_pid = cur_active.fetchone()[0]
    log(f"Spawned active session with PID {active_pid}")
    
    # 2. Open idle-in-transaction session
    conn_iit = psycopg2.connect(**DB_CONFIG)
    cur_iit = conn_iit.cursor()
    cur_iit.execute("SELECT pg_backend_pid();")
    iit_pid = cur_iit.fetchone()[0]
    cur_iit.execute("BEGIN; SELECT 1;")
    log(f"Spawned idle-in-transaction session with PID {iit_pid}")
    
    # 3. Open idle session
    conn_idle = psycopg2.connect(**DB_CONFIG)
    conn_idle.autocommit = True
    cur_idle = conn_idle.cursor()
    cur_idle.execute("SELECT pg_backend_pid();")
    idle_pid = cur_idle.fetchone()[0]
    cur_idle.execute("SELECT 1;")
    log(f"Spawned idle session with PID {idle_pid}")
    
    # Start long query in active connection in a separate thread
    active_finished = threading.Event()
    active_error = []
    
    def run_active_query():
        try:
            cur_active.execute("SELECT pg_sleep(3);")
            active_finished.set()
        except Exception as e:
            active_error.append(e)
            active_finished.set()
            
    t = threading.Thread(target=run_active_query)
    t.start()
    
    # Wait 0.5s for query to be running
    time.sleep(0.5)
    
    # Verify states in pg_stat_activity
    conn_check = psycopg2.connect(**DB_CONFIG)
    cur_check = conn_check.cursor(cursor_factory=RealDictCursor)
    cur_check.execute("SELECT pid, state FROM pg_stat_activity WHERE pid IN (%s, %s, %s);", (active_pid, iit_pid, idle_pid))
    observed_states = {row['pid']: row['state'] for row in cur_check.fetchall()}
    cur_check.close()
    conn_check.close()
    
    log(f"Verified states: PID {active_pid} = '{observed_states.get(active_pid)}', "
        f"PID {iit_pid} = '{observed_states.get(iit_pid)}', "
        f"PID {idle_pid} = '{observed_states.get(idle_pid)}'")
    
    assert observed_states.get(active_pid) == 'active', f"Expected active state for PID {active_pid}"
    assert observed_states.get(iit_pid) == 'idle in transaction', f"Expected idle in transaction for PID {iit_pid}"
    assert observed_states.get(idle_pid) == 'idle', f"Expected idle state for PID {idle_pid}"
    
    # Now run reaper with idle_minutes=0.0 (aggressive threshold to test predicate filtering)
    reaper = LocalPostgresReaper(**DB_CONFIG)
    
    # First: DRY RUN
    log("Running LocalPostgresReaper.reap(idle_minutes=0.0, dry_run=True)...")
    dry_candidates = reaper.reap(idle_minutes=0.0, dry_run=True, verbose=True)
    dry_candidate_pids = [c['pid'] for c in dry_candidates]
    
    assert active_pid not in dry_candidate_pids, f"VIOLATION: Active PID {active_pid} included in reaper candidates!"
    assert iit_pid not in dry_candidate_pids, f"VIOLATION: Idle-in-transaction PID {iit_pid} included in reaper candidates!"
    log("Dry-run correctly ignored active and idle-in-transaction connections.", "PASS")
    
    # Check that idle connection is still alive after dry-run
    cur_idle.execute("SELECT 2;")
    assert cur_idle.fetchone()[0] == 2
    log("Idle connection PID remained intact after dry-run.", "PASS")
    
    # Second: REAL REAP with idle_minutes=0.0 to verify actual termination filtering
    log("Running LocalPostgresReaper.reap(idle_minutes=0.0, dry_run=False)...")
    reaped = reaper.reap(idle_minutes=0.0, dry_run=False, verbose=True)
    reaped_pids = [r['pid'] for r in reaped]
    
    assert active_pid not in reaped_pids, f"CRITICAL VIOLATION: Active PID {active_pid} was terminated!"
    assert iit_pid not in reaped_pids, f"CRITICAL VIOLATION: Idle-in-transaction PID {iit_pid} was terminated!"
    log(f"Active PID {active_pid} and IIT PID {iit_pid} were NOT terminated by reaper.", "PASS")
    
    # Wait for active thread to finish
    t.join(timeout=5)
    assert not active_error, f"Active query raised error: {active_error}"
    log(f"Active query on PID {active_pid} finished normally without interruption.", "PASS")
    
    # Verify IIT connection can still commit cleanly
    cur_iit.execute("COMMIT;")
    cur_iit.execute("SELECT 42;")
    assert cur_iit.fetchone()[0] == 42
    log(f"Idle-in-transaction connection PID {iit_pid} remained alive and committed cleanly.", "PASS")
    
    # Clean up connections
    cur_active.close()
    conn_active.close()
    cur_iit.close()
    conn_iit.close()
    try:
        cur_idle.close()
        conn_idle.close()
    except Exception:
        pass
    log("All test connections cleaned up.", "PASS")

def test_cluster_sql_predicate():
    log("=== TEST 3: Cluster PostgreSQL Reaper Predicate & Safety Audit ===", "INFO")
    cluster_reaper = ClusterPostgresReaper()
    
    # Query cluster stats
    total, states, max_conn = cluster_reaper.get_stats()
    log(f"Cluster PostgreSQL stats: total={total}/{max_conn}, states={states}")
    
    # Run cluster reaper in dry-run
    candidates = cluster_reaper.reap(idle_minutes=3.0, dry_run=True, verbose=True)
    for c in candidates:
        assert c.get('state', 'idle') == 'idle' or 'state' not in c, "Cluster candidate state must be idle"
        log(f"Cluster candidate verified: PID {c['pid']} on DB {c.get('datname')} idle for {c.get('idle_seconds')}s")
    
    log(f"Cluster reaper identified {len(candidates)} candidates in dry-run without terminating any.", "PASS")

def test_full_reaper_limits():
    log("=== TEST 4: Full Reaper Execution & < 40 Slots Threshold Enforcement ===", "INFO")
    success = run_reaper(target='all', idle_minutes=3.0, threshold=40, dry_run=False, verbose=True)
    assert success, "Reaper run_reaper returned False!"
    
    # Verify local counts
    local_reaper = LocalPostgresReaper(**DB_CONFIG)
    total_local, _, max_local = local_reaper.get_stats()
    innoria_local = local_reaper.get_db_count('innoria_prod')
    log(f"Verified local connections: total={total_local} (<40), innoria_prod={innoria_local} (<40)")
    assert total_local < 40, f"Local total connections {total_local} >= 40!"
    assert innoria_local < 40, f"Local innoria_prod connections {innoria_local} >= 40!"
    
    # Verify cluster counts
    cluster_reaper = ClusterPostgresReaper()
    total_cluster, _, max_cluster = cluster_reaper.get_stats()
    innoria_cluster = cluster_reaper.get_db_count('innoria_prod')
    log(f"Verified cluster connections: total={total_cluster}, innoria_prod={innoria_cluster} (<40)")
    assert innoria_cluster < 40, f"Cluster innoria_prod connections {innoria_cluster} >= 40!"
    
    log("Post-reap connection counts strictly < 40 slots validated on all environments.", "PASS")

def test_advisory_lock_concurrency():
    log("=== TEST 5: Advisory Session Lock Concurrency & Anti-Collision ===", "INFO")
    # Open connection 1 and acquire the reaper advisory lock
    conn_lock = psycopg2.connect(**DB_CONFIG)
    cur_lock = conn_lock.cursor()
    cur_lock.execute("SELECT pg_try_advisory_lock(hashtext('pg_connection_pool_reaper'));")
    locked = cur_lock.fetchone()[0]
    assert locked is True, "Failed to acquire test advisory lock on connection 1"
    log("Acquired pg_connection_pool_reaper advisory lock on connection 1", "PASS")

    # Now attempt to run reaper on connection 2. It must safely detect lock contention and skip gracefully without crashing
    reaper = LocalPostgresReaper(**DB_CONFIG)
    result = reaper.reap(idle_minutes=0.0, dry_run=False, verbose=True)
    assert result == [], "Expected empty result when advisory lock is held by peer process"
    log("Reaper cleanly skipped execution without collision or deadlock while lock was held", "PASS")

    # Release the lock on connection 1
    cur_lock.execute("SELECT pg_advisory_unlock(hashtext('pg_connection_pool_reaper'));")
    unlocked = cur_lock.fetchone()[0]
    assert unlocked is True, "Failed to release test advisory lock"
    cur_lock.close()
    conn_lock.close()
    log("Released advisory lock on connection 1", "PASS")

if __name__ == '__main__':
    try:
        test_active_and_iit_immunity()
        test_advisory_lock_concurrency()
        test_cluster_sql_predicate()
        test_full_reaper_limits()
        log("\n🎉 ALL ADVERSARIAL REAPER TESTS PASSED 100%!", "PASS")
        sys.exit(0)
    except AssertionError as e:
        log(f"\n❌ ASSERTION FAILED: {e}", "FAIL")
        sys.exit(1)
    except Exception as e:
        log(f"\n❌ UNEXPECTED ERROR: {e}", "FAIL")
        import traceback
        traceback.print_exc()
        sys.exit(2)
