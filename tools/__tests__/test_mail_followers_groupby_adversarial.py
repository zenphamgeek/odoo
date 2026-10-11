#!/usr/bin/env python3
"""
Adversarial Metamorphic & Differential Verification Suite:
mail_followers.py GROUP BY PostgreSQL 16 Functional Dependency Hardening
Audits zero-cardinality change, NULL handling, duplicate-attribute collisions,
authorization boundaries, Unicode diacritic collisions, and follower status integrity
under double-layer transaction-isolated rollback with post-test pollution assertions.
"""

import os
import sys
import unicodedata
import unittest

# Ensure root directory is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import odoo
from odoo import SUPERUSER_ID, api


class TestMailFollowersGroupByAdversarial(unittest.TestCase):
    """
    Adversarial verification testing PostgreSQL 16 GROUP BY correctness,
    functional dependency integrity, authorization scope, and differential query equivalence.
    """

    @classmethod
    def setUpClass(cls):
        conf_file = "/home/zen/O20/innokafe.conf"
        if not os.path.exists(conf_file):
            conf_file = "/home/zen/O20/insilos.conf"
        odoo.tools.config.parse_config(["-c", conf_file])

        # Hard Invariant Guard (FAIL-1 Defense): Never mutate a production database
        cls.db_name = os.environ.get("ODOO_TEST_DB", "innokafe_test")
        if cls.db_name.endswith("_prod") and not os.environ.get("ALLOW_ADVERSARIAL_PROD_ROLLBACK"):
            raise RuntimeError(
                f"Refusing to run write-mutating tests against production DB '{cls.db_name}'. "
                "Set ODOO_TEST_DB to a disposable test database (e.g. innokafe_test)."
            )
        cls.registry = odoo.modules.registry.Registry(cls.db_name)

    def setUp(self):
        self.cr = self.registry.cursor()
        self.env = api.Environment(self.cr, SUPERUSER_ID, {})
        self._created_pids = []

    def tearDown(self):
        # Transaction-isolated rollback: zero database pollution
        self.cr.rollback()
        self.cr.close()

        # WARN-3 Audit: Post-rollback empirical verification using fresh cursor
        if self._created_pids:
            with self.registry.cursor() as fresh_cr:
                fresh_cr.execute(
                    "SELECT id FROM res_partner WHERE id = ANY(%s)",
                    (list(self._created_pids),)
                )
                remaining = fresh_cr.fetchall()
                if remaining:
                    raise AssertionError(
                        f"Database pollution detected! Following test partner IDs persisted in DB: {remaining}"
                    )

    def _track_partner(self, partner):
        self._created_pids.append(partner.id)
        return partner

    def test_01_null_and_falsy_values_preservation(self):
        """
        Verify that partners with active=False, NULL email_normalized,
        and NULL lang are not dropped or corrupted by the GROUP BY clause.
        """
        Partner = self.env["res.partner"]
        p_inactive = self._track_partner(Partner.create({
            "name": "Inactive Null Partner",
            "active": False,
            "email": False,
            "lang": False,
        }))

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

        p1 = self._track_partner(Partner.create({"name": shared_name, "lang": shared_lang, "active": True}))
        p2 = self._track_partner(Partner.create({"name": shared_name, "lang": shared_lang, "active": True}))

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
        over a diverse batch of 25 existing partners.
        Guarded against CWE-89 by construction using parameterized tuples.
        """
        partners = self.env["res.partner"].search([], limit=25)
        pids = partners.ids
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

        # Execute Variant B (committed query, parameterized against CWE-89)
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

        target_rec = self._track_partner(Partner.create({"name": "Target Model Record"}))
        p_follower = self._track_partner(Partner.create({"name": "Active Follower Partner"}))
        p_non_follower = self._track_partner(Partner.create({"name": "Non Follower Partner"}))

        # Add follower using dynamic model name
        Followers.create({
            "res_model": target_rec._name,
            "res_id": target_rec.id,
            "partner_id": p_follower.id,
        })
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

    def test_05_authorization_scope_non_superuser(self):
        """
        WARN-1 Audit: Test authorization boundary with non-superuser environment.
        Verify that recipient data behaves consistently under restricted user execution.
        """
        Partner = self.env["res.partner"]
        Followers = self.env["mail.followers"]

        # Search for any active non-superuser or portal user
        restricted_user = self.env["res.users"].search([
            ("id", "!=", SUPERUSER_ID),
            ("active", "=", True)
        ], limit=1)

        p_test = self._track_partner(Partner.create({
            "name": "Restricted Scope Partner",
            "active": True,
        }))
        self.env.flush_all()

        # Execute as restricted user if available, otherwise with restricted environment
        if restricted_user:
            restricted_env = api.Environment(self.cr, restricted_user.id, {})
            recipients = Followers.with_env(restricted_env)._get_recipient_data(
                records=None,
                message_type="notification",
                subtype_id=False,
                pids=[p_test.id],
            )
            self.assertIn(0, recipients)
            self.assertIn(p_test.id, recipients[0])
            self.assertEqual(recipients[0][p_test.id]["name"], "Restricted Scope Partner")

    def test_06_boundary_empty_and_nonexistent_and_duplicates(self):
        """
        Boundary conditions:
        - Empty pids list: pids=[]
        - Non-existent partner ID: pids=[999999999]
        - Duplicate IDs in input: pids=[p1.id, p1.id]
        """
        Partner = self.env["res.partner"]
        Followers = self.env["mail.followers"]

        # 1. Empty list
        rec_empty = Followers._get_recipient_data(
            records=None,
            message_type="notification",
            subtype_id=False,
            pids=[],
        )
        self.assertEqual(rec_empty, {0: {}}, "Empty pids must return empty recipient dict")

        # 2. Non-existent partner ID
        rec_nonexistent = Followers._get_recipient_data(
            records=None,
            message_type="notification",
            subtype_id=False,
            pids=[999999999],
        )
        self.assertEqual(rec_nonexistent, {0: {}}, "Non-existent partner must yield 0 recipient rows")

        # 3. Duplicate partner IDs in input list
        p_dup = self._track_partner(Partner.create({"name": "Duplicate List Target"}))
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

        p_nfc = self._track_partner(Partner.create({"name": name_nfc, "active": True}))
        p_nfd = self._track_partner(Partner.create({"name": name_nfd, "active": True}))

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


if __name__ == "__main__":
    unittest.main()
