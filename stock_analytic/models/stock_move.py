# Copyright 2013 Julius Network Solutions
# Copyright 2015 Clear Corp
# Copyright 2016 OpenSynergy Indonesia
# Copyright 2017 ForgeFlow S.L.
# Copyright 2018 Hibou Corp.
# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from collections import defaultdict

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        res = super().button_confirm()
        for order in self:
            # Create a defaultdict to collect analytic distributions
            analytic_distribution = defaultdict(float)
            for line in order.order_line:
                # Assuming line.analytic_distribution is a dictionary
                if line.analytic_distribution:
                    for account_id, distribution in line.analytic_distribution.items():
                        analytic_distribution[account_id] += distribution

            # Assign the merged analytic distribution to the picking
            for picking in order.picking_ids:
                if analytic_distribution:
                    picking.analytic_distribution = dict(analytic_distribution)
        return res


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            # Create a defaultdict to collect analytic distributions
            analytic_distribution = defaultdict(float)
            for line in order.order_line:
                # Assuming line.analytic_distribution is a dictionary
                if line.analytic_distribution:
                    for account_id, distribution in line.analytic_distribution.items():
                        analytic_distribution[account_id] += distribution

            # Assign the merged analytic distribution to the picking
            for picking in order.picking_ids:
                if analytic_distribution:
                    picking.analytic_distribution = dict(analytic_distribution)
        return res

class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move", "analytic.mixin"]

    def _prepare_account_move_line(
        self, qty, cost, credit_account_id, debit_account_id, svl_id, description
    ):
        self.ensure_one()
        res = super()._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, svl_id, description
        )
        if not self.analytic_distribution:
            return res
        for line in res:
            if (
                line[2]["account_id"]
                != self.product_id.categ_id.property_stock_valuation_account_id.id
            ):
                # Add analytic account in debit line
                line[2].update({"analytic_distribution": self.analytic_distribution})
        return res

    def _prepare_procurement_values(self):
        """
        Allows to transmit analytic account from moves to new
        moves through procurement.
        """
        res = super()._prepare_procurement_values()
        if self.analytic_distribution:
            res.update(
                {
                    "analytic_distribution": self.analytic_distribution,
                }
            )
        return res

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """
        We fill in the analytic account when creating the move line from
        the move
        """
        res = super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )
        if self.analytic_distribution:
            res.update({"analytic_distribution": self.analytic_distribution})
        return res

    def _action_done(self, cancel_backorder=False):
        for move in self:
            # Validate analytic distribution only for outgoing moves.
            if move.location_id.usage not in (
                "internal",
                "transit",
            ) or move.location_dest_id.usage in ("internal", "transit"):
                continue
            move._validate_distribution(
                **{
                    "product": move.product_id.id,
                    "business_domain": "stock_move",
                    "company_id": move.company_id.id,
                }
            )
        return super()._action_done(cancel_backorder=cancel_backorder)


class StockMoveLine(models.Model):
    _name = "stock.move.line"
    _inherit = ["stock.move.line", "analytic.mixin"]

    @api.model
    def _prepare_stock_move_vals(self):
        """
        In the case move lines are created manually, we should fill in the
        new move created here with the analytic account if filled in.
        """
        res = super()._prepare_stock_move_vals()
        if self.analytic_distribution:
            res.update({"analytic_distribution": self.analytic_distribution})
        return res