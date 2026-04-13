{    'name': 'Smart Inventory Reorder Recommendation',    'version': '16.0.1.0.0',    'summary': 'Predicts stock depletion and gives reorder recommendations',    'description': """Smart Inventory Reorder Recommendation Module
- Reads current stock
- Checks sales in the last 30 days
- Calculates average daily demand
- Predicts days left
- Generates reorder alerts
    """,    'author': 'Shahad Khalid Hassan',    'category': 'Inventory',    'depends': ['base', 'stock', 'sale'],    'data': [        'security/ir.model.access.csv',        'views/reorder_views.xml',        'data/cron.xml',    ],    'installable': True,    'application': True,    'auto_install': False,    'license': 'LGPL-3',}