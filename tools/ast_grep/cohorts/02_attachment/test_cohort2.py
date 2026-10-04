#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
INSILOS SOVEREIGN HARD FORK — COHORT 2 COMPREHENSIVE VERIFICATION SUITE
Domain: ir.attachment -> system.attachment
IBM Enterprise Document / Digital Asset Foundation
================================================================================
"""
import base64
import hashlib
import os
import sys
from pathlib import Path

# Add repo to sys.path
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

def run_tests(env):
    print("=" * 80)
    print("🧪 RUNNING COHORT 2: ir.attachment -> system.attachment VERIFICATION SUITE")
    print("=" * 80)

    # 1. ORM Registry Aliasing
    print("\n[Step 1] Verifying ORM Registry Model Aliasing...")
    att_sys = env['system.attachment']
    att_leg = env['ir.attachment']
    assert att_sys == att_leg, f"Registry alias mismatch: {att_sys} != {att_leg}"
    assert att_leg._name == 'system.attachment', f"Legacy alias _name is not system.attachment: {att_leg._name}"
    assert att_leg._table == 'system_attachment', f"Legacy alias _table is not system_attachment: {att_leg._table}"
    print(f"  [✓] env['ir.attachment'] successfully resolves to '{att_sys._name}' (table: {att_sys._table})")

    # 2. Write-Through via Legacy Alias
    print("\n[Step 2] Testing Write-Through via Legacy Interface (env['ir.attachment'].create)...")
    payload = b"INSILOS_SOVEREIGN_DIGITAL_ASSET_FOUNDATION_2026_COHORT_2_PAYLOAD"
    payload_b64 = base64.b64encode(payload).decode('ascii')
    
    rec = env['ir.attachment'].create({
        'name': 'insilos_cohort2_spec.bin',
        'datas': payload_b64,
        'mimetype': 'application/octet-stream',
        'type': 'binary',
    })
    print(f"  [✓] Created record ID={rec.id}, Model={rec._name}, Checksum={rec.checksum}")

    # 3. Read Verification via Canonical Model
    print("\n[Step 3] Reading Binary Data via Sovereign Model (env['system.attachment'].browse)...")
    fetched = env['system.attachment'].browse(rec.id)
    assert fetched.exists(), "Attachment record could not be found in system.attachment!"
    assert fetched.name == 'insilos_cohort2_spec.bin', f"Name mismatch: {fetched.name}"
    assert bytes(fetched.raw) == payload, "Raw binary payload does not match source bytes!"
    print(f"  [✓] Binary parity verified: {len(bytes(fetched.raw))} bytes match byte-for-byte.")

    # 4. Filestore Disk Persistence Verification
    print("\n[Step 4] Verifying Filestore Physical Disk Integrity (~/.local/share/Odoo/filestore)...")
    if fetched.store_fname:
        disk_path = fetched._full_path(fetched.store_fname)
        assert os.path.exists(disk_path), f"Disk file not found on filesystem: {disk_path}"
        with open(disk_path, 'rb') as f:
            disk_bytes = f.read()
        assert disk_bytes == payload, "Disk byte content corrupted or mismatched!"
        disk_sha1 = hashlib.sha1(disk_bytes).hexdigest()
        assert disk_sha1 == fetched.checksum, f"Disk SHA1 ({disk_sha1}) != DB checksum ({fetched.checksum})"
        print(f"  [✓] Physical disk file verified: {disk_path}")
        print(f"  [✓] Content-Addressable CAS Checksum (SHA1): {disk_sha1}")
    else:
        print("  [!] Attachment stored in db_datas (filestore bypass configured)")

    # 5. Clean Up
    print("\n[Step 5] Cleaning up test artifact...")
    rec.unlink()
    assert not env['system.attachment'].browse(rec.id).exists(), "Record still exists after unlink!"
    print("  [✓] Test record cleanly removed.")

    print("\n" + "=" * 80)
    print("🎉 ALL COHORT 2 ATTACHMENT SUITE CHECKS PASSED (100% OPERATIONAL)")
    print("=" * 80)

if __name__ == '__main__':
    import insilos
    from insilos import api, SUPERUSER_ID
    from insilos.modules.registry import Registry

    config_file = REPO_ROOT / "insilos.conf"
    db_name = "odoo20_dev"
    insilos.tools.config.parse_config(['-c', str(config_file), '-d', db_name])
    reg = Registry(db_name)
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        run_tests(env)
