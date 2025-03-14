{
    'name': 'Custom AST',
    'version': '1.0',
    'category': 'Custom Modules',
    'author': 'Votre Nom ou Société',
    'website': 'https://www.votresite.com',
    'summary': 'Module de personnalisation pour gérer les fonctionnalités spécifiques de notre projet AST',
    'description': """
        Ce module contient les développements personnalisés pour le projet AST,
        y compris des modèles de données, des vues, des actions, des rapports, et
        d'autres fonctionnalités spécifiques.
    """,
    'depends': [
        'base',
        'sale',
        'account',
        'purchase',
        'stock',
    ],
    'data': [
        'security/security.xml',
        'views/custom_ast_views.xml',  # Définissez vos vues XML ici
        'views/sale_order.xml',  # Définissez vos vues XML ici
        'views/Header_Footer.xml',
        'views/custom_devis.xml',
        'views/custom_bc.xml',
        'reports/report_purchase_order_import.xml',
        'reports/ast_bl_bon_prelevement.xml',
        'reports/ast_bl_bon_de_reception.xml',
        'reports/ast_bl_bon_de_reception_local.xml',
        'views/custom_db.xml',
        'views/custom_paper_format.xml',
        'views/stock_lot_views.xml',
        'views/hr_contract_view.xml',
        # 'views/custom_bl.xml',
        
        

    ],
    'installable': True,
    'auto_install': False,
    'application': True,  # Si ce module doit être un module d'application
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'],  # Vous pouvez ajouter une icône pour le module
}
