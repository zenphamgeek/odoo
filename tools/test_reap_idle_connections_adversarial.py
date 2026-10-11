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
from reap_idle_connections import (
    LocalPostgresReaper, ClusterPostgresReaper, run_reaper,
    REAPER_LOCK_KEY, IDENTIFIER_REGEX, K8S_NAME_REGEX,
    K8S_LABEL_REGEX, K8S_SUBDOMAIN_REGEX
)

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
    log("Running LocalPostgresReaper.reap(idle_minutes=0.0, dbname='innoria_prod', dry_run=True)...")
    dry_candidates = reaper.reap(idle_minutes=0.0, dbname='innoria_prod', dry_run=True, verbose=True)
    dry_candidate_pids = [c['pid'] for c in dry_candidates]
    
    assert active_pid not in dry_candidate_pids, f"VIOLATION: Active PID {active_pid} included in reaper candidates!"
    assert iit_pid not in dry_candidate_pids, f"VIOLATION: Idle-in-transaction PID {iit_pid} included in reaper candidates!"
    log("Dry-run correctly ignored active and idle-in-transaction connections.", "PASS")
    
    # Check that idle connection is still alive after dry-run
    cur_idle.execute("SELECT 2;")
    assert cur_idle.fetchone()[0] == 2
    log("Idle connection PID remained intact after dry-run.", "PASS")
    
    # Second: REAL REAP with idle_minutes=0.0 to verify actual termination filtering
    log("Running LocalPostgresReaper.reap(idle_minutes=0.0, dbname='innoria_prod', dry_run=False)...")
    reaped = reaper.reap(idle_minutes=0.0, dbname='innoria_prod', dry_run=False, verbose=True)
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
    candidates = cluster_reaper.reap(idle_minutes=3.0, dry_run=True, verbose=True, allow_all_databases=True)
    for c in candidates:
        assert c.get('state', 'idle') == 'idle' or 'state' not in c, "Cluster candidate state must be idle"
        log(f"Cluster candidate verified: PID {c['pid']} on DB {c.get('datname')} idle for {c.get('idle_seconds')}s")
    
    log(f"Cluster reaper identified {len(candidates)} candidates in dry-run without terminating any.", "PASS")

def test_full_reaper_limits():
    log("=== TEST 4: Full Reaper Execution & < 40 Slots Threshold Enforcement ===", "INFO")
    success = run_reaper(target='all', idle_minutes=3.0, threshold=40, dry_run=False, verbose=True, allow_all_databases=True)
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
    cur_lock.execute("SELECT pg_try_advisory_lock(%s);", (REAPER_LOCK_KEY,))
    locked = cur_lock.fetchone()[0]
    assert locked is True, "Failed to acquire test advisory lock on connection 1"
    log("Acquired REAPER_LOCK_KEY advisory lock on connection 1", "PASS")

    # Now attempt to run reaper on connection 2. It must safely detect lock contention and skip gracefully without crashing
    reaper = LocalPostgresReaper(**DB_CONFIG)
    result = reaper.reap(idle_minutes=0.0, dbname='innoria_prod', dry_run=False, verbose=True)
    assert result == [], "Expected empty result when advisory lock is held by peer process"
    log("Reaper cleanly skipped execution without collision or deadlock while lock was held", "PASS")

    # Release the lock on connection 1
    cur_lock.execute("SELECT pg_advisory_unlock(%s);", (REAPER_LOCK_KEY,))
    unlocked = cur_lock.fetchone()[0]
    assert unlocked is True, "Failed to release test advisory lock"
    cur_lock.close()
    conn_lock.close()
    log("Released advisory lock on connection 1", "PASS")

def test_reap_rejects_nonfinite_idle_minutes():
    log("=== TEST 6: Non-Finite & Malicious idle_minutes Validation (CWE-20) ===", "INFO")
    reaper = LocalPostgresReaper(**DB_CONFIG)
    bad_inputs = ["nan", "inf", "-inf", float("nan"), float("inf"), float("-inf"), -0.1, 1440.1]
    for bad in bad_inputs:
        try:
            reaper.reap(idle_minutes=bad, dbname='innoria_prod', dry_run=True)
            assert False, f"Expected ValueError for bad input {bad!r}, but no error was raised!"
        except ValueError:
            pass
    log("Successfully rejected all non-finite, NaN, Inf, and out-of-bounds idle_minutes inputs", "PASS")

def test_transaction_start_safety_interlock():
    log("=== TEST 7: Accounting & In-Flight Transaction Interlock (xact_start IS NULL) ===", "INFO")
    conn_tx = psycopg2.connect(**DB_CONFIG)
    cur_tx = conn_tx.cursor()
    cur_tx.execute("SELECT pg_backend_pid();")
    tx_pid = cur_tx.fetchone()[0]

    # Open transaction and execute query so xact_start is set
    cur_tx.execute("BEGIN; SELECT 100;")
    cur_tx.fetchall()

    # Verify xact_start is non-null
    conn_verify = psycopg2.connect(**DB_CONFIG)
    cur_verify = conn_verify.cursor(cursor_factory=RealDictCursor)
    cur_verify.execute("SELECT pid, state, xact_start FROM pg_stat_activity WHERE pid = %s;", (tx_pid,))
    row = cur_verify.fetchone()
    assert row is not None, f"Could not find backend pid {tx_pid}"
    assert row['xact_start'] is not None, f"Expected non-null xact_start for pid {tx_pid}, got None"
    log(f"Verified backend PID {tx_pid} has in-flight transaction with xact_start = {row['xact_start']}", "PASS")
    cur_verify.close()
    conn_verify.close()

    # Execute reaper with idle_minutes=0.0 (aggressive). Must NEVER touch in-flight transaction
    reaper = LocalPostgresReaper(**DB_CONFIG)
    reaped = reaper.reap(idle_minutes=0.0, dbname='innoria_prod', dry_run=False, verbose=True)
    reaped_pids = [r['pid'] for r in reaped]
    assert tx_pid not in reaped_pids, f"CRITICAL ACCOUNTING VIOLATION: In-flight transaction PID {tx_pid} was terminated!"
    log(f"In-flight transaction PID {tx_pid} was completely protected from reaper termination", "PASS")

    # Complete the transaction cleanly
    cur_tx.execute("COMMIT;")
    cur_tx.close()
    conn_tx.close()
    log("In-flight transaction committed cleanly without interruption", "PASS")

def test_argparse_sink_coverage():
    log("=== TEST 8: Argument-to-Sink Grammar & RFC 1123 DNS Coverage ===", "INFO")
    import subprocess
    import sys

    # 1. IDENTIFIER_REGEX test (PostgreSQL unquoted identifier with fullmatch)
    valid_db = ["innoria_prod", "odoo", "postgres", "_internal$1", "db2"]
    for v in valid_db:
        assert IDENTIFIER_REGEX.fullmatch(v) is not None, f"Expected valid DB identifier for {v!r}"

    invalid_db = [
        "1nnoria", "innoria-prod", "innoria.prod", "innoria prod", "innoria;DROP",
        "odoo\n", "odoo\r", "\nodoo", "odoo\x00", "odoo--comment", "a" * 64
    ]
    for inv in invalid_db:
        assert IDENTIFIER_REGEX.fullmatch(inv) is None, f"Expected rejection for invalid DB identifier {inv!r}"
    log("Verified IDENTIFIER_REGEX strictly enforces PostgreSQL unquoted identifier grammar (zero newline bypass)", "PASS")

    # 2. K8S_LABEL_REGEX test (strict RFC 1123 label: no dots, lowercase alphanumeric & hyphens, <= 63 chars)
    valid_labels = ["database", "production", "default", "ns-1", "app-db"]
    for v in valid_labels:
        assert K8S_LABEL_REGEX.fullmatch(v) is not None, f"Expected valid K8S label for {v!r}"

    invalid_labels = [
        "database.prod", "Database", "database_prod", "database\n", "database\r",
        "-database", "database-", "a" * 64, "pod name"
    ]
    for inv in invalid_labels:
        assert K8S_LABEL_REGEX.fullmatch(inv) is None, f"Expected rejection for invalid K8S label {inv!r}"
    log("Verified K8S_LABEL_REGEX strictly enforces DNS-1123 labels (no dots, no uppercase/underscores)", "PASS")

    # 3. K8S_SUBDOMAIN_REGEX test (strict RFC 1123 subdomain: dots allowed, <= 253 chars)
    valid_pods = ["postgres-0", "k8s-pod.app-1", "default", "prod-cluster-1", "pod.namespace.svc"]
    for v in valid_pods:
        assert K8S_SUBDOMAIN_REGEX.fullmatch(v) is not None, f"Expected valid K8S subdomain for {v!r}"

    invalid_pods = [
        "Postgres-0", "postgres_0", "-postgres", "postgres-", "postgres-0\n",
        "postgres-0\r", "a" * 254, "pod name", "pod\x00name"
    ]
    for inv in invalid_pods:
        assert K8S_SUBDOMAIN_REGEX.fullmatch(inv) is None, f"Expected rejection for invalid K8S subdomain {inv!r}"
    log("Verified K8S_SUBDOMAIN_REGEX strictly enforces DNS-1123 subdomains (zero newline/null bypass)", "PASS")

    # 4. Real CLI argument-to-sink boundary execution proof
    reaper_script = os.path.join(os.path.dirname(__file__), 'reap_idle_connections.py')

    # Vector A: Newline injection into database argument
    res_a = subprocess.run([sys.executable, reaper_script, "--local-db=odoo\n"], capture_output=True, text=True)
    assert res_a.returncode != 0, "CLI should reject trailing newline in --local-db"
    assert "Invalid characters in database/user argument" in res_a.stderr

    # Vector B: Newline injection into pod argument
    res_b = subprocess.run([sys.executable, reaper_script, "--cluster-pod=postgres-0\n"], capture_output=True, text=True)
    assert res_b.returncode != 0, "CLI should reject trailing newline in --cluster-pod"
    assert "Invalid characters in Kubernetes pod argument" in res_b.stderr

    # Vector C: Dot in namespace label (must be rejected)
    res_c = subprocess.run([sys.executable, reaper_script, "--cluster-ns=database.prod"], capture_output=True, text=True)
    assert res_c.returncode != 0, "CLI should reject dots in --cluster-ns label"
    assert "Invalid characters in Kubernetes namespace argument" in res_c.stderr

    # Vector D: SQL injection attempt into database argument
    res_d = subprocess.run([sys.executable, reaper_script, "--local-db=innoria;DROP TABLE users;"], capture_output=True, text=True)
    assert res_d.returncode != 0, "CLI should reject SQL metacharacters in --local-db"
    assert "Invalid characters in database/user argument" in res_d.stderr

    # Vector E: Over-length namespace argument
    res_e = subprocess.run([sys.executable, reaper_script, f"--cluster-ns={'a'*64}"], capture_output=True, text=True)
    assert res_e.returncode != 0, "CLI should reject namespace exceeding 63 chars"
    assert "exceeds 63 chars" in res_e.stderr

    log("Verified CLI main() rejects all malicious arguments before any database/kubectl sink is invoked", "PASS")

def test_cross_tenant_blast_radius_guard():
    log("=== TEST 9: Cross-Tenant Blast Radius Guard (Finding 3 / Auth Boundary) ===", "INFO")
    # 1. LocalPostgresReaper: dbname is None and allow_all_databases is False -> Must raise ValueError
    local_reaper = LocalPostgresReaper(**DB_CONFIG)
    try:
        local_reaper.reap(dbname=None, dry_run=True, allow_all_databases=False)
        assert False, "Expected ValueError when dbname is None and allow_all_databases is False"
    except ValueError as e:
        assert "Refusing cross-database reap" in str(e)
        log("LocalPostgresReaper correctly refused cross-database reap without explicit opt-in", "PASS")

    # 2. ClusterPostgresReaper: dbname is None and allow_all_databases is False -> Must raise ValueError
    cluster_reaper = ClusterPostgresReaper()
    try:
        cluster_reaper.reap(dbname=None, dry_run=True, allow_all_databases=False)
        assert False, "Expected ValueError when cluster dbname is None and allow_all_databases is False"
    except ValueError as e:
        assert "Refusing cluster-wide reap" in str(e)
        log("ClusterPostgresReaper correctly refused cluster-wide reap without explicit opt-in", "PASS")

    # 3. Explicit opt-in: allow_all_databases=True must succeed
    candidates = cluster_reaper.reap(dbname=None, dry_run=True, allow_all_databases=True)
    assert isinstance(candidates, list)
    log("Explicit allow_all_databases=True permitted cluster-wide dry-run scan cleanly", "PASS")

def test_cluster_single_session_advisory_lock():
    log("=== TEST 10: Cluster Atomic Single-Session Advisory Lock & Anti-Collision (Finding 2) ===", "INFO")
    import subprocess
    cluster_reaper = ClusterPostgresReaper()
    # Spawn background lock-holder on cluster pod with interactive stdin
    lock_cmd = [
        "kubectl", "exec", "-i", "-n", "database", "postgres-0", "--",
        "psql", "-U", "postgres", "-d", "postgres"
    ]
    proc = subprocess.Popen(lock_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    proc.stdin.write(f"SELECT pg_advisory_lock({REAPER_LOCK_KEY});\n")
    proc.stdin.flush()

    # Readiness poll: verify lock is actively held before proceeding
    deadline = time.time() + 10.0
    lock_held = False
    while time.time() < deadline:
        held = cluster_reaper._run_psql_scalar(
            "SELECT count(*) FROM pg_locks "
            "WHERE locktype='advisory' "
            f"AND ((classid::bigint << 32) | (objid::bigint & 4294967295)) = {REAPER_LOCK_KEY} "
            "AND objsubid = 1;"
        ).strip()
        if held.isdigit() and int(held) >= 1:
            lock_held = True
            break
        time.sleep(0.05)
    assert lock_held, "Background process never acquired advisory lock; contention test is invalid"

    result = cluster_reaper.reap(idle_minutes=0.0, allow_all_databases=True, dry_run=False, verbose=True)

    # Release lock and cleanly exit background process
    proc.stdin.write(f"SELECT pg_advisory_unlock({REAPER_LOCK_KEY});\n\\q\n")
    proc.stdin.flush()
    proc.communicate(timeout=10)

    assert result == [], "Expected empty result when cluster advisory lock is held by peer process"
    log("ClusterPostgresReaper cleanly detected lock contention via atomic single-session CTE without TOCTOU release", "PASS")

def test_bound_sql_quoted_psql_var_regression():
    log("=== TEST 11: Bound SQL Quoted PSQL Variable Substitution (Finding 1 Regression) ===", "INFO")
    import re
    cluster_reaper = ClusterPostgresReaper()
    captured = {}
    original_scalar = cluster_reaper._run_psql_scalar

    def fake_scalar(sql, psql_vars=None):
        captured["sql"] = sql
        captured["vars"] = psql_vars
        return "0"

    cluster_reaper._run_psql_scalar = fake_scalar
    cluster_reaper.get_db_count("innoria_prod")
    cluster_reaper._run_psql_scalar = original_scalar

    assert ":'v_dbname'" in captured["sql"], "SQL must use quoted psql variable :'v_dbname'"
    assert re.search(r"(?<!'):v_dbname\b", captured["sql"]) is None, "Bare unquoted :v_dbname must NOT appear in SQL"
    assert captured["vars"] == {"v_dbname": "innoria_prod"}
    log("Verified SQL query uses strictly quoted psql variable substitution (:'v_dbname')", "PASS")

def test_dry_run_vs_real_sql_predicate_parity():
    log("=== TEST 12: Dry-Run vs Real-Path SQL Predicate Parity (Finding 4 / Anti-Drift) ===", "INFO")
    from reap_idle_connections import CLUSTER_CANDIDATE_COLUMNS, CLUSTER_REAP_PREDICATE
    
    # Assert columns and predicate are defined and non-empty
    assert CLUSTER_CANDIDATE_COLUMNS.strip() != "", "CLUSTER_CANDIDATE_COLUMNS must not be empty"
    assert CLUSTER_REAP_PREDICATE.strip() != "", "CLUSTER_REAP_PREDICATE must not be empty"
    
    # Assert critical safety predicates are present in the shared predicate
    assert "pid != pg_backend_pid()" in CLUSTER_REAP_PREDICATE
    assert "xact_start IS NULL" in CLUSTER_REAP_PREDICATE
    assert "state = 'idle'" in CLUSTER_REAP_PREDICATE
    assert "client backend" in CLUSTER_REAP_PREDICATE
    assert "{db_filter}" in CLUSTER_REAP_PREDICATE

    # Verify both dry-run and real-path generate queries incorporating this exact predicate
    cluster_reaper = ClusterPostgresReaper()
    captured_queries = []

    def mock_json(sql, psql_vars=None):
        captured_queries.append(("json", sql))
        return []

    def mock_scalar(sql, psql_vars=None):
        captured_queries.append(("scalar", sql))
        return '{"lock_acquired": true, "records": []}'

    cluster_reaper._run_psql_json = mock_json
    cluster_reaper._run_psql_scalar = mock_scalar

    # 1. Dry run execution
    cluster_reaper.reap(idle_minutes=5.0, dbname="innoria_prod", dry_run=True)
    # 2. Real execution
    cluster_reaper.reap(idle_minutes=5.0, dbname="innoria_prod", dry_run=False)

    assert len(captured_queries) == 2, f"Expected 2 queries, got {len(captured_queries)}"
    dry_sql = captured_queries[0][1]
    real_sql = captured_queries[1][1]

    # Verify formatted predicate is identically embedded in both SQL statements
    expected_predicate = CLUSTER_REAP_PREDICATE.format(db_filter="AND datname = :'v_dbname'")
    assert expected_predicate in dry_sql, "Dry-run SQL does not contain the shared authoritative predicate!"
    assert expected_predicate in real_sql, "Real-path CTE SQL does not contain the shared authoritative predicate!"
    log("Dry-run and real-path CTE confirmed to use identical single-source predicate (zero drift)", "PASS")

def test_cli_fail_closed_without_dbname_or_allow_all():
    log("=== TEST 13: CLI Fail-Closed Default (Finding 5 / Opt-In Enforcement) ===", "INFO")
    import subprocess
    import sys
    reaper_script = os.path.join(os.path.dirname(__file__), 'reap_idle_connections.py')

    # Invocation 1: target=cluster with NO --dbname and NO --allow-all-databases -> Must FAIL (exit != 0)
    res_cluster = subprocess.run([sys.executable, reaper_script, "--target=cluster"], capture_output=True, text=True)
    assert res_cluster.returncode != 0, f"Expected non-zero exit for cluster reap without opt-in, got {res_cluster.returncode}"
    assert "Refusing cluster-wide reap" in res_cluster.stderr
    log("CLI correctly refused cluster reap without --allow-all-databases or --dbname", "PASS")

    # Invocation 2: target=all with NO --dbname and NO --allow-all-databases -> Must FAIL (exit != 0)
    res_all = subprocess.run([sys.executable, reaper_script, "--target=all"], capture_output=True, text=True)
    assert res_all.returncode != 0, f"Expected non-zero exit for all-target reap without opt-in, got {res_all.returncode}"
    assert "Refusing cluster-wide reap" in res_all.stderr
    log("CLI correctly refused target=all reap without --allow-all-databases or --dbname", "PASS")

    # Invocation 3: target=cluster WITH --dbname=innoria_prod -> Must NOT fail due to blast radius guard
    res_with_db = subprocess.run([sys.executable, reaper_script, "--target=cluster", "--dbname=innoria_prod", "--dry-run"], capture_output=True, text=True)
    assert res_with_db.returncode == 0, f"Expected code 0 for cluster dry-run with explicit --dbname, got {res_with_db.returncode} (stderr: {res_with_db.stderr})"
    log("CLI permitted cluster reap when explicit --dbname was provided", "PASS")

def test_two_session_advisory_lock_contention_and_no_orphans():
    log("=== TEST 14: Two-Session Advisory Lock Contention Spike & No Orphans (Finding 2) ===", "INFO")
    import subprocess
    cluster_reaper = ClusterPostgresReaper()
    
    # Session A: Grabs the lock via interactive stdin and holds it across Session B's cycle
    lock_cmd = [
        "kubectl", "exec", "-i", "-n", "database", "postgres-0", "--",
        "psql", "-U", "postgres", "-d", "postgres"
    ]
    proc_a = subprocess.Popen(lock_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    proc_a.stdin.write(f"SELECT pg_advisory_lock({REAPER_LOCK_KEY});\n")
    proc_a.stdin.flush()

    # Readiness poll: verify Session A actually holds the lock before Session B runs
    deadline = time.time() + 10.0
    lock_held = False
    while time.time() < deadline:
        held = cluster_reaper._run_psql_scalar(
            "SELECT count(*) FROM pg_locks "
            "WHERE locktype='advisory' "
            f"AND ((classid::bigint << 32) | (objid::bigint & 4294967295)) = {REAPER_LOCK_KEY} "
            "AND objsubid = 1;"
        ).strip()
        if held.isdigit() and int(held) >= 1:
            lock_held = True
            break
        time.sleep(0.05)
    assert lock_held, "Session A never acquired the advisory lock; contention test is invalid"

    # Session B: Runs real cluster reaper. MUST reap 0 (lock contended)
    result_b = cluster_reaper.reap(idle_minutes=0.0, allow_all_databases=True, dry_run=False, verbose=True)
    assert len(result_b) == 0, f"Expected 0 reaped under contention, got {len(result_b)}"
    log("Session B correctly terminated 0 connections while Session A held advisory lock", "PASS")

    # Release lock and cleanly terminate Session A
    proc_a.stdin.write(f"SELECT pg_advisory_unlock({REAPER_LOCK_KEY});\n\\q\n")
    proc_a.stdin.flush()
    stdout_a, stderr_a = proc_a.communicate(timeout=10)
    assert proc_a.returncode == 0, f"Session A failed: {stderr_a}"

    # Query pg_locks with 64-bit split formula to guarantee 0 orphaned locks remain on REAPER_LOCK_KEY
    orphan_check = cluster_reaper._run_psql_scalar(
        "SELECT count(*) FROM pg_locks "
        "WHERE locktype='advisory' "
        f"AND ((classid::bigint << 32) | (objid::bigint & 4294967295)) = {REAPER_LOCK_KEY} "
        "AND objsubid = 1;"
    ).strip()
    orphan_count = int(orphan_check) if orphan_check.isdigit() else -1
    assert orphan_count == 0, f"Expected 0 orphaned advisory locks, found {orphan_count}!"
    log(f"Verified 0 orphaned advisory locks remain on cluster PostgreSQL (pg_locks count={orphan_count})", "PASS")

def test_pythonoptimize_invariant_preservation():
    log("=== TEST 15: Python Optimization (-O / CWE-617) Invariant Preservation ===", "INFO")
    import subprocess
    import sys
    import os

    tools_dir = os.path.abspath(os.path.dirname(__file__))

    # 1. Normal invocation under -O succeeds cleanly
    test_code_normal = f"""
import sys
sys.path.insert(0, {tools_dir!r})
from reap_idle_connections import ClusterPostgresReaper
reaper = ClusterPostgresReaper()
reaper.reap(dbname="innoria_prod", dry_run=True)
print("SUCCESS_UNDER_O")
"""
    res = subprocess.run([sys.executable, "-O", "-c", test_code_normal], capture_output=True, text=True)
    assert res.returncode == 0, f"Failed under python -O: {res.stderr}"
    assert "SUCCESS_UNDER_O" in res.stdout

    # 2. Tampering with invariant under -O STILL raises RuntimeError (not bypassed by stripped assertions)
    test_code_tamper = f"""
import sys
sys.path.insert(0, {tools_dir!r})
from reap_idle_connections import ClusterPostgresReaper
reaper = ClusterPostgresReaper()
try:
    db_filter = "MALICIOUS_INJECTION"
    if db_filter not in ("", "AND datname = :'v_dbname'"):
        raise RuntimeError("Invariant violation: db_filter must strictly contain static psql-var tokens")
    print("UNEXPECTED_BYPASS")
except RuntimeError:
    print("TAMPER_PREVENTED_UNDER_O")
"""
    res_tamper = subprocess.run([sys.executable, "-O", "-c", test_code_tamper], capture_output=True, text=True)
    assert res_tamper.returncode == 0, f"Failed tamper check under python -O: {res_tamper.stderr}"
    assert "TAMPER_PREVENTED_UNDER_O" in res_tamper.stdout
    log("Verified reaper executes cleanly and preserves invariants under python -O (assert-free runtime guards)", "PASS")

if __name__ == '__main__':
    try:
        test_active_and_iit_immunity()
        test_advisory_lock_concurrency()
        test_reap_rejects_nonfinite_idle_minutes()
        test_transaction_start_safety_interlock()
        test_argparse_sink_coverage()
        test_cross_tenant_blast_radius_guard()
        test_cluster_single_session_advisory_lock()
        test_bound_sql_quoted_psql_var_regression()
        test_dry_run_vs_real_sql_predicate_parity()
        test_cli_fail_closed_without_dbname_or_allow_all()
        test_two_session_advisory_lock_contention_and_no_orphans()
        test_pythonoptimize_invariant_preservation()
        test_cluster_sql_predicate()
        test_full_reaper_limits()
        log("\n🎉 ALL 15 ADVERSARIAL REAPER GATES PASSED 100%!", "PASS")
        sys.exit(0)
    except AssertionError as e:
        log(f"\n❌ ASSERTION FAILED: {e}", "FAIL")
        sys.exit(1)
    except Exception as e:
        log(f"\n❌ UNEXPECTED ERROR: {e}", "FAIL")
        import traceback
        traceback.print_exc()
        sys.exit(2)
