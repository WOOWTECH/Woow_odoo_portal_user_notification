# Copyright 2026 WoowTech
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""Never next to the previous engine: it serves the same addresses.

From R1 until the cutover, woow_subscription runs next to the previous
engine, whose portal pages answer the old addresses until it is uninstalled.
Were both modules installed, the old pages would be
taken over. The manifest's ``excludes`` makes Odoo refuse the combination,
in either order, before anything is written. The previous engine is not on
the test addons path: a stand-in module record (name and state only) plays its part here.
"""
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

MODULE = 'woow_subscription_legacy_urls'
OLD_ENGINE = 'sh_subscription'


@tagged('post_install', '-at_install', MODULE)
class TestPreviousEngineExcluded(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Module = cls.env['ir.module.module']
        cls.module = Module.search([('name', '=', MODULE)])
        cls.old_engine = Module.search([('name', '=', OLD_ENGINE)]) or Module.create({
            'name': OLD_ENGINE,
            'shortdesc': "Previous subscription engine (stand-in)",
            'state': 'uninstalled',
        })

    def assertRefusedAsIncompatible(self, module):
        with self.assertRaises(UserError) as refused:
            module.button_install()
        self.assertIn('incompatible', str(refused.exception))

    def test_declared_in_the_manifest(self):
        self.assertEqual(self.module.state, 'installed')
        self.assertEqual(self.module.exclusion_ids.mapped('name'), [OLD_ENGINE])
        self.assertFalse(self.module.auto_install, "installed by hand, once the previous engine is gone")

    def test_refused_while_the_previous_engine_is_installed(self):
        self.old_engine.state = 'installed'
        self.module.state = 'uninstalled'
        self.assertRefusedAsIncompatible(self.module)
        self.assertEqual(self.module.state, 'uninstalled', "refused before anything changed")

    def test_previous_engine_cannot_come_back_next_to_it(self):
        self.assertRefusedAsIncompatible(self.old_engine)
        self.assertEqual(self.old_engine.state, 'uninstalled')
