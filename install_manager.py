#!/usr/bin/env python3
import ast
import os
import subprocess
import sys
import psycopg2
from collections import defaultdict, deque

enterprise_dir = '/home/zen/O20/enterprise'
community_dir = '/home/zen/O20/addons'
addons_dir = '/home/zen/O20/addons'
conf_path = '/home/zen/O20/insilos.conf'
python_bin = '/home/zen/O20/.venv/bin/python'
insilos_bin = '/home/zen/O20/insilos-bin'

def get_db_installed():
    conn = psycopg2.connect(host='127.0.0.1', port=5434, user='insilos', password='1NN0R1@2026', dbname='odoo20_dev')
    cur = conn.cursor()
    cur.execute("SELECT name, state FROM ir_module_module WHERE state = 'installed';")
    installed = set(r[0] for r in cur.fetchall())
    conn.close()
    return installed

def load_manifests():
    manifests = {}
    for p in [enterprise_dir, community_dir, addons_dir]:
        if os.path.exists(p):
            for d in os.listdir(p):
                mf_path = os.path.join(p, d, '__manifest__.py')
                if os.path.exists(mf_path) and d not in manifests:
                    try:
                        with open(mf_path, 'r', encoding='utf-8') as f:
                            manifests[d] = ast.literal_eval(f.read())
                    except Exception:
                        pass
    return manifests

def get_target_modules(manifests):
    all_modules = [d for d in os.listdir(enterprise_dir) if os.path.exists(os.path.join(enterprise_dir, d, '__manifest__.py'))]
    backlog_mods = set()
    for m in all_modules:
        if m.startswith('test_'):
            backlog_mods.add(m)
        elif 'l10n_' in m:
            if not (m.startswith('l10n_vn') or m.startswith('l10n_us') or m.startswith('l10n_generic')):
                backlog_mods.add(m)
        elif m == 'pos_blackbox_be':
            backlog_mods.add(m)
    return sorted([m for m in all_modules if m not in backlog_mods])

def get_ordered_to_install():
    manifests = load_manifests()
    target_modules = get_target_modules(manifests)
    installed = get_db_installed()
    to_install = [m for m in target_modules if m not in installed]
    
    # Topological sort
    in_degree = defaultdict(int)
    adj = defaultdict(set)
    to_install_set = set(to_install)

    for m in to_install:
        deps = manifests.get(m, {}).get('depends', [])
        for d in deps:
            if d in to_install_set:
                adj[d].add(m)
                in_degree[m] += 1

    queue = deque([m for m in to_install if in_degree[m] == 0])
    ordered = []
    while queue:
        curr = queue.popleft()
        ordered.append(curr)
        for nxt in adj[curr]:
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    remaining = to_install_set - set(ordered)
    if remaining:
        ordered.extend(sorted(list(remaining)))
    return ordered

def run_install(module_names):
    cmd = [python_bin, insilos_bin, '-c', conf_path, '-d', 'odoo20_dev', '-i', ','.join(module_names), '--stop-after-init']
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
    return res.returncode == 0, res.stdout

if __name__ == '__main__':
    ordered = get_ordered_to_install()
    print(f"Modules to install: {len(ordered)}")
    batch_size = 10
    failed = []
    
    for i in range(0, len(ordered), batch_size):
        batch = ordered[i:i+batch_size]
        # Filter already installed if any previous batch pulled them
        installed = get_db_installed()
        batch = [m for m in batch if m not in installed]
        if not batch:
            continue
        print(f"\n--- Installing batch {i//batch_size + 1} ({len(batch)} modules): {batch} ---")
        ok, out = run_install(batch)
        if ok:
            print(f"Batch {i//batch_size + 1} SUCCESS!")
        else:
            print(f"Batch {i//batch_size + 1} FAILED. Falling back to single installs...")
            for m in batch:
                installed = get_db_installed()
                if m in installed:
                    continue
                print(f"  Attempting single install: {m}")
                m_ok, m_out = run_install([m])
                if m_ok:
                    print(f"  SUCCESS: {m}")
                else:
                    print(f"  FAILURE: {m}")
                    print("  Full output snippet:")
                    print("\n".join(m_out.splitlines()[-30:]))
                    failed.append((m, m_out))
            if failed:
                print(f"Recorded {len(failed)} failure(s) so far. Continuing with remaining batches...")

    installed_now = get_db_installed()
    manifests = load_manifests()
    target = get_target_modules(manifests)
    remaining = [m for m in target if m not in installed_now]
    print(f"\nSummary: {len(installed_now)} installed in DB, {len(remaining)} target modules remaining.")
