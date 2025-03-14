from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    date_de_fabrication = fields.Date(string='Date de fabrication')




class StockLot(models.Model):
    _inherit = 'stock.lot'  # Inherit from stock.lot instead of stock.production.lot

    date_de_fabrication = fields.Date(string='Date de fabrication')

# class StockProductionLot(models.Model):
#     _inherit = 'stock.production.lot'
#
#     date_de_fabrication = fields.Date(string='Date de fabrication')