from odoo import models, fields, api

class AnalyticAccountGroup(models.Model):
    _name = 'analytic.account.group'
    _description = 'Analytic Account Group'

    name = fields.Char(string='Name', required=True)
    analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        'analytic_account_group_rel',
        'group_id',
        'account_id',
        string='Analytic Accounts'
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_group_id = fields.Many2one(
        'analytic.account.group',
        string='Kostenplaats',
        compute='_compute_analytic_group',
        store=True,
        index=True
    )

    @api.depends('analytic_distribution')
    def _compute_analytic_group(self):
        AnalyticAccount = self.env['account.analytic.account']
        for line in self:
            if line.analytic_distribution:
                ids = [int(id) for id in line.analytic_distribution.keys() if id.isdigit()]
                accounts = AnalyticAccount.browse(ids)
                group_name = ', '.join(accounts.mapped('name'))

                # Find or create the group
                group = self.env['analytic.account.group'].search([('name', '=', group_name)], limit=1)
                if not group:
                    group = self.env['analytic.account.group'].create({
                        'name': group_name,
                        'analytic_account_ids': [(6, 0, ids)]
                    })

                line.analytic_group_id = group.id
            else:
                line.analytic_group_id = False