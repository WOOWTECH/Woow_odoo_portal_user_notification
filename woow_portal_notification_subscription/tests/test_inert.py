# Copyright 2026 WoowTech
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""The bridge brings nothing and writes nothing, also while the engine is dormant.

R1 installs woow_subscription held dormant next to the billing system still
in use, and this bridge comes along through auto_install. The bridge must
not create a notification or write anything then.
"""
from contextlib import contextmanager
from unittest.mock import patch

from odoo import Command
from odoo.sql_db import Cursor
from odoo.tests import TransactionCase, tagged
from odoo.tools import SQL

MODULE = 'woow_portal_notification_subscription'
SUBSCRIPTION_LIST = '/woow#/billing/subscriptions'
DORMANT_PARAM = 'woow_subscription.dormant'
#: Statements that change the database.
WRITES = ('INSERT', 'UPDATE', 'DELETE', 'MERGE', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'COPY')


@contextmanager
def recorded_statements():
    """Collect the SQL of every statement run on a database cursor meanwhile."""
    statements = []
    execute = Cursor.execute

    def recording_execute(cr, query, params=None, log_exceptions=True):
        statements.append(query.code if isinstance(query, SQL) else str(query))
        return execute(cr, query, params, log_exceptions)

    with patch.object(Cursor, 'execute', recording_execute):
        yield statements


@tagged('post_install', '-at_install', MODULE)
class TestBridgeIsInert(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)

        def user(login, *groups):
            return Users.create({
                'name': login, 'login': login, 'email': login + '@example.invalid',
                'groups_id': [Command.set([cls.env.ref(group).id for group in groups])],
            })

        cls.customer = user('wpns_inert_customer', 'base.group_portal')
        cls.stranger = user('wpns_inert_stranger', 'base.group_portal')
        cls.accountant = user('wpns_inert_accountant', 'base.group_user', 'account.group_account_invoice')
        plan = cls.env['woow.subscription.plan'].create({'name': 'Wpns inert plan', 'price': 120.0})
        cls.env['product.product'].create({
            'name': 'Wpns inert service', 'type': 'service',
            'woow_is_subscription': True, 'woow_subscription_plan_id': plan.id,
        })
        # Made while the engine is live: a dormant engine creates no subscription.
        Subscription = cls.env['woow.subscription']
        cls.subscription = Subscription.create_for_plan(cls.customer.partner_id, plan)
        cls.accountant_subscription = Subscription.create_for_plan(cls.accountant.partner_id, plan)

    def test_installed_together_with_the_engine(self):
        """auto_install on both dependencies: installing the engine where the centre is installed brings it."""
        module = self.env['ir.module.module'].search([('name', '=', MODULE)])
        self.assertEqual(module.state, 'installed')
        self.assertTrue(module.auto_install)
        self.assertEqual(sorted(module.dependencies_id.mapped('name')),
                         ['woow_portal_notification', 'woow_subscription'])
        self.assertTrue(all(module.dependencies_id.mapped('auto_install_required')))

    def test_no_data_of_its_own(self):
        """Only the reference Odoo keeps for any module extending a model: no record, field or view."""
        data = self.env['ir.model.data'].search([('module', '=', MODULE)])
        self.assertEqual(data.mapped(lambda xmlid: (xmlid.model, xmlid.name)),
                         [('ir.model', 'model_woow_subscription')])

    def test_dormant_engine_nothing_is_notified_or_written(self):
        self.env['ir.config_parameter'].sudo().set_param(DORMANT_PARAM, '1')
        Subscription = self.env['woow.subscription']
        self.assertTrue(Subscription._is_dormant())
        counts = {model: self.env[model].sudo().search_count([])
                  for model in ('mail.message', 'mail.notification', 'mail.mail')}
        self.env.flush_all()
        with recorded_statements() as statements:
            customer_url = self.subscription.with_user(self.customer)._wpn_portal_url()
            stranger_url = self.subscription.with_user(self.stranger)._wpn_portal_url()
            Reader = Subscription.with_user(self.accountant)
            own = Reader.search(Reader._wpn_portal_record_domain())
            self.env.flush_all()
        self.assertEqual(customer_url, SUBSCRIPTION_LIST)
        self.assertFalse(stranger_url, "not their subscription: no page, the centre shows the message")
        self.assertEqual(own, self.accountant_subscription)
        self.assertTrue(statements, "the recorder saw the reads")
        self.assertEqual([sql for sql in statements if sql.lstrip().upper().startswith(WRITES)], [])
        self.assertEqual({model: self.env[model].sudo().search_count([]) for model in counts}, counts)
