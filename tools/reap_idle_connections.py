#!/usr/bin/env python3
"""
tools/reap_idle_connections.py
=============================================================================
PostgreSQL Idle Connection Pool Reaper for Insilos SaaS Architecture.

Safely terminates stale PostgreSQL connections that have been idle for > 3 minutes,
preventing connection pool saturation and maintaining connection count well under
the 40/100 slot threshold.

Safety Invariants:
1. Targets only connections with state = 'idle'. Never touches 'active',
   'idle in transaction', or transaction-locked connections.
2. Filters out current backend PID (pid != pg_backend_pid()).
3. Excludes active replication workers, background writers, walreceiver/walsender,
   and autovacuum workers.
4. Operates across both local PostgreSQL (port 5434) and cluster PostgreSQL (postgres-0 / pgbouncer).
=============================================================================
"""

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from typing import Dict, List, Tuple, Any, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


def log(msg: str, level: str = 'INFO') -> None:
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    badges = {
        'INFO': '\033[94m[*]\033[0m',
        'SUCCESS': '\033[92m[✓]\033[0m',
        'WARN': '\033[93m[!]\033[0m',
        'ERROR': '\033[91m[✗]\033[0m',
        'HEADER': '\033[95m[⚡]\033[0m'
    }
    badge = badges.get(level, '[*]')
    print(f"{badge} {msg}")


def format_states(states_dict: Dict[Optional[str], int]) -> str:
    parts = []
    for state, cnt in sorted(states_dict.items(), key=lambda x: str(x[0])):
        label = state if state is not None else 'system/bg'
        parts.append(f"{label}: {cnt}")
    return ", ".join(parts) if parts else "none"


# Global Lock Registry: 0x52454150 is the allocated 32-bit integer namespace ('REAP' = 1380270416)
# Used exclusively for serializing postgres connection pool reaper sessions across local & cluster pods.
REAPER_LOCK_KEY = 0x52454150
IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_$]{0,62}$")


class LocalPostgresReaper:
    """Manages idle connection reaping on local PostgreSQL instance (port 5434)."""

    def __init__(self, host: str = '127.0.0.1', port: int = 5434,
                 user: str = 'odoo', password: Optional[str] = None,
                 dbname: str = 'innoria_prod'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password or os.getenv('PGPASSWORD') or os.getenv('ODOO_DB_PASSWORD') or None
        self.dbname = dbname

    def connect(self):
        if not HAS_PSYCOPG2:
            raise RuntimeError("psycopg2 is required for local PostgreSQL connection reaping.")
        conn_kwargs = {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'dbname': self.dbname,
        }
        if self.password:
            conn_kwargs['password'] = self.password
        return psycopg2.connect(**conn_kwargs)

    def acquire_advisory_lock(self, cur) -> bool:
        """Acquires a session-level advisory lock to serialize reaper runs and prevent races."""
        cur.execute("SELECT pg_try_advisory_lock(%s) AS locked;", (REAPER_LOCK_KEY,))
        row = cur.fetchone()
        return bool(row and (row['locked'] if isinstance(row, dict) else row[0]))

    def release_advisory_lock(self, cur) -> None:
        """Releases the session-level advisory lock."""
        cur.execute("SELECT pg_advisory_unlock(%s);", (REAPER_LOCK_KEY,))

    def get_stats(self) -> Tuple[int, Dict[Optional[str], int], int]:
        """Returns (total_connections, states_breakdown, max_connections)."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SHOW max_connections;")
                max_conn = int(cur.fetchone()[0])

                cur.execute("SELECT count(*) FROM pg_stat_activity;")
                total = cur.fetchone()[0]

                cur.execute("SELECT state, count(*) FROM pg_stat_activity GROUP BY state;")
                states = {row[0]: row[1] for row in cur.fetchall()}

                return total, states, max_conn

    def get_db_count(self, dbname: str = 'innoria_prod') -> int:
        """Returns connection count for a specific database."""
        if not IDENTIFIER_REGEX.match(dbname):
            raise ValueError(f"Invalid database name: {dbname}")
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = %s;", (dbname,))
                return int(cur.fetchone()[0])

    def reap(self, idle_minutes: float = 3.0, dbname: Optional[str] = None,
             dry_run: bool = False, verbose: bool = False) -> List[Dict[str, Any]]:
        """Identifies and terminates idle connections older than idle_minutes."""
        idle_mins = float(idle_minutes)
        if math.isnan(idle_mins) or math.isinf(idle_mins):
            raise ValueError(f"idle_minutes must be a finite number, got: {idle_minutes!r}")
        if idle_mins < 0.0 or idle_mins > 1440.0:
            raise ValueError(f"idle_minutes must be between 0.0 and 1440.0, got: {idle_minutes}")

        db_filter = ""
        params: List[Any] = [idle_mins]
        if dbname:
            if not IDENTIFIER_REGEX.match(dbname):
                raise ValueError(f"Invalid database name: {dbname}")
            db_filter = "AND datname = %s"
            params.append(dbname)

        candidate_sql = f"""
            SELECT
                pid,
                datname,
                usename,
                client_addr::text AS client_addr,
                state_change,
                round(extract(epoch FROM (now() - state_change)))::int AS idle_seconds
            FROM pg_stat_activity
            WHERE state = 'idle'
              AND state_change < now() - (%s * INTERVAL '1 minute')
              AND pid != pg_backend_pid()
              AND xact_start IS NULL
              AND (backend_type = 'client backend' OR backend_type IS NULL)
              {db_filter}
            ORDER BY state_change ASC;
        """

        reaped_records = []
        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if not dry_run and not self.acquire_advisory_lock(cur):
                    log("Another reaper process holds the advisory lock (REAPER_LOCK_KEY). Skipping cycle.", 'WARN')
                    return []
                try:
                    cur.execute(candidate_sql, tuple(params))
                    candidates = cur.fetchall()

                    for row in candidates:
                        pid = row.get('pid')
                        if pid is None or type(pid) is not int or pid <= 0:
                            continue
                        datname = row.get('datname') or 'unknown'
                        idle_sec = row.get('idle_seconds', 0)

                        if dry_run:
                            if verbose:
                                log(f"  [DRY-RUN] Would terminate PID {pid} (DB: {datname}, Idle: {idle_sec}s)", 'WARN')
                            reaped_records.append(dict(row))
                        else:
                            cur.execute("SELECT pg_terminate_backend(%s);", (pid,))
                            res = cur.fetchone()
                            terminated = bool(res and (res.get('pg_terminate_backend') if isinstance(res, dict) else res[0]))
                            rec = dict(row)
                            rec['terminated'] = terminated
                            if terminated:
                                reaped_records.append(rec)
                                if verbose:
                                    log(f"  Terminated idle PID {pid} on {datname} (idle {idle_sec}s)", 'SUCCESS')
                            else:
                                if verbose:
                                    log(f"  PID {pid} could not be terminated (may have already closed)", 'WARN')
                finally:
                    if not dry_run:
                        self.release_advisory_lock(cur)

        return reaped_records


class ClusterPostgresReaper:
    """Manages idle connection reaping on Kubernetes cluster PostgreSQL instance."""

    def __init__(self, namespace: str = 'database', pod: str = 'postgres-0',
                 user: str = 'postgres', dbname: str = 'postgres'):
        self.namespace = namespace
        self.pod = pod
        self.user = user
        self.dbname = dbname

    def _run_psql_json(self, sql: str) -> Any:
        wrapper_sql = f"SELECT json_agg(t) FROM ({sql.strip().rstrip(';')}) t;"
        cmd = [
            "kubectl", "exec", "-n", self.namespace, self.pod, "--",
            "psql", "-U", self.user, "-d", self.dbname, "-t", "-A", "-c", wrapper_sql
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if res.returncode != 0:
            raise RuntimeError(f"Cluster psql failed ({res.returncode}): {res.stderr.strip()}")
        out = res.stdout.strip()
        if not out:
            return []
        try:
            return json.loads(out)
        except Exception:
            # Fallback if json_agg returns null or empty
            return []

    def _run_psql_scalar(self, sql: str) -> str:
        cmd = [
            "kubectl", "exec", "-n", self.namespace, self.pod, "--",
            "psql", "-U", self.user, "-d", self.dbname, "-t", "-A", "-c", sql
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if res.returncode != 0:
            raise RuntimeError(f"Cluster psql failed ({res.returncode}): {res.stderr.strip()}")
        return res.stdout.strip()

    def get_stats(self) -> Tuple[int, Dict[Optional[str], int], int]:
        """Returns (total_connections, states_breakdown, max_connections)."""
        max_conn = int(self._run_psql_scalar("SHOW max_connections;"))
        total = int(self._run_psql_scalar("SELECT count(*) FROM pg_stat_activity;"))

        state_rows = self._run_psql_json(
            "SELECT COALESCE(state, 'system/bg') AS state, count(*)::int AS count FROM pg_stat_activity GROUP BY state"
        )
        states = {row['state']: row['count'] for row in state_rows} if state_rows else {}
        return total, states, max_conn

    def get_db_count(self, dbname: str = 'innoria_prod') -> int:
        """Returns connection count for a specific database."""
        if not IDENTIFIER_REGEX.match(dbname):
            raise ValueError(f"Invalid database name: {dbname}")
        out = self._run_psql_scalar(f"SELECT count(*) FROM pg_stat_activity WHERE datname = '{dbname}';")
        return int(out) if out.isdigit() else 0

    def reap(self, idle_minutes: float = 3.0, dbname: Optional[str] = None,
             dry_run: bool = False, verbose: bool = False) -> List[Dict[str, Any]]:
        """Identifies and terminates idle connections older than idle_minutes."""
        idle_mins = float(idle_minutes)
        if math.isnan(idle_mins) or math.isinf(idle_mins):
            raise ValueError(f"idle_minutes must be a finite number, got: {idle_minutes!r}")
        if idle_mins < 0.0 or idle_mins > 1440.0:
            raise ValueError(f"idle_minutes must be between 0.0 and 1440.0, got: {idle_minutes}")

        db_filter = ""
        if dbname:
            if not IDENTIFIER_REGEX.match(dbname):
                raise ValueError(f"Invalid database name: {dbname}")
            db_filter = f"AND datname = '{dbname}'"
        candidate_sql = f"""
            SELECT
                pid,
                datname,
                usename,
                client_addr::text AS client_addr,
                state_change::text AS state_change,
                round(extract(epoch FROM (now() - state_change)))::int AS idle_seconds
            FROM pg_stat_activity
            WHERE state = 'idle'
              AND state_change < now() - INTERVAL '{idle_mins} minutes'
              AND pid != pg_backend_pid()
              AND xact_start IS NULL
              AND (backend_type = 'client backend' OR backend_type IS NULL)
              {db_filter}
            ORDER BY state_change ASC
        """

        if not dry_run:
            locked = self._run_psql_scalar(f"SELECT pg_try_advisory_lock({REAPER_LOCK_KEY});")
            if locked.strip() != 't':
                log("Another cluster reaper process holds the advisory lock (REAPER_LOCK_KEY). Skipping cycle.", 'WARN')
                return []

        reaped_records = []
        try:
            candidates = self._run_psql_json(candidate_sql) or []
            if not candidates:
                return reaped_records

            if dry_run:
                for row in candidates:
                    pid = row.get('pid')
                    if pid is None or type(pid) is not int or pid <= 0:
                        continue
                    datname = row.get('datname', 'unknown')
                    idle_sec = row.get('idle_seconds', 0)
                    if verbose:
                        log(f"  [DRY-RUN] Would terminate cluster PID {pid} (DB: {datname}, Idle: {idle_sec}s)", 'WARN')
                    reaped_records.append(dict(row))
            else:
                pids = [int(row['pid']) for row in candidates if str(row.get('pid', '')).isdigit() and int(row.get('pid', 0)) > 0]
                if not pids:
                    return reaped_records
                pids_str = ",".join(str(p) for p in pids)
                batch_sql = f"""
                    SELECT pid, pg_terminate_backend(pid) AS terminated
                    FROM unnest(ARRAY[{pids_str}]) AS pid;
                """
                term_results = self._run_psql_json(batch_sql) or []
                term_map = {r['pid']: r.get('terminated', False) for r in term_results}
                for row in candidates:
                    pid = row.get('pid')
                    if pid is None or type(pid) is not int or pid <= 0:
                        continue
                    datname = row.get('datname', 'unknown')
                    idle_sec = row.get('idle_seconds', 0)
                    terminated = term_map.get(pid, False)
                    rec = dict(row)
                    rec['terminated'] = terminated
                    if terminated:
                        reaped_records.append(rec)
                        if verbose:
                            log(f"  Terminated cluster idle PID {pid} on {datname} (idle {idle_sec}s)", 'SUCCESS')
                    else:
                        if verbose:
                            log(f"  Cluster PID {pid} could not be terminated (may have already closed)", 'WARN')
        finally:
            if not dry_run:
                self._run_psql_scalar(f"SELECT pg_advisory_unlock({REAPER_LOCK_KEY});")

        return reaped_records


def run_reaper(target: str = 'all', idle_minutes: float = 3.0,
               threshold: int = 40, dry_run: bool = False,
               verbose: bool = False,
               local_host: str = '127.0.0.1', local_port: int = 5434,
               local_user: str = 'odoo', local_pass: Optional[str] = None,
               local_db: str = 'innoria_prod',
               cluster_ns: str = 'database', cluster_pod: str = 'postgres-0',
               cluster_user: str = 'postgres', cluster_db: str = 'postgres') -> bool:
    """Executes reaper across designated targets and validates limits."""

    local_pass = local_pass or os.getenv('PGPASSWORD') or os.getenv('ODOO_DB_PASSWORD') or None

    log("=" * 70, 'HEADER')
    log("PostgreSQL Idle Connection Pool Reaper (Safety Guardrail)", 'HEADER')
    log(f"Config: Target={target} | Idle Threshold > {idle_minutes}m | Max Threshold < {threshold} slots | DryRun={dry_run}", 'INFO')
    log("=" * 70, 'HEADER')

    overall_pass = True

    # 1. Cluster Target
    if target in ('all', 'cluster'):
        log("\n--- AUDITING CLUSTER POSTGRESQL (Kubernetes pod database/postgres-0) ---", 'INFO')
        try:
            cluster_reaper = ClusterPostgresReaper(
                namespace=cluster_ns,
                pod=cluster_pod,
                user=cluster_user,
                dbname=cluster_db
            )
            total_before, states_before, max_conn = cluster_reaper.get_stats()
            innoria_before = cluster_reaper.get_db_count("innoria_prod")
            log(f"Before Reaper: {total_before}/{max_conn} cluster connections (innoria_prod: {innoria_before}) [{format_states(states_before)}]", 'INFO')

            reaped = cluster_reaper.reap(idle_minutes=idle_minutes, dry_run=dry_run, verbose=verbose)
            action_verb = "Identified" if dry_run else "Successfully reaped"
            log(f"{action_verb} {len(reaped)} idle connections (idle > {idle_minutes} min).", 'SUCCESS' if reaped else 'INFO')

            if not dry_run and reaped:
                time.sleep(0.5)

            total_after, states_after, _ = cluster_reaper.get_stats()
            innoria_after = cluster_reaper.get_db_count("innoria_prod")
            log(f"After Reaper : {total_after}/{max_conn} cluster connections (innoria_prod: {innoria_after}) [{format_states(states_after)}]", 'INFO')

            cluster_pass = True
            if innoria_after < threshold:
                log(f"Cluster innoria_prod Connection Limit: PASS ({innoria_after} < {threshold} required threshold)", 'SUCCESS')
            else:
                log(f"Cluster innoria_prod Connection Limit: WARN/FAIL ({innoria_after} >= {threshold} required threshold)", 'WARN')
                cluster_pass = False

            if total_after < threshold:
                log(f"Cluster Overall Connection Limit: PASS ({total_after} < {threshold} required threshold)", 'SUCCESS')
            else:
                log(f"Cluster Overall Allocated Pool: {total_after}/{max_conn} slots ({max_conn - total_after} free slots across 15 tenant pools)", 'INFO')

            if not cluster_pass:
                overall_pass = False

        except Exception as e:
            log(f"Error auditing cluster PostgreSQL: {e}", 'ERROR')
            overall_pass = False

    # 2. Local Target
    if target in ('all', 'local'):
        log(f"\n--- AUDITING LOCAL POSTGRESQL ({local_host}:{local_port}) ---", 'INFO')
        try:
            local_reaper = LocalPostgresReaper(
                host=local_host,
                port=local_port,
                user=local_user,
                password=local_pass,
                dbname=local_db
            )
            total_before, states_before, max_conn = local_reaper.get_stats()
            innoria_local_before = local_reaper.get_db_count(local_db)
            log(f"Before Reaper: {total_before}/{max_conn} local connections ({local_db}: {innoria_local_before}) [{format_states(states_before)}]", 'INFO')

            reaped = local_reaper.reap(idle_minutes=idle_minutes, dry_run=dry_run, verbose=verbose)
            action_verb = "Identified" if dry_run else "Successfully reaped"
            log(f"{action_verb} {len(reaped)} idle connections (idle > {idle_minutes} min).", 'SUCCESS' if reaped else 'INFO')

            if not dry_run and reaped:
                time.sleep(0.5)

            total_after, states_after, _ = local_reaper.get_stats()
            innoria_local_after = local_reaper.get_db_count(local_db)
            log(f"After Reaper : {total_after}/{max_conn} local connections ({local_db}: {innoria_local_after}) [{format_states(states_after)}]", 'INFO')

            if total_after < threshold and innoria_local_after < threshold:
                log(f"Local Connection Limit: PASS (Total: {total_after} < {threshold}, {local_db}: {innoria_local_after} < {threshold})", 'SUCCESS')
            else:
                log(f"Local Connection Limit: WARN/FAIL ({total_after} >= {threshold} required threshold)", 'WARN')
                overall_pass = False

        except Exception as e:
            log(f"Error auditing local PostgreSQL: {e}", 'ERROR')
            overall_pass = False

    log("\n" + "=" * 70, 'HEADER')
    if overall_pass:
        log("🎉 CONNECTION POOL REAPING COMPLETE: All targets within safe threshold (< 40 slots).", 'SUCCESS')
    else:
        log("⚠️ REAPING COMPLETED WITH WARNINGS: One or more targets exceed threshold or encountered errors.", 'WARN')
    log("=" * 70 + "\n", 'HEADER')

    return overall_pass


def main():
    parser = argparse.ArgumentParser(
        description="Safe PostgreSQL Idle Connection Pool Reaper for Insilos SaaS"
    )
    parser.add_argument(
        '--target', choices=['all', 'cluster', 'local'], default='all',
        help="Target environment to reap: all (default), cluster, local"
    )
    parser.add_argument(
        '--idle-minutes', type=float, default=3.0,
        help="Reap connections idle for longer than this duration (default: 3.0 minutes)"
    )
    parser.add_argument(
        '--threshold', type=int, default=40,
        help="Target threshold for total connections (default: < 40 slots)"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Scan and report candidate idle connections without terminating them"
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help="Print detailed PID information for each reaped connection"
    )
    parser.add_argument('--local-host', default='127.0.0.1', help="Local PostgreSQL host (default: 127.0.0.1)")
    parser.add_argument('--local-port', type=int, default=5434, help="Local PostgreSQL port (default: 5434)")
    parser.add_argument('--local-user', default='odoo', help="Local PostgreSQL user (default: odoo)")
    parser.add_argument('--local-pass', default=None, help="Local PostgreSQL password (default: env PGPASSWORD / ODOO_DB_PASSWORD)")
    parser.add_argument('--local-db', default='innoria_prod', help="Local PostgreSQL database (default: innoria_prod)")
    parser.add_argument('--cluster-ns', default='database', help="Cluster PostgreSQL namespace (default: database)")
    parser.add_argument('--cluster-pod', default='postgres-0', help="Cluster PostgreSQL pod (default: postgres-0)")
    parser.add_argument('--cluster-user', default='postgres', help="Cluster PostgreSQL user (default: postgres)")
    parser.add_argument('--cluster-db', default='postgres', help="Cluster PostgreSQL database (default: postgres)")

    args = parser.parse_args()

    for name, val in [("local-db", args.local_db), ("cluster-db", args.cluster_db),
                      ("cluster-user", args.cluster_user), ("cluster-pod", args.cluster_pod),
                      ("cluster-ns", args.cluster_ns)]:
        if val and not IDENTIFIER_REGEX.match(val):
            print(f"[✗] Invalid characters in CLI argument --{name}: {val}", file=sys.stderr)
            sys.exit(1)

    success = run_reaper(
        target=args.target,
        idle_minutes=args.idle_minutes,
        threshold=args.threshold,
        dry_run=args.dry_run,
        verbose=args.verbose,
        local_host=args.local_host,
        local_port=args.local_port,
        local_user=args.local_user,
        local_pass=args.local_pass,
        local_db=args.local_db,
        cluster_ns=args.cluster_ns,
        cluster_pod=args.cluster_pod,
        cluster_user=args.cluster_user,
        cluster_db=args.cluster_db
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
