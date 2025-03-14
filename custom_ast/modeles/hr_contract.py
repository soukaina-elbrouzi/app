from odoo import models, fields

class HrContract(models.Model):
    _inherit = 'hr.contract'

    prime_responsabilite = fields.Monetary(string="Prime de Responsabilité")
    indemnite_direction = fields.Monetary(string="Indemnité de Direction")
    indemnite_encadrement = fields.Monetary(string="Indemnité d'encadrement")

    indemnite_transport = fields.Monetary(string="Indemnité de Transport")
    indemnite_caisse = fields.Monetary(string="Indemnité de Caisse")
    indemnite_lait = fields.Monetary(string="Indemnité de lait")
    indemnite_panier = fields.Monetary(string="Indemnité de panier")
    indemnite_representation = fields.Monetary(string="Indemnité de Representation")
    prime_salissure = fields.Monetary(string="Prime de salissure")
    prime_tournee = fields.Monetary(string="Prime de tournée")
    
    
    currency_id = fields.Many2one(
        'res.currency', 
        string='Devise', 
        required=True, 
        default=lambda self: self.env.company.currency_id
    )
