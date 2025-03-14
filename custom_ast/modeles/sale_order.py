from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_unit_original = fields.Float(string="Prix Liste", compute="_compute_price_unit_original", store=True)
    discount_original = fields.Float(string="Remise Originale (%)", compute="_compute_discount_original", store=True)
    is_authorized = fields.Boolean(string="Autorisé", default=False)  # Autorisation par un supérieur
    has_changes = fields.Boolean(
        string="Changements détectés",
        compute="_compute_has_changes",
        store=True  # Stocker la valeur pour éviter de recalculer à chaque accès.
    )


    @api.depends('price_reduce_taxexcl', 'discount', 'price_unit_original', 'discount_original', 'is_authorized')
    def _compute_has_changes(self):
        """Détecte les changements non autorisés dans le prix ou la remise, avec journalisation des valeurs."""
        for line in self:
            # Journaliser les valeurs des champs dépendants
            discount_original_rounded = round(line.discount_original, 2)
            _logger.info(
                "Calcul has_changes pour la ligne %s : "
                "#####################################price_reduce_taxexcl=%s, price_unit_original=%s, discount=%s, discount_original=%s, is_authorized=%s",
                line.id,
                line.price_reduce_taxexcl,
                line.price_unit_original,
                line.discount,
                discount_original_rounded,
                line.is_authorized
            )
            # Calcul de has_changes
            line.has_changes = (
                (line.price_unit != line.price_unit_original or line.discount != discount_original_rounded)
            )

    @api.depends('product_id', 'product_uom', 'product_uom_qty', 'order_id.pricelist_id')
    def _compute_price_unit_original(self):
        for line in self:
            if line.product_id and line.order_id.pricelist_id:
                # Récupération du prix unitaire basé sur la liste de prix
                pricelist = line.order_id.pricelist_id
                price_unit = pricelist._get_product_price(
                    product=line.product_id,
                    quantity=line.product_uom_qty,
                    partner=line.order_id.partner_id
                )
                line.price_unit_original = line.product_id.list_price
            else:
                # Si la liste de prix ou le produit n'est pas trouvé, utiliser le prix standard du produit
                line.price_unit_original = line.product_id.list_price

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_discount_original(self):
        discount_enabled = self.env['product.pricelist.item']._is_discount_feature_enabled()
        for line in self:
            if not line.product_id or line.display_type:
                line.discount_original = 0.0
                continue

            if not (line.order_id.pricelist_id and discount_enabled):
                line.discount_original = 0.0
                continue

            if not line.pricelist_item_id._show_discount():
                line.discount_original = 0.0
                continue

            line = line.with_company(line.company_id)
            pricelist_price = line._get_pricelist_price()
            base_price = line._get_pricelist_price_before_discount()

            if base_price != 0:  # Éviter la division par zéro
                discount = (base_price - pricelist_price) / base_price * 100
                if (discount > 0 and base_price > 0) or (discount < 0 and base_price < 0):
                    line.discount_original = discount


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    # Nouvelle liste avec un statut supplémentaire

    state = fields.Selection([
        ('draft', 'Devis'),
        ('bon_preparation', 'Bon de commande'),
        ('sent', 'Envoyé'),
        ('sale', 'Bon de préparation'),
        ('cancel', 'Annulé'),
    ], string="Statut")


    is_lot_change_required = fields.Boolean(string="Exigence de changement de lot")
    lot_change_detail = fields.Text(string="Détail du changement de lot", help="Détail en cas d'exigence de changement de lot")


    is_price_changed = fields.Boolean(string="Changement de prix", compute="_compute_price_change", store=True)
    is_authorized = fields.Boolean(string="Autorisé", default=False)
    requested_authorization = fields.Boolean(string="Demande d'autorisation", default=False)

    condition_has_changed = fields.Boolean(
        string="Condition de paiement modifiée",
        compute='_compute_condition_has_changed',
        store=True,
    )

    requested_payment_term_authorization = fields.Boolean(
        string="Autorisation demandée pour changement de condition",
        default=False,
    )
    is_payment_term_authorized = fields.Boolean(
        string="Changement de condition autorisé",
        default=False,
    )
    is_authorized_finance = fields.Boolean(string="Authorisé par la finance", default=True)

    def action_authorize_finance(self):
        for order in self:
            if not order.is_authorized_finance:
                order.is_authorized_finance = True

    def action_authorize_payment_term(self):
        for order in self:
            if order.requested_payment_term_authorization:
                order.is_payment_term_authorized = True


    @api.depends('partner_id.property_payment_term_id', 'payment_term_id')
    def _compute_condition_has_changed(self):
        for order in self:
            if order.partner_id and order.partner_id.property_payment_term_id:
                order.condition_has_changed = order.payment_term_id != order.partner_id.property_payment_term_id


    @api.depends('order_line.price_unit', 'order_line.discount', 'order_line.price_unit_original',
                 'order_line.discount_original')
    def _compute_price_change(self):
        for order in self:
            order.is_price_changed = any(
                (line.price_unit != line.price_unit_original or line.discount != round(line.discount_original, 2))
                and not line.is_authorized
                for line in order.order_line
            )


    def action_request_combined_authorization(self):
        for order in self:
            if order.condition_has_changed:
                order.requested_payment_term_authorization = True
            if order.is_price_changed:
                order.requested_authorization = True
                order.message_post(body=_("Une demande d'autorisation a été envoyée."))

    def action_authorize_price_change(self):
        self.is_authorized = True
        self.order_line.write({'is_authorized': True})


    def _confirmation_error_message(self):
        """Return whether order can be confirmed or not. If not, return error message."""
        self.ensure_one()

        # Ajouter le statut 'bon_preparation' comme valide pour confirmation
        if self.state not in {'draft', 'sent', 'bon_preparation'}:
            return _("Some orders are not in a state requiring confirmation.")

        # Vérification des lignes de commande
        if any(
            not line.display_type
            and not line.is_downpayment
            and not line.product_id
            for line in self.order_line
        ):
            return _("A line on these orders is missing a product, you cannot confirm it.")

        return False


    def action_set_draft(self):
        """
        Cette méthode retourne l'état à 'draft'.
        """
        for order in self:
            order.state = 'draft'

    def action_set_bon_preparation(self):
        """
        Cette méthode change l'état à 'bon_preparation' après vérification des conditions.
        """
        for order in self:

            # Vérifier si le prix ou la remise a été modifié sans autorisation
            if order.is_price_changed and not order.is_authorized:
                # Construire un message détaillé avec uniquement les lignes ayant has_changes=True
                changed_lines = []
                for line in order.order_line:
                    if line.has_changes and not line.is_authorized:
                        changes = []
                        if line.price_reduce_taxexcl != line.price_unit_original:
                            changes.append(
                                _("Prix unitaire modifié : %(new_price).2f (original : %(original_price).2f)") % {
                                    'new_price': line.price_unit,
                                    'original_price': line.price_unit_original,
                                }
                            )
                        if line.discount != round(line.discount_original, 2):
                            changes.append(
                                _("Remise modifiée : %(new_discount).2f%% (originale : %(original_discount).2f%%)") % {
                                    'new_discount': line.discount,
                                    'original_discount': round(line.discount_original, 2),
                                }
                            )
                        if changes:
                            changed_lines.append(
                                _("Produit : %(product)s | %(details)s") % {
                                    'product': line.product_id.display_name,
                                    'details': " | ".join(changes),
                                }
                            )

                # Lever une exception avec les détails des modifications
                if changed_lines:
                    raise UserError(
                        _(
                            "Le prix ou la remise a été modifié pour les lignes suivantes :\n%s\nVeuillez demander une autorisation avant de passer à l'état 'bon de commande'.")
                        % "\n".join(changed_lines)
                    )

            # Vérifier si les conditions de paiement dans le devis diffèrent de celles du client
            if order.condition_has_changed and not order.is_payment_term_authorized:
                raise UserError(
                    _("Les conditions de paiement du devis (%s) diffèrent de celles définies pour le client (%s). "
                      "Veuillez demander une autorisation avant de passer à l'état 'bon préparation'.")
                    % (order.payment_term_id.name, order.partner_id.property_payment_term_id.name)
                )
            # Vérifier si les champs 'client_order_ref' et 'x_studio_bc_pice_jointe' sont remplis
            if not order.client_order_ref or not order.x_studio_bc_pice_jointe:
                raise UserError(
                    _("Les champs 'Référence commande client' ou 'Pièce jointe' doivent être remplis avant de passer à l'état 'bon de commande'.")
                )

            # Autoriser le plafond
            if not order.is_authorized_finance:
               raise UserError(
                    _("Merci de vérifier le plafond du client.")
                )
        # Si toutes les validations passent, on change l'état
        self.write({'state': 'bon_preparation','is_authorized': False, 'requested_authorization': False, 'requested_payment_term_authorization': False, 'is_payment_term_authorized': False,})
        return True
