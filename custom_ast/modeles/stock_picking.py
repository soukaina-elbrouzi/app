from odoo import models, fields, api
from odoo.exceptions import UserError



class StockPicking(models.Model):
    _inherit = 'stock.picking'


    is_lot_change_requested = fields.Boolean(string="Demande d'autorisation", default=False)
    is_lot_change_authorized = fields.Boolean(string="Autorisation accordée", default=False)


    @api.model
    def _check_lot_change_authorization(self):
        if self.x_studio_related_field_72t_1igbig3g8 and not self.is_lot_change_authorized:
            raise UserError("Vous n'avez pas le droit d'imprimer ce rapport. Une autorisation pour le changement de lot est nécessaire.")



    def request_lot_change_authorization(self):
        """Demander l'autorisation pour le changement de lot."""
        if self.is_lot_change_requested:
            raise UserError("Une demande d'autorisation a déjà été effectuée.")
        self.is_lot_change_requested = True
        self.message_post(body="Une demande d'autorisation pour le changement de lot a été effectuée.")

    def authorize_lot_change(self):
        """Autoriser le changement de lot."""
        if not self.is_lot_change_requested:
            raise UserError("Aucune demande d'autorisation n'a été effectuée.")
        self.is_lot_change_authorized = True
        self.message_post(body="L'autorisation pour le changement de lot a été accordée.")

    def print_bon_prelevement(self):
        self._check_lot_change_authorization()
        return self.env.ref('custom_ast.action_report_bon_de_prelevement').report_action(self)

