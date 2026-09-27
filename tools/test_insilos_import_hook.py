#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification Suite for Insilos PEP 451 Import Hook Adapter
==========================================================
Validates that:
1. 'insilos' namespace is transparently mapped to 'odoo'.
2. 'from insilos import models, fields, api, http, tools' works identically to 'odoo'.
3. 'from insilos.addons import crm, account' resolves smoothly without upstream modification.
4. Deep imports ('from insilos.models import Model', 'from insilos.fields import Char', etc.) work.
5. Classes, fields, decorators, and singletons have exact object identity (is) with odoo.
6. Custom model definitions inheriting from insilos.models.Model function cleanly.
"""

import sys
import unittest


class TestInsilosImportHook(unittest.TestCase):

    def test_01_top_level_module_import(self):
        """Verify import insilos resolves and aliases to odoo."""
        import insilos
        import odoo

        self.assertIs(insilos, odoo, "insilos must alias directly to odoo module object")
        self.assertIn("insilos", sys.modules, "sys.modules must contain 'insilos'")

    def test_02_core_namespaces_import(self):
        """Verify importing models, fields, api, http, tools from insilos."""
        from insilos import models, fields, api, http, tools
        import odoo.models
        import odoo.fields
        import odoo.api
        import odoo.http
        import odoo.tools

        self.assertIs(models, odoo.models, "insilos.models must be odoo.models")
        self.assertIs(fields, odoo.fields, "insilos.fields must be odoo.fields")
        self.assertIs(api, odoo.api, "insilos.api must be odoo.api")
        self.assertIs(http, odoo.http, "insilos.http must be odoo.http")
        self.assertIs(tools, odoo.tools, "insilos.tools must be odoo.tools")

    def test_03_addons_namespace_import(self):
        """Verify importing addons such as crm and account from insilos.addons."""
        from insilos.addons import crm, account
        import odoo.addons.crm
        import odoo.addons.account

        self.assertIs(crm, odoo.addons.crm, "insilos.addons.crm must be odoo.addons.crm")
        self.assertIs(account, odoo.addons.account, "insilos.addons.account must be odoo.addons.account")

        # Test aliased import syntax
        import insilos.addons.crm as crm_alias
        self.assertIs(crm_alias, crm, "aliased import must match direct import")

    def test_04_deep_imports(self):
        """Verify deep member imports from submodules."""
        from insilos.models import Model, TransientModel, AbstractModel
        from insilos.fields import Char, Integer, Boolean, Many2one, Many2many, One2many
        from insilos.api import model, constrains, depends, onchange
        from insilos.http import request, route, Controller, Response
        from insilos.tools import config
        from insilos import SUPERUSER_ID, _, Command

        import odoo.models
        import odoo.fields
        import odoo.api
        import odoo.http
        import odoo.tools
        import odoo

        self.assertIs(Model, odoo.models.Model)
        self.assertIs(TransientModel, odoo.models.TransientModel)
        self.assertIs(AbstractModel, odoo.models.AbstractModel)

        self.assertIs(Char, odoo.fields.Char)
        self.assertIs(Integer, odoo.fields.Integer)
        self.assertIs(Boolean, odoo.fields.Boolean)
        self.assertIs(Many2one, odoo.fields.Many2one)
        self.assertIs(Many2many, odoo.fields.Many2many)
        self.assertIs(One2many, odoo.fields.One2many)

        self.assertIs(model, odoo.api.model)
        self.assertIs(constrains, odoo.api.constrains)
        self.assertIs(depends, odoo.api.depends)
        self.assertIs(onchange, odoo.api.onchange)

        self.assertIs(route, odoo.http.route)
        self.assertIs(Controller, odoo.http.Controller)
        self.assertIs(Response, odoo.http.Response)

        self.assertIs(config, odoo.tools.config)
        self.assertEqual(SUPERUSER_ID, odoo.SUPERUSER_ID)
        self.assertIs(_, odoo._)
        self.assertIs(Command, odoo.Command)

    def test_05_dynamic_attribute_access(self):
        """Verify that accessing insilos.<attr> dynamically resolves cleanly."""
        import insilos

        self.assertTrue(hasattr(insilos, "models"))
        self.assertTrue(hasattr(insilos, "fields"))
        self.assertTrue(hasattr(insilos, "api"))
        self.assertTrue(hasattr(insilos, "http"))
        self.assertTrue(hasattr(insilos, "tools"))
        self.assertTrue(hasattr(insilos, "addons"))

    def test_06_custom_model_subclassing(self):
        """Verify that a Python class can subclass insilos.models.Model and declare fields."""
        from insilos import models, fields

        class DummyInsilosPartner(models.Model):
            _register = False
            _name = "test.insilos.partner"
            _description = "Insilos Adapter Test Model"

            display_name = fields.Char(string="Display Name")
            active = fields.Boolean(string="Active", default=True)

        self.assertTrue(issubclass(DummyInsilosPartner, models.Model))
        import odoo.models
        self.assertTrue(issubclass(DummyInsilosPartner, odoo.models.Model))

        # Test model with explicit _module attribute
        class RegisteredInsilosModel(models.Model):
            _module = "insilos_adapter"
            _name = "test.insilos.registered"

        self.assertTrue(issubclass(RegisteredInsilosModel, models.Model))

    def test_07_invalid_import_raises_import_error(self):
        """Verify that attempting to import non-existent modules raises ImportError."""
        with self.assertRaises((ImportError, ModuleNotFoundError)):
            import insilos.non_existent_submodule_xyz_12345

        with self.assertRaises((ImportError, ModuleNotFoundError)):
            from insilos.addons import non_existent_addon_xyz_12345

    def test_08_deep_submodule_sys_modules_registration(self):
        """Verify deep submodules are properly bound in sys.modules and to their parent packages."""
        import insilos.addons.crm.models
        import odoo.addons.crm.models

        self.assertIn("insilos.addons.crm.models", sys.modules)
        self.assertIs(sys.modules["insilos.addons.crm.models"], sys.modules["odoo.addons.crm.models"])
        self.assertIs(insilos.addons.crm.models, odoo.addons.crm.models)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInsilosImportHook)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
