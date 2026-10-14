import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

TRUTHY = ('1', 'true', 'yes', 'on')


class Al2cAgentUsage(models.Model):
    """Daily action counter per autonomous agent (budget enforcement)."""
    _name = 'al2c.agent.usage'
    _description = 'AL2C Agent Daily Usage'
    _order = 'date desc, agent_name'

    agent_name = fields.Char(required=True, index=True)
    date = fields.Date(required=True, index=True, default=fields.Date.context_today)
    count = fields.Integer(default=0)

    _agent_date_unique = models.Constraint(
        'unique (agent_name, date)',
        'One usage counter per agent and day.',
    )


class Al2cAutonomyGuard(models.AbstractModel):
    """Shared guard for every autonomous agent action.

    Reads the global kill-switch ``al2c.autonomy_enabled`` and the per-agent
    daily budget ``al2c.agent_daily_budget`` (number of actions per agent per
    day, ``0`` = unlimited).
    """
    _name = 'al2c.autonomy.guard'
    _description = 'AL2C Autonomy Guard'

    @api.model
    def _al2c_autonomy_enabled(self):
        value = self.env['ir.config_parameter'].sudo().get_param('al2c.autonomy_enabled', 'False')
        return str(value).strip().lower() in TRUTHY

    @api.model
    def _dgm_autonomy_enabled(self):
        """Checks both global and DGM-specific autonomous operation master switches (Fail-Closed)."""
        ICP = self.env['ir.config_parameter'].sudo()
        al2c_val = str(ICP.get_param('al2c.autonomy_enabled', 'False')).strip().lower()
        dgm_val = str(ICP.get_param('dgm.autonomy_enabled', 'False')).strip().lower()
        return (al2c_val in TRUTHY) and (dgm_val in TRUTHY)

    @api.model
    def _al2c_daily_budget(self):
        value = self.env['ir.config_parameter'].sudo().get_param('al2c.agent_daily_budget', '0')
        try:
            return max(int(float(value)), 0)
        except (TypeError, ValueError):
            return 0

    @api.model
    def _al2c_check_autonomy(self, agent_name, cost=1):
        """Raise UserError when autonomy is disabled or the agent exhausted its
        daily budget; otherwise consume ``cost`` units of budget."""
        agent_name = agent_name or 'unknown-agent'
        if not self._al2c_autonomy_enabled():
            _logger.info("AL2C: action of agent %s refused (autonomy disabled)", agent_name)
            raise UserError(self.env._(
                "Autonomous actions are disabled (system parameter al2c.autonomy_enabled). "
                "Agent %(agent)s cannot perform this action; a human must take over.",
                agent=agent_name,
            ))
        budget = self._al2c_daily_budget()
        Usage = self.env['al2c.agent.usage'].sudo()
        today = fields.Date.context_today(self)
        usage = Usage.search([('agent_name', '=', agent_name), ('date', '=', today)], limit=1)
        used = usage.count if usage else 0
        if budget and used + cost > budget:
            raise UserError(self.env._(
                "Agent %(agent)s reached its daily budget (%(used)s/%(budget)s actions).",
                agent=agent_name, used=used, budget=budget,
            ))
        if usage:
            usage.count = used + cost
        else:
            Usage.create({'agent_name': agent_name, 'date': today, 'count': cost})
        return True

    @api.model
    def _al2c_check_method_allowed(self, model_name, method_name):
        """
        AL2C-GOV-204 Method-Level Deny-List:
        Autonomous agents are strictly blocked from invoking high-risk sensitive methods:
        - hr.payslip: action_payslip_done (Human HR/CFO release ceiling)
        - account.move: button_draft (cannot unpost audited fiscal invoices)
        - account.move: action_cancel_einvoice (cannot cancel certified tax invoices without CFO)
        """
        if self.env.user.has_group('insilos_al2c.group_al2c_agent') and not self.env.su:
            denied_methods = {
                'hr.payslip': ['action_payslip_done', 'action_validate'],
                'account.move': ['button_draft', 'action_cancel_einvoice'],
                'sale.order': ['action_approve_deal_desk'],
                'al2c.dispute': ['action_resolve_dispute', 'action_cancel_dispute'],
            }
            if method_name in denied_methods.get(model_name, []):
                from odoo.exceptions import AccessError
                raise AccessError(self.env._(
                    "Autonomous agent %(user)s is denied from calling %(method)s on %(model)s (AL2C-GOV-204 Segregation of Duties).",
                    user=self.env.user.name, method=method_name, model=model_name
                ))
        return True

