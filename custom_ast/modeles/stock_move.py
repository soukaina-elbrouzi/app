from odoo import models, fields, api


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    total_cost = fields.Float(string="Coût Total", help="Le coût total de tous les mouvements dans le lot")

    ratio = fields.Float(string="Ratio", compute='_compute_ratio', store=True, help="Le ratio entre le coût total et la valeur de la facture")

    @api.depends('move_ids.product_uom_qty', 'move_ids.price_unit')
    def _compute_total_cost(self):
        """ Calculer le coût total basé sur les mouvements (moves) dans le lot """
        for batch in self:
            total_cost = 0.0
            for move in batch.move_ids:
                # Calcul du coût total (prix unitaire * quantité) pour chaque mouvement
                total_cost += move.product_uom_qty * move.product_id.standard_price
            batch.total_cost = total_cost

    @api.depends('total_cost', 'move_ids.product_uom_qty', 'move_ids.price_unit')
    def _compute_ratio(self):
        """ Calculer le ratio basé sur le coût total et la valeur de la facture """
        for batch in self:
            total_value = sum(move.product_uom_qty * move.price_unit for move in batch.move_ids)

            # Vérifier que la valeur totale n'est pas nulle pour éviter une division par zéro
            if total_value > 0:
                batch.ratio = batch.total_cost / total_value
            else:
                batch.ratio = 0

    @api.onchange('total_cost')
    def distribute_cost(self):
        """ Distribuer le coût total sur les mouvements selon le ratio """
        for batch in self:
            if batch.ratio > 0:
                for move in batch.move_ids:
                    # Calculer le coût distribué pour chaque mouvement
                    move.distributed_cost = batch.ratio * move.product_uom_qty * move.price_unit

