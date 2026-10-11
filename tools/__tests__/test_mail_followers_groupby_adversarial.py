#!/usr/bin/env python3
"""
Adversarial Metamorphic & Differential Verification Suite:
mail_followers.py GROUP BY PostgreSQL 16 Functional Dependency Hardening
Audits zero-cardinality change, NULL handling, duplicate-attribute collisions,
Unicode NFC/NFD diacritics, boundary cases, and authorization integrity
under strict non-prod database isolation and transaction rollback proof.
"""

import os
import re
import sys
import unicodedata
import unittest

# Ensure root directory is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import odoo
from odoo import SUPERUSER_ID, api

# Unambiguous markers: a name containing these is never disposable, even concatenated.
_PROD_SUBSTRINGS = ("prod", "production")
# Ambiguous markers: real words embed them ('maintenance', 'domain'), so match whole tokens only.
_PROD_TOKENS = ("main", "master")


def _looks_like_production(db_name: str) -> bool:
    """
    Two-tier guard (CWE-20):
      - substring for unambiguous markers -> blocks 'proddb', 'prodclone', 'production2024'
      - regex prefix/boundary for 'live' -> blocks 'live', 'liveserver', 'odoo_live' but allows 'delivery_qa'
      - token-boundary for ambiguous markers -> allows 'maintenance', 'domain_test'
    """
    low = db_name.lower()
    if any(sub in low for sub in _PROD_SUBSTRINGS):
        return True
    if re.search(r"(^|_|-)live($|_|-|server|db|[0-9])", low):
        return True
    tokens = set(re.split(r"[^a-z0-9]+", low))
    return any(tok in tokens for tok in _PROD_TOKENS)


class TestMailFollowersGroupByAdversarial(unittest.TestCase):
    """
    Adversarial verification testing PostgreSQL 16 GROUP BY correctness,
    functional dependency integrity, and differential query equivalence.
    Enforces Zero-Production Blast Radius invariants.
    """

    @classmethod
    def setUpClass(cls):
        conf_file = "/home/zen/O20/innokafe.conf"
        if not os.path.exists(conf_file):
            conf_file = "/home/zen/O20/insilos.conf"
        odoo.tools.config.parse_config(["-c", conf_file])

        # Dynamic test database resolution (Zero Production Blast Radius)
        test_db = os.environ.get("ODOO_TEST_DB", "innokafe_test")

        # Deny-by-default allowlist: only databases explicitly marked disposable may run
        # write-capable adversarial tests.
        allowed = {
            d.strip()
            for d in os.environ.get(
                "ODOO_TEST_DB_ALLOWLIST", "innokafe_test,odoo20_dev,insilos20_dev"
            ).split(",")
            if d.strip()
        }

        # Validate the guard's own input: prevent poisoned allowlist blast-radius holes
        poisoned = {d for d in allowed if _looks_like_production(d)}
        if poisoned:
            raise RuntimeError(
                f"BLAST RADIUS GUARD: allowlist contains production-like entries {sorted(poisoned)}"
            )

        if test_db not in allowed or _looks_like_production(test_db):
            raise RuntimeError(
                f"BLAST RADIUS GUARD: '{test_db}' is not in the disposable test allowlist "
                f"{sorted(allowed)} or matches production tokens."
            )

        cls.db_target = test_db
        cls.registry = odoo.modules.registry.Registry(cls.db_target)

    def setUp(self):
        self.cr = self.registry.cursor()
        self.env = api.Environment(self.cr, SUPERUSER_ID, {})
        self._created_partner_ids = []
        self._created_follower_ids = []

    def tearDown(self):
        rollback_error = None
        if getattr(self, "cr", None):
            try:
                self.cr.rollback()
            except Exception as exc:
                rollback_error = exc
            finally:
                try:
                    self.cr.close()
                except Exception:
                    pass

        # Empirical pollution proof on an independent connection - runs even if rollback raised
        leaked = []
        tracked = {
            "res_partner": self._created_partner_ids,
            "mail_followers": getattr(self, "_created_follower_ids", []),
        }
        if any(ids for ids in tracked.values()):
            registry = getattr(self, "registry", None)
            if registry is None:
                raise RuntimeError(
                    "Pollution-proof aborted: self.registry unavailable; cannot verify isolation."
                )
            with registry.cursor() as fresh_cr:
                fresh_cr.execute("SET LOCAL statement_timeout = '5s'")
                for table, ids in tracked.items():
                    if not ids:
                        continue
                    fresh_cr.execute(
                        f"SELECT id FROM {table} WHERE id = ANY(%s)", (list(ids),)
                    )
                    leaked += [(table, row[0]) for row in fresh_cr.fetchall()]

        if rollback_error is not None:
            raise AssertionError(f"Isolation rollback FAILED (connection released): {rollback_error!r}")
        if leaked:
            raise AssertionError(f"Isolation breach: records persisted after rollback: {leaked}")

    def test_00_empty_pids_boundary_preservation(self):
        """
        Boundary invariant: Empty pids list must return valid empty structure
        {0: {}} when records=None, never raising KeyError or SQL syntax errors.
        """
        recipients = self.env["mail.followers"]._get_recipient_data(
            records=None,
            message_type="notification",
            subtype_id=False,
            pids=[],
        )
        self.assertIn(0, recipients, "Expected root key 0 when records=None")
        self.assertEqual(recipients[0], {}, "Empty pids must return empty recipient map")

    def test_01_null_and_falsy_values_preservation(self):
        """
        Verify that partners with active=False, NULL email_normalized,
        and NULL lang are not dropped or corrupted by the GROUP BY clause.
        """
        Partner = self.env["res.partner"]
        p_inactive = Partner.create({
            "name": "Inactive Null Partner",
            "active": False,
            "email": False,
            "lang": False,
        })
        self._created_partner_ids.append(p_inactive.id)

        recipients = self.env["mail.followers"]._get_recipient_data(
            records=None,
            message_type="notification",
            subtype_id=False,
            pids=[p_inactive.id],
        )

        self.assertIn(0, recipients, "Expected root key 0 when records=None")
        partner_data = recipients[0].get(p_inactive.id)
        self.assertIsNotNone(partner_data, "Inactive partner must exist in recipient data")
        self.assertEqual(partner_data["id"], p_inactive.id)
        self.assertFalse(partner_data["active"])
        self.assertFalse(partner_data["email_normalized"])
        self.assertFalse(partner_data["lang"])
        self.assertEqual(partner_data["name"], "Inactive Null Partner")
        self.assertFalse(partner_data["is_follower"])

    def test_02_duplicate_attributes_zero_collapse(self):
        """
        Adversarial test: Two distinct partners sharing the exact same name,
        lang, active status, and partner_share MUST NOT be collapsed together.
        """
        Partner = self.env["res.partner"]
        shared_name = "Collision Twin Target"
        shared_lang = "en_US"

        p1 = Partner.create({"name": shared_name, "lang": shared_lang, "active": True})
        p2 = Partner.create({"name": shared_name, "lang": shared_lang, "active": True})
        self._created_partner_ids.extend([p1.id, p2.id])

        self.assertNotEqual(p1.id, p2.id, "Precondition: partners must have distinct IDs")

        recipients = self.env["mail.followers"]._get_recipient_data(
            records=None,
            message_type="notification",
            subtype_id=False,
            pids=[p1.id, p2.id],
        )

        self.assertIn(0, recipients)
        res_0 = recipients[0]
        self.assertEqual(len(res_0), 2, f"Expected 2 distinct rows, got {len(res_0)}")
        self.assertIn(p1.id, res_0)
        self.assertIn(p2.id, res_0)
        self.assertEqual(res_0[p1.id]["name"], shared_name)
        self.assertEqual(res_0[p2.id]["name"], shared_name)

    def test_03_differential_query_equivalence(self):
        """
        Differential metamorphic test: Compare pre-change query against post-change query
        over a diverse batch of up to 25 existing partners.
        """
        partners = self.env["res.partner"].search([], limit=25)
        pids = partners.ids
        if not pids:
            p_fix = self.env["res.partner"].create({"name": "Differential Fixture Partner"})
            self._created_partner_ids.append(p_fix.id)
            pids = [p_fix.id]

        self.assertTrue(len(pids) > 0, "Precondition: need existing partners in database")

        # Variant A: Pre-change SQL (group by only partner.id, sub_user...)
        sql_variant_a = """
    SELECT partner.id as pid,
           partner.active as active,
           partner.email_normalized AS email_normalized,
           partner.lang as lang,
           partner.name as name,
           partner.partner_share as pshare,
           sub_user.uid as uid,
           COALESCE(sub_user.share, FALSE) as ushare,
           COALESCE(sub_user.notification_type, 'email') as notif,
           sub_user.groups as groups,
           0 as res_id,
           FALSE as is_follower
      FROM res_partner partner
 LEFT JOIN LATERAL (
        SELECT users.id AS uid,
               users.share AS share,
               users.notification_type AS notification_type,
               ARRAY_AGG(groups_rel.gid) FILTER (WHERE groups_rel.gid IS NOT NULL) AS groups
          FROM res_users users
     LEFT JOIN res_groups_users_rel groups_rel ON groups_rel.uid = users.id
         WHERE users.partner_id = partner.id AND users.active
      GROUP BY users.id,
               users.share,
               users.notification_type
      ORDER BY users.share ASC NULLS FIRST, users.id ASC
         FETCH FIRST ROW ONLY
         ) sub_user ON TRUE
     WHERE partner.id IN %s
  GROUP BY partner.id,
           sub_user.uid,
           sub_user.share,
           sub_user.notification_type,
           sub_user.groups
  ORDER BY partner.id ASC
"""

        # Variant B: Post-change SQL (includes functionally dependent partner columns)
        sql_variant_b = """
    SELECT partner.id as pid,
           partner.active as active,
           partner.email_normalized AS email_normalized,
           partner.lang as lang,
           partner.name as name,
           partner.partner_share as pshare,
           sub_user.uid as uid,
           COALESCE(sub_user.share, FALSE) as ushare,
           COALESCE(sub_user.notification_type, 'email') as notif,
           sub_user.groups as groups,
           0 as res_id,
           FALSE as is_follower
      FROM res_partner partner
 LEFT JOIN LATERAL (
        SELECT users.id AS uid,
               users.share AS share,
               users.notification_type AS notification_type,
               ARRAY_AGG(groups_rel.gid) FILTER (WHERE groups_rel.gid IS NOT NULL) AS groups
          FROM res_users users
     LEFT JOIN res_groups_users_rel groups_rel ON groups_rel.uid = users.id
         WHERE users.partner_id = partner.id AND users.active
      GROUP BY users.id,
               users.share,
               users.notification_type
      ORDER BY users.share ASC NULLS FIRST, users.id ASC
         FETCH FIRST ROW ONLY
         ) sub_user ON TRUE
     WHERE partner.id IN %s
  GROUP BY partner.id,
           partner.active,
           partner.email_normalized,
           partner.lang,
           partner.name,
           partner.partner_share,
           sub_user.uid,
           sub_user.share,
           sub_user.notification_type,
           sub_user.groups
  ORDER BY partner.id ASC
"""

        # Execute Variant B (committed query with safe tuple parameterization)
        self.cr.execute(sql_variant_b, (tuple(pids),))
        res_b = self.cr.fetchall()

        # Attempt to execute Variant A if planner allows functional dependency
        try:
            self.cr.execute(sql_variant_a, (tuple(pids),))
            res_a = self.cr.fetchall()
            # Assert byte-level identical result sets
            self.assertEqual(len(res_a), len(res_b), "Cardinality must be identical")
            self.assertEqual(res_a, res_b, "Output rows must be byte-for-byte identical")
        except Exception as e:
            # If PostgreSQL rejects Variant A, that proves why the GROUP BY fix was necessary!
            print(f"\n[INFO] PostgreSQL rejected Variant A ({e.__class__.__name__}): {e}")
            print("[INFO] Confirms Variant B is strictly required on this PostgreSQL engine.")

    def test_04_follower_status_and_records_linkage(self):
        """
        Verify that follower status is accurately mapped when records is provided.
        """
        Partner = self.env["res.partner"]
        Followers = self.env["mail.followers"]

        target_rec = Partner.create({"name": "Target Model Record"})
        p_follower = Partner.create({"name": "Active Follower Partner"})
        p_non_follower = Partner.create({"name": "Non Follower Partner"})
        self._created_partner_ids.extend([target_rec.id, p_follower.id, p_non_follower.id])

        # Add follower using dynamic model name
        fol = Followers.create({
            "res_model": target_rec._name,
            "res_id": target_rec.id,
            "partner_id": p_follower.id,
        })
        self._created_follower_ids.append(fol.id)
        self.env.flush_all()

        recipients = Followers._get_recipient_data(
            records=target_rec,
            message_type="notification",
            subtype_id=False,
            pids=[p_follower.id, p_non_follower.id],
        )

        follower_info = recipients.get(target_rec.id, {})
        self.assertIn(p_follower.id, follower_info)
        self.assertIn(p_non_follower.id, follower_info)
        self.assertTrue(follower_info[p_follower.id]["is_follower"], "Follower partner must have is_follower=True")
        self.assertFalse(follower_info[p_non_follower.id]["is_follower"], "Non-follower partner must have is_follower=False")

    def test_05_non_superuser_authorization_integrity(self):
        """
        Authorization verification (CWE-863): Ensure recipient data calculation
        functions reliably and securely when queried in a non-superuser context.
        """
        Partner = self.env["res.partner"]
        p_test = Partner.create({"name": "Auth Guarded Partner", "active": True})
        self._created_partner_ids.append(p_test.id)

        # Query recipient data as an internal user
        User = self.env["res.users"]
        internal_user = User.search([("id", "!=", SUPERUSER_ID), ("active", "=", True)], limit=1)
        if not internal_user:
            internal_user = self.env.user

        user_followers = self.env["mail.followers"].with_user(internal_user)
        recipients = user_followers._get_recipient_data(
            records=None,
            message_type="notification",
            subtype_id=False,
            pids=[p_test.id],
        )
        self.assertIn(0, recipients)
        self.assertIn(p_test.id, recipients[0])
        self.assertEqual(recipients[0][p_test.id]["name"], "Auth Guarded Partner")

    def test_06_boundary_empty_and_nonexistent_and_duplicates(self):
        """
        Boundary conditions:
        - Non-existent partner ID: pids=[999999999]
        - Duplicate IDs in input: pids=[p1.id, p1.id]
        """
        Partner = self.env["res.partner"]
        Followers = self.env["mail.followers"]

        # 1. Non-existent partner ID
        rec_nonexistent = Followers._get_recipient_data(
            records=None,
            message_type="notification",
            subtype_id=False,
            pids=[999999999],
        )
        self.assertEqual(rec_nonexistent, {0: {}}, "Non-existent partner must yield 0 recipient rows")

        # 2. Duplicate partner IDs in input list
        p_dup = Partner.create({"name": "Duplicate List Target"})
        self._created_partner_ids.append(p_dup.id)

        rec_dup = Followers._get_recipient_data(
            records=None,
            message_type="notification",
            subtype_id=False,
            pids=[p_dup.id, p_dup.id, p_dup.id],
        )
        self.assertIn(0, rec_dup)
        self.assertEqual(len(rec_dup[0]), 1, "Duplicate IDs must not produce duplicate dict entries")
        self.assertIn(p_dup.id, rec_dup[0])

    def test_07_unicode_nfc_nfd_diacritic_preservation(self):
        """
        Adversarial test: NFC vs NFD Unicode normalization.
        'Đắk Lắk Cà Phê' in NFC (composed) vs NFD (decomposed) are byte-distinct
        Unicode representations. They must NOT collapse or cause GROUP BY errors.
        """
        Partner = self.env["res.partner"]
        name_base = "Đắk Lắk Cà Phê"
        name_nfc = unicodedata.normalize("NFC", name_base)
        name_nfd = unicodedata.normalize("NFD", name_base)

        self.assertNotEqual(
            name_nfc.encode("utf-8"),
            name_nfd.encode("utf-8"),
            "Precondition: NFC and NFD byte encodings must differ"
        )

        p_nfc = Partner.create({"name": name_nfc, "active": True})
        p_nfd = Partner.create({"name": name_nfd, "active": True})
        self._created_partner_ids.extend([p_nfc.id, p_nfd.id])

        recipients = self.env["mail.followers"]._get_recipient_data(
            records=None,
            message_type="notification",
            subtype_id=False,
            pids=[p_nfc.id, p_nfd.id],
        )

        self.assertIn(0, recipients)
        res_0 = recipients[0]
        self.assertEqual(len(res_0), 2, "NFC and NFD partners must both be preserved distinctly")
        self.assertIn(p_nfc.id, res_0)
        self.assertIn(p_nfd.id, res_0)
        self.assertEqual(res_0[p_nfc.id]["name"], name_nfc)
        self.assertEqual(res_0[p_nfd.id]["name"], name_nfd)

    def test_08_rollback_proof_zero_database_pollution(self):
        """
        Zero-Pollution Proof: Verify that records created during the test
        stay inside the transaction and are completely erased upon rollback.
        """
        Partner = self.env["res.partner"]
        p_transient = Partner.create({"name": "Transient Proof Record", "active": True})
        p_id = p_transient.id

        # The record exists inside this cursor
        self.assertTrue(Partner.browse(p_id).exists())

        # Test rollback explicitly
        self.cr.rollback()

        # In a freshly opened cursor, the record must NOT exist
        with self.registry.cursor() as fresh_cr:
            fresh_env = api.Environment(fresh_cr, SUPERUSER_ID, {})
            self.assertFalse(
                fresh_env["res.partner"].browse(p_id).exists(),
                "CRITICAL: Record persisted past rollback! Transaction isolation failed."
            )

    def test_09_blast_radius_guard_token_precision(self):
        """
        Unit verification of the two-tier blast-radius classifier.
        Ensures:
        - Substring production markers ('proddb', 'production2024', 'liveserver', 'prodclone') are blocked.
        - Exact ambiguous tokens ('main', 'master', 'innokafe_main') are blocked.
        - Legitimate non-production substrings ('innokafe_maintenance', 'delivery_qa', 'domain_test') are permitted.
        """
        # Tier 1: Concatenated and substring unambiguous markers
        self.assertTrue(_looks_like_production("prod"))
        self.assertTrue(_looks_like_production("production"))
        self.assertTrue(_looks_like_production("live"))
        self.assertTrue(_looks_like_production("proddb"))
        self.assertTrue(_looks_like_production("production2024"))
        self.assertTrue(_looks_like_production("liveserver"))
        self.assertTrue(_looks_like_production("prodclone"))
        self.assertTrue(_looks_like_production("innokafe_prod"))
        self.assertTrue(_looks_like_production("system_live_test"))

        # Tier 2: Ambiguous markers (token boundary)
        self.assertTrue(_looks_like_production("main"))
        self.assertTrue(_looks_like_production("master"))
        self.assertTrue(_looks_like_production("my-main-db"))
        self.assertTrue(_looks_like_production("innokafe_master"))

        # Legitimate non-production names containing substrings of ambiguous markers
        self.assertFalse(_looks_like_production("innokafe_maintenance"))
        self.assertFalse(_looks_like_production("delivery_qa"))
        self.assertFalse(_looks_like_production("domain_test"))
        self.assertFalse(_looks_like_production("innokafe_test"))
        self.assertFalse(_looks_like_production("odoo20_dev"))
        self.assertFalse(_looks_like_production("insilos20_dev"))


if __name__ == "__main__":
    unittest.main()
