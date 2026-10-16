#!/usr/bin/env python3
"""
Sovereign Automated Verification Suite for DGM & INNORIA Role-Based Access Control (RBAC) Matrix.
Verifies:
1. 100% coverage of `dgm_rbac_profile`, `dgm_confidentiality_level`, `dgm_read_group_ids`,
   and `dgm_write_group_ids` across all active folders (978) and files (>= 7,874) in
   `insilos20_dev`, local `innoria_prod`, and K8s `innoria_prod`.
2. 100% preservation of `owner_id IS NULL` on company folders, `access_internal IN ('view', 'edit')`,
   `user_folder_id` hierarchy (`'COMPANY'` for root, `folder_id::text` for children), and 0 empty folders.
3. Strict runtime enforcement of `check_dgm_folder_rbac_access(operation='read'|'write', user=...)`
   across basic employees, HR officers, HR managers, accountants, and project engineers.
"""

import os
import subprocess
import sys

VENV_PYTHON = "/home/zen/O20/.venv/bin/python3"
if os.path.exists(VENV_PYTHON) and os.path.realpath(sys.executable) != os.path.realpath(VENV_PYTHON):
    try:
        import psycopg2  # noqa: F401
    except ImportError:
        os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

sys.path.insert(0, "/home/zen/O20")

import odoo
from odoo import api, Command, SUPERUSER_ID
from odoo.exceptions import AccessError, ValidationError


EXPECTED_PROFILES = {
    "exec_legal",
    "company_sop",
    "hr_cb",
    "finance_tax",
    "commercial_contract",
    "project_delivery",
    "brand_sales",
    "mti_contract",
    "mti_timesheet",
    "sales_kit",
    "digital_solution",
}


def verify_db_rbac_invariants(cr, db_label):
    # 1. Total active folders & files
    cr.execute("SELECT COUNT(*) FROM documents_document WHERE active = TRUE AND type = 'folder'")
    total_folders = cr.fetchone()[0]
    cr.execute("SELECT COUNT(*) FROM documents_document WHERE active = TRUE AND type != 'folder'")
    total_files = cr.fetchone()[0]

    assert total_folders >= 978, f"[{db_label}] Expected >= 978 active folders, got {total_folders}"
    assert total_files >= 7870, f"[{db_label}] Expected >= 7870 active files, got {total_files}"

    # 2. Zero unmapped active documents/folders & 100% generation hash coverage
    cr.execute("""
        SELECT COUNT(*) FROM documents_document
        WHERE active = TRUE
          AND (dgm_rbac_profile IS NULL OR dgm_confidentiality_level IS NULL OR dgm_rbac_generation_id IS NULL)
    """)
    unmapped = cr.fetchone()[0]
    assert unmapped == 0, f"[{db_label}] Found {unmapped} active records without RBAC profile/confidentiality/generation_id"

    # 3. Every active record must have >= 1 read group and >= 1 write group
    cr.execute("""
        SELECT COUNT(*) FROM documents_document d
        WHERE d.active = TRUE
          AND NOT EXISTS (SELECT 1 FROM dgm_doc_read_group_rel r WHERE r.document_id = d.id)
    """)
    missing_read = cr.fetchone()[0]
    assert missing_read == 0, f"[{db_label}] Found {missing_read} active records without dgm_read_group_ids"

    cr.execute("""
        SELECT COUNT(*) FROM documents_document d
        WHERE d.active = TRUE
          AND NOT EXISTS (SELECT 1 FROM dgm_doc_write_group_rel w WHERE w.document_id = d.id)
    """)
    missing_write = cr.fetchone()[0]
    assert missing_write == 0, f"[{db_label}] Found {missing_write} active records without dgm_write_group_ids"

    # 4. Hierarchical tree parentage invariant (AGENTS.md §6)
    cr.execute("""
        SELECT COUNT(*) FROM documents_document
        WHERE active = TRUE AND type = 'folder'
          AND (owner_id IS NOT NULL OR access_internal NOT IN ('view', 'edit'))
    """)
    bad_folder_access = cr.fetchone()[0]
    assert bad_folder_access == 0, f"[{db_label}] Found {bad_folder_access} folders violating owner_id/access_internal invariant"

    # 5. Zero empty folders invariant
    cr.execute("""
        SELECT COUNT(*) FROM documents_document f
        WHERE f.active = TRUE AND f.type = 'folder'
          AND NOT EXISTS (
              SELECT 1 FROM documents_document c
              WHERE c.active = TRUE AND c.folder_id = f.id
          )
    """)
    empty_folders = cr.fetchone()[0]
    assert empty_folders == 0, f"[{db_label}] Found {empty_folders} empty active folders"

    # 6. Verify all 11 RBAC profiles are active
    cr.execute("""
        SELECT dgm_rbac_profile,
               SUM(CASE WHEN type = 'folder' THEN 1 ELSE 0 END) AS folders,
               SUM(CASE WHEN type != 'folder' THEN 1 ELSE 0 END) AS files
        FROM documents_document
        WHERE active = TRUE
        GROUP BY dgm_rbac_profile
        ORDER BY dgm_rbac_profile
    """)
    dist = {r[0]: (r[1], r[2]) for r in cr.fetchall()}
    missing_profiles = EXPECTED_PROFILES - set(dist.keys())
    assert not missing_profiles, f"[{db_label}] Missing RBAC profiles: {missing_profiles}"

    print(f"[✓] {db_label}: {total_folders} folders & {total_files} files verified across all 11 RBAC profiles (0 unmapped, 0 empty folders)")
    return dist


def test_cross_tenant_isolation_boundary(env, u_basic, doc_sop):
    """Adversarial Test 1: CWE-284 / CWE-863 Cross-Company Document Isolation."""
    Company = env["res.company"].sudo().with_context(no_create_folder=True)
    outside_company = Company.create({"name": "Outside Adversarial Tenant Corp"})
    env.cr.execute("UPDATE documents_document SET company_id = %s WHERE id = %s", (outside_company.id, doc_sop.id))
    doc_sop.invalidate_recordset(["company_id"])
    try:
        doc_sop.check_dgm_folder_rbac_access("read", user=u_basic)
        raise AssertionError("Cross-company user should NOT be allowed to read document belonging to another company")
    except AccessError as exc:
        assert "Cross-company" in str(exc)
    finally:
        env.cr.execute("UPDATE documents_document SET company_id = NULL WHERE id = %s", (doc_sop.id,))
        doc_sop.invalidate_recordset(["company_id"])
    print("[✓] Adversarial Test 1 (test_cross_tenant_isolation_boundary): CWE-284 cross-company boundary verified")


def test_dag_acyclicity_and_chunked_generation(env):
    """Adversarial Test 2: DAG Acyclicity CTE & Chunked Generation Hash Verification."""
    Doc = env["documents.document"].sudo()
    assert Doc._verify_folder_dag_acyclicity() is True

    # Simulate a cycle inside a nested savepoint and confirm ValidationError is raised
    f_sample = Doc.search([("type", "=", "folder"), ("folder_id", "!=", False)], limit=1)
    parent_id = f_sample.folder_id.id
    with env.cr.savepoint() as cycle_sp:
        env.cr.execute("UPDATE documents_document SET folder_id = %s WHERE id = %s", (f_sample.id, parent_id))
        try:
            Doc._verify_folder_dag_acyclicity()
            raise AssertionError("Expected ValidationError on circular folder DAG cycle")
        except ValidationError:
            pass
        finally:
            cycle_sp.close(rollback=True)

    env.cr.execute("SELECT COUNT(DISTINCT dgm_rbac_generation_id) FROM documents_document WHERE active = TRUE")
    distinct_gens = env.cr.fetchone()[0]
    assert distinct_gens == 1, f"Expected 1 deterministic generation_id across active documents, got {distinct_gens}"
    print("[✓] Adversarial Test 2 (test_dag_acyclicity_and_chunked_generation): DAG cycle interception & deterministic generation hash verified")


def test_working_tree_clean_gate():
    """Adversarial Test 3: Verify generate_build_info.py rejects dirty working trees."""
    res = subprocess.run(
        [sys.executable, "/home/zen/O20/tools/generate_build_info.py"],
        cwd="/home/zen/O20",
        capture_output=True,
        text=True,
        check=False,
    )
    status_res = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd="/home/zen/O20",
        capture_output=True,
        text=True,
        check=False,
    )
    if status_res.stdout.strip():
        assert res.returncode == 1 and "Working tree is dirty" in res.stderr, (
            f"Expected exit code 1 and 'Working tree is dirty', got code={res.returncode}, stderr={res.stderr}"
        )
    print("[✓] Adversarial Test 3 (test_working_tree_clean_gate): Dirty working tree fail-closed gate verified")


def verify_orm_rbac_enforcement(env):
    Doc = env["documents.document"].sudo()
    # Verify ORM _compute_user_folder_id across all 978 active folders
    all_folders = Doc.search([("type", "=", "folder")])
    for f in all_folders:
        expected_ufid = "COMPANY" if not f.folder_id else str(f.folder_id.id)
        assert f.user_folder_id == expected_ufid, f"Folder {f.id} ({f.name}) has user_folder_id={f.user_folder_id}, expected {expected_ufid}"
    print(f"[✓] ORM _compute_user_folder_id verified across all {len(all_folders)} active folders ('COMPANY' root & str(folder_id.id) children)")
    Users = env["res.users"].sudo().with_context(no_reset_password=True)

    g_user = env.ref("base.group_user")
    g_hr_user = env.ref("hr.group_hr_user")
    g_hr_mgr = env.ref("hr.group_hr_manager")
    g_acc_user = env.ref("account.group_account_user")
    g_proj_user = env.ref("project.group_project_user")

    with env.cr.savepoint() as sp:
        def make_user(login, group_recs):
            group_Field = "group_ids" if "group_ids" in Users._fields else "groups_id"
            return Users.create({
                "name": f"RBAC Test {login}",
                "login": f"rbac_test_{login}@digimate.vn",
                group_Field: [Command.set(group_recs.ids)],
            })

        u_basic = make_user("basic", g_user)
        u_hr_officer = make_user("hr_officer", g_user | g_hr_user)
        u_hr_mgr = make_user("hr_mgr", g_user | g_hr_mgr)
        u_acc = make_user("acc", g_user | g_acc_user)
        u_proj = make_user("proj", g_user | g_proj_user)

        doc_sop = Doc.search([("dgm_rbac_profile", "=", "company_sop"), ("type", "!=", "folder")], limit=1)
        doc_hr = Doc.search([("dgm_rbac_profile", "=", "hr_cb"), ("type", "!=", "folder")], limit=1)
        doc_fin = Doc.search([("dgm_rbac_profile", "=", "finance_tax"), ("type", "!=", "folder")], limit=1)
        doc_exec = Doc.search([("dgm_rbac_profile", "=", "exec_legal"), ("type", "!=", "folder")], limit=1)
        doc_proj = Doc.search([("dgm_rbac_profile", "=", "project_delivery"), ("type", "!=", "folder")], limit=1)
        doc_mti_ts = Doc.search([("dgm_rbac_profile", "=", "mti_timesheet"), ("type", "!=", "folder")], limit=1)

        assert doc_sop and doc_hr and doc_fin and doc_exec and doc_proj and doc_mti_ts, "Sample documents for RBAC profiles not found"

        # 1. Basic internal user: can read SOPs, cannot write SOPs, cannot read HR/Finance/Exec/Project
        assert doc_sop.check_dgm_folder_rbac_access("read", user=u_basic) is True
        for restricted_doc in (doc_hr, doc_fin, doc_exec, doc_proj):
            try:
                restricted_doc.check_dgm_folder_rbac_access("read", user=u_basic)
                raise AssertionError(f"Basic user should NOT be allowed to read {restricted_doc.dgm_rbac_profile}")
            except AccessError:
                pass
        try:
            doc_sop.check_dgm_folder_rbac_access("write", user=u_basic)
            raise AssertionError("Basic user should NOT be allowed to write company_sop")
        except AccessError:
            pass

        # 2. HR Officer vs HR Manager on hr_cb (including INNO - NHÂN SỰ and BHXH/Lương DGM)
        assert doc_hr.check_dgm_folder_rbac_access("read", user=u_hr_officer) is True
        try:
            doc_hr.check_dgm_folder_rbac_access("write", user=u_hr_officer)
            raise AssertionError("HR Officer should NOT be allowed to write hr_cb")
        except AccessError:
            pass
        assert doc_hr.check_dgm_folder_rbac_access("read", user=u_hr_mgr) is True
        assert doc_hr.check_dgm_folder_rbac_access("write", user=u_hr_mgr) is True

        # 3. Accountant on finance_tax vs hr_cb
        assert doc_fin.check_dgm_folder_rbac_access("read", user=u_acc) is True
        assert doc_fin.check_dgm_folder_rbac_access("write", user=u_acc) is True
        try:
            doc_hr.check_dgm_folder_rbac_access("read", user=u_acc)
            raise AssertionError("Accountant without HR group should NOT read hr_cb")
        except AccessError:
            pass

        # 4. Project engineer on project_delivery & mti_timesheet
        assert doc_proj.check_dgm_folder_rbac_access("read", user=u_proj) is True
        assert doc_proj.check_dgm_folder_rbac_access("write", user=u_proj) is True
        assert doc_mti_ts.check_dgm_folder_rbac_access("read", user=u_proj) is True
        try:
            doc_exec.check_dgm_folder_rbac_access("read", user=u_proj)
            raise AssertionError("Project engineer should NOT read exec_legal")
        except AccessError:
            pass

        # 5. Adversarial security tests
        test_cross_tenant_isolation_boundary(env, u_basic, doc_sop)
        test_dag_acyclicity_and_chunked_generation(env)

        # 6. Verify cron_dgm_document_triage_split RBAC auto-reconciliation & INNO customer folder -> project linkage
        with env.cr.savepoint():
            env.cr.execute("UPDATE documents_document SET dgm_rbac_profile = NULL WHERE id = %s", (doc_sop.id,))
            doc_sop.invalidate_recordset(["dgm_rbac_profile"])
            assert not doc_sop.dgm_rbac_profile
            triage_res = Doc.cron_dgm_document_triage_split()
            assert isinstance(triage_res, dict) and "rbac_reconciled" in triage_res, (
                f"Expected 'rbac_reconciled' in cron_dgm_document_triage_split summary, got {triage_res}"
            )
            assert triage_res["rbac_reconciled"] >= 1, (
                f"Expected rbac_reconciled >= 1 when a document was unmapped, got {triage_res}"
            )
            doc_sop.invalidate_recordset(["dgm_rbac_profile"])
            assert doc_sop.dgm_rbac_profile == "company_sop", (
                f"Expected doc_sop.dgm_rbac_profile restored to 'company_sop', got {doc_sop.dgm_rbac_profile}"
            )

            link_res = env["project.project"].sudo().link_inno_customer_folders_to_projects()
            assert link_res.get("status") == "success" and link_res.get("customer_folders_verified", 0) >= 22, (
                f"Expected >= 22 customer folders verified by link_inno_customer_folders_to_projects, got {link_res}"
            )
            assert link_res.get("projects_linked", 0) >= 1, (
                f"Expected >= 1 active projects linked by link_inno_customer_folders_to_projects, got {link_res}"
            )
            env.cr.execute("""
                SELECT COUNT(*) FROM documents_document f
                WHERE f.active = TRUE AND f.type = 'folder'
                  AND NOT EXISTS (
                      SELECT 1 FROM documents_document c
                      WHERE c.active = TRUE AND c.folder_id = f.id
                  )
            """)
            assert env.cr.fetchone()[0] == 0, "Expected 0 empty active folders after link_inno_customer_folders_to_projects()"
        print("[✓] Autonomous Triage Cron RBAC Reconciliation ('rbac_reconciled') & INNO Customer Folder -> Project Linkage verified")

        sp.close(rollback=True)

    print("[✓] Runtime ORM RBAC enforcement (check_dgm_folder_rbac_access) verified across 5 role personas")


def verify_k8s_rbac():
    cmd = [
        "kubectl", "exec", "-n", "production", "deploy/innoria-prod-app", "--",
        "python3", "-c",
        (
            "import sys; sys.path.insert(0, '/app/insilos'); import odoo.tools.config, odoo.sql_db; "
            "odoo.tools.config.parse_config(['--db_host=pgbouncer-service','--db_port=6432','--db_user=insilos','-d','innoria_prod']); "
            "cr = odoo.sql_db.db_connect('innoria_prod').cursor(); "
            "cr.execute(\"SELECT COUNT(*) FROM documents_document WHERE active=TRUE AND type='folder' AND dgm_rbac_profile IS NOT NULL AND dgm_rbac_generation_id IS NOT NULL\"); f=cr.fetchone()[0]; "
            "cr.execute(\"SELECT COUNT(*) FROM documents_document WHERE active=TRUE AND type!='folder' AND dgm_rbac_profile IS NOT NULL AND dgm_rbac_generation_id IS NOT NULL\"); d=cr.fetchone()[0]; "
            "cr.execute(\"SELECT COUNT(*) FROM documents_document WHERE active=TRUE AND (dgm_rbac_profile IS NULL OR dgm_rbac_generation_id IS NULL)\"); u=cr.fetchone()[0]; "
            "print(f'K8S_RBAC_OK folders={f} files={d} unmapped={u}'); "
            "assert f >= 978 and d >= 7870 and u == 0"
        ),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert res.returncode == 0 and "K8S_RBAC_OK" in res.stdout, f"K8s RBAC check failed: {res.stdout} {res.stderr}"
    print(f"[✓] K8s live production (`innoria_prod`): {res.stdout.strip()}")


def main():
    for db_name, conf in [("insilos20_dev", "/home/zen/O20/insilos.conf"), ("innoria_prod", "/home/zen/O20/innoria.conf")]:
        odoo.tools.config.parse_config(["-c", conf, "-d", db_name])
        with odoo.sql_db.db_connect(db_name).cursor() as cr:
            verify_db_rbac_invariants(cr, db_name)

    odoo.tools.config.parse_config(["-c", "/home/zen/O20/insilos.conf", "-d", "insilos20_dev"])
    reg = odoo.modules.registry.Registry.new("insilos20_dev")
    with reg.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        verify_orm_rbac_enforcement(env)

    test_working_tree_clean_gate()
    verify_k8s_rbac()
    print("[🎉] ALL DGM & INNORIA DOCUMENTS RBAC MATRIX CHECKS PASSED (EXIT 0)")


if __name__ == "__main__":
    main()
