from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    freight_cost = fields.Float(string="Freight Cost")

    transhipment = fields.Selection([
        ('allowed', 'Allowed'),
        ('not_allowed', 'Not allowed')
    ], string="Transhipment", default='allowed')

    partial_shipment = fields.Selection([
        ('allowed', 'Allowed'),
        ('not_allowed', 'Not allowed')
    ], string="Partial Shipment", default='not_allowed')

    port_of_loading = fields.Char(string="Port of Loading")
    port_of_discharge = fields.Char(string="Port of Discharge")
    # Add a field for the shipping address (delivery address)
    partner_shipping_id = fields.Many2one(
        'res.partner',
        string="Adresse de livraison",
        domain="[('type', '=', 'delivery')]",
        help="Select the delivery address for this order."
    )

    # Add a field for the billing address
    partner_invoice_id = fields.Many2one(
        'res.partner',
        string="Adresse de facturation",
        domain="[('type', '=', 'invoice')]",
        help="Select the billing address for this order."
    )

    # Onchange method to set the delivery and invoice address when partner_id is changed
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            # Automatically select the first 'delivery' address for shipping
            self.partner_shipping_id = self.partner_id.child_ids.filtered(lambda c: c.type == 'delivery')[:1]
            # Automatically select the first 'invoice' address for billing
            self.partner_invoice_id = self.partner_id.child_ids.filtered(lambda c: c.type == 'invoice')[:1]