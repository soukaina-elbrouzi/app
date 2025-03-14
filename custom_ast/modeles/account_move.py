from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'


    @api.model_create_multi
    def create(self, vals):
        # Créer la facture en utilisant la méthode standard d'Odoo
        invoice = super(AccountMove, self).create(vals)

        # Vérifier si la facture est liée à une commande de vente
        if invoice.move_type == 'out_invoice' and invoice.invoice_origin:
            sale_order = self.env['sale.order'].search([('name', '=', invoice.invoice_origin)], limit=1)
            if sale_order and sale_order.payment_term_id:
                # Récupérer la condition de paiement depuis la commande de vente
                payment_term = sale_order.payment_term_id.name.lower()

                if payment_term == 'paiement comptant':  # Vérification pour Paiement Comptant
                    total_ht = sum(line.price_subtotal for line in invoice.invoice_line_ids)
                    escompte_percentage = 3

                    # Calculer les valeurs
                    escompte_value = total_ht * (escompte_percentage / 100)
                    total_with_escompte = total_ht - escompte_value

                    # Remplir les champs personnalisés
                    invoice.x_studio_escompte = f"Escompte de {escompte_percentage} %"
                    invoice.x_studio_valeur_escompte = escompte_value
                    invoice.x_studio_total_avec_escompte = total_with_escompte

                elif payment_term == '30 jours':  # Vérification pour 30 jours
                    total_ht = sum(line.price_subtotal for line in invoice.invoice_line_ids)
                    escompte_percentage = 1.5

                    # Calculer les valeurs
                    escompte_value = total_ht * (escompte_percentage / 100)
                    total_with_escompte = total_ht - escompte_value

                    # Remplir les champs personnalisés
                    invoice.x_studio_escompte = f"Escompte de {escompte_percentage} %"
                    invoice.x_studio_valeur_escompte = escompte_value
                    invoice.x_studio_total_avec_escompte = total_with_escompte

        return invoice

    def _compute_tax_totals(self):
        """ Hérite de la méthode d'origine pour ajouter des données personnalisées aux tax_totals. """
        super(AccountMove, self)._compute_tax_totals()
        for move in self:
            if move.is_invoice(include_receipts=True) and move.tax_totals:
                # Ajouter votre propre clé/valeur au dictionnaire tax_totals
                move.tax_totals['x_studio_escompte'] = move.x_studio_escompte
                move.tax_totals['x_studio_total_avec_escompte'] = move.x_studio_total_avec_escompte
                move.tax_totals['x_studio_valeur_escompte'] = move.x_studio_valeur_escompte

    tax_details_html = fields.Html(
        compute='_compute_tax_details_html',
        string="Tax Details",
        sanitize=False,
        readonly=True
    )

    def _compute_tax_details_html(self):
        for move in self:
            tax_totals = move.tax_totals
            amount_untaxed = move.amount_untaxed  # Récupérer la valeur amount_untaxed
            x_studio_escompte = move.x_studio_escompte  # Récupérer la valeur amount_untaxed
            x_studio_valeur_escompte = move.x_studio_valeur_escompte  # Récupérer la valeur amount_untaxed
            x_studio_total_avec_escompte = move.x_studio_total_avec_escompte  # Récupérer la valeur amount_untaxed
            x_studio_total = move.x_studio_total_avec_escompte  # Récupérer la valeur amount_untaxed
            amount_total  = move.amount_total
            total_ht = 0
            if tax_totals:
                total_taxes = sum(
                    tax_group.get('tax_amount_currency', 0.0) 
                    for subtotal in tax_totals.get('subtotals', []) 
                    for tax_group in subtotal.get('tax_groups', [])
                )
                total_ht = x_studio_total_avec_escompte + total_taxes
            html_content = '<table class="float-end">'
            html_content += '<tbody>'
            html_content += f'<tr><td>Net commercial HT </td><td class="text-end">{amount_untaxed}</td></tr>'
            html_content += f'<tr><td>{x_studio_escompte}</td><td class="text-end">{x_studio_valeur_escompte}</td></tr>'
            html_content += f'<tr><td>Net financier HT </td><td class="text-end">{x_studio_total_avec_escompte}</td></tr>'
            if tax_totals:
                for subtotal in tax_totals.get('subtotals', []):
                    for tax_group in subtotal.get('tax_groups', []):
                        group_name = tax_group.get('group_name', '')
                        tax_amount = tax_group.get('tax_amount_currency', 0.0)
                        html_content += f'<tr><td>{group_name}</td><td class="text-end">{tax_amount:.2f}</td></tr>'
            html_content += f'<tr style="border: 4px dotted green;"><td>Net à payer TTC</td><td class="text-end">{total_ht:.2f}</td></tr>'
            html_content += f'<tr style="border: 4px dotted red;"><td>Net commercial TTC </td><td class="text-end">{amount_total}</td></tr>'

            html_content += '</tbody></table>'
            move.tax_details_html = html_content
