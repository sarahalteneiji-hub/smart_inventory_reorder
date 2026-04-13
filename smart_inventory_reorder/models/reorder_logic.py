from odoo import models, fields, api
from datetime import timedelta


class SmartReorderRecommendation(models.Model):
    _name = 'smart.reorder.recommendation'
    _description = 'Smart Reorder Recommendation'
    _order = 'days_left asc, product_id asc'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade'
    )

    current_stock = fields.Float(
        string='Current Stock',
        compute='_compute_recommendation_data',
        store=True
    )

    sales_last_30_days = fields.Float(
        string='Sales Last 30 Days',
        compute='_compute_recommendation_data',
        store=True
    )

    average_daily_demand = fields.Float(
        string='Average Daily Demand',
        compute='_compute_recommendation_data',
        store=True
    )

    days_left = fields.Float(
        string='Days Left',
        compute='_compute_recommendation_data',
        store=True
    )

    reorder_status = fields.Selection(
        [
            ('ok', 'OK'),
            ('reorder_soon', 'Reorder Soon'),
            ('no_sales', 'No Recent Sales'),
        ],
        string='Status',
        compute='_compute_recommendation_data',
        store=True
    )

    alert_message = fields.Char(
        string='Alert Message',
        compute='_compute_recommendation_data',
        store=True
    )

    alert_days = fields.Integer(
        string='Alert Days Threshold',
        default=5
    )

    @api.depends('product_id', 'alert_days')
    def _compute_recommendation_data(self):
        """
        Compute:
        - current stock
        - sales in last 30 days
        - average daily demand
        - days left
        - reorder status
        - alert message
        """
        SaleOrderLine = self.env['sale.order.line']
        today = fields.Datetime.now()
        date_30_days_ago = today - timedelta(days=30)

        for rec in self:
            rec.current_stock = 0.0
            rec.sales_last_30_days = 0.0
            rec.average_daily_demand = 0.0
            rec.days_left = 0.0
            rec.reorder_status = 'no_sales'
            rec.alert_message = 'No recent sales, no reorder needed now.'

            if not rec.product_id:
                continue

            # Current stock from Odoo inventory
            rec.current_stock = rec.product_id.qty_available

            # Read confirmed sales in the last 30 days
            sale_lines = SaleOrderLine.search([
                ('product_id', '=', rec.product_id.id),
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', date_30_days_ago),
            ])

            total_sold = sum(sale_lines.mapped('product_uom_qty'))
            rec.sales_last_30_days = total_sold

            # Average daily demand
            avg_daily = total_sold / 30.0 if total_sold > 0 else 0.0
            rec.average_daily_demand = avg_daily

            # If no recent sales
            if avg_daily == 0:
                rec.days_left = 0.0
                rec.reorder_status = 'no_sales'
                rec.alert_message = f"{rec.product_id.display_name}: No recent sales, no reorder needed now."
                continue

            # Days left
            rec.days_left = rec.current_stock / avg_daily if avg_daily else 0.0

            # Compare with threshold
            if rec.days_left <= rec.alert_days:
                rec.reorder_status = 'reorder_soon'
                rec.alert_message = (
                    f"Reorder {rec.product_id.display_name} — "
                    f"stock will run out in {round(rec.days_left)} days."
                )
            else:
                rec.reorder_status = 'ok'
                rec.alert_message = (
                    f"{rec.product_id.display_name}: Stock is sufficient for about "
                    f"{round(rec.days_left)} days."
                )

    @api.model
    def run_daily_recommendation_update(self):
        """
        Daily cron job:
        Create or update recommendation records for all storable products.
        """
        products = self.env['product.product'].search([
            ('detailed_type', '=', 'product')
        ])

        for product in products:
            record = self.search([('product_id', '=', product.id)], limit=1)
            if not record:
                record = self.create({
                    'product_id': product.id,
                })

            # Force recompute by writing the same product_id
            record.write({
                'product_id': product.id,
            })

        return True
