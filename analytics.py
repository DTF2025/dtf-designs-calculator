from datetime import datetime, timedelta
from sqlalchemy import func, text
import json

class BusinessAnalytics:
    def __init__(self, db):
        self.db = db
    
    def get_dashboard_stats(self):
        """Get key business metrics for dashboard"""
        from app import Quote, Order, Customer
        
        # Get date ranges
        today = datetime.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        # Total stats
        total_quotes = Quote.query.count()
        total_orders = Order.query.count()
        total_customers = Customer.query.count()
        
        # This month stats
        this_month_quotes = Quote.query.filter(
            func.date(Quote.created_at) >= this_month_start
        ).count()
        
        this_month_orders = Order.query.filter(
            func.date(Order.created_at) >= this_month_start
        ).count()
        
        # Revenue calculations
        total_revenue = self.db.session.query(
            func.sum(Quote.final_price)
        ).filter(Quote.status == 'approved').scalar() or 0
        
        this_month_revenue = self.db.session.query(
            func.sum(Quote.final_price)
        ).filter(
            Quote.status == 'approved',
            func.date(Quote.created_at) >= this_month_start
        ).scalar() or 0
        
        # Conversion rate
        approved_quotes = Quote.query.filter(Quote.status == 'approved').count()
        conversion_rate = (approved_quotes / total_quotes * 100) if total_quotes > 0 else 0
        
        # Average order value
        avg_order_value = total_revenue / approved_quotes if approved_quotes > 0 else 0
        
        return {
            'total_quotes': total_quotes,
            'total_orders': total_orders,
            'total_customers': total_customers,
            'this_month_quotes': this_month_quotes,
            'this_month_orders': this_month_orders,
            'total_revenue': total_revenue,
            'this_month_revenue': this_month_revenue,
            'conversion_rate': round(conversion_rate, 1),
            'avg_order_value': round(avg_order_value, 2)
        }
    
    def get_daily_stats(self, days=30):
        """Get daily statistics for charts"""
        from app import Quote, Order
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Daily quotes
        daily_quotes = self.db.session.query(
            func.date(Quote.created_at).label('date'),
            func.count(Quote.id).label('count')
        ).filter(
            func.date(Quote.created_at) >= start_date
        ).group_by(func.date(Quote.created_at)).all()
        
        # Daily orders
        daily_orders = self.db.session.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('count')
        ).filter(
            func.date(Order.created_at) >= start_date
        ).group_by(func.date(Order.created_at)).all()
        
        # Daily revenue
        daily_revenue = self.db.session.query(
            func.date(Quote.created_at).label('date'),
            func.sum(Quote.final_price).label('revenue')
        ).filter(
            Quote.status == 'approved',
            func.date(Quote.created_at) >= start_date
        ).group_by(func.date(Quote.created_at)).all()
        
        return {
            'quotes': [(str(row.date), row.count) for row in daily_quotes],
            'orders': [(str(row.date), row.count) for row in daily_orders],
            'revenue': [(str(row.date), float(row.revenue or 0)) for row in daily_revenue]
        }
    
    def get_category_breakdown(self):
        """Get quote breakdown by category"""
        from app import Quote
        
        category_stats = self.db.session.query(
            Quote.category,
            func.count(Quote.id).label('count'),
            func.sum(Quote.final_price).label('total_value')
        ).filter(
            Quote.status == 'approved'
        ).group_by(Quote.category).all()
        
        return {
            'categories': [row.category for row in category_stats],
            'counts': [row.count for row in category_stats],
            'values': [float(row.total_value or 0) for row in category_stats]
        }
    
    def get_customer_insights(self):
        """Get customer behavior insights"""
        from app import Customer, Quote
        
        # Top customers by total spent
        top_customers = self.db.session.query(
            Customer.name,
            Customer.email,
            func.sum(Quote.final_price).label('total_spent'),
            func.count(Quote.id).label('quote_count')
        ).join(Quote).filter(
            Quote.status == 'approved'
        ).group_by(Customer.id, Customer.name, Customer.email).order_by(
            func.sum(Quote.final_price).desc()
        ).limit(10).all()
        
        # Customer type breakdown
        customer_types = self.db.session.query(
            Customer.customer_type,
            func.count(Customer.id).label('count')
        ).group_by(Customer.customer_type).all()
        
        return {
            'top_customers': [
                {
                    'name': row.name,
                    'email': row.email,
                    'total_spent': float(row.total_spent or 0),
                    'quote_count': row.quote_count
                } for row in top_customers
            ],
            'customer_types': {row.customer_type: row.count for row in customer_types}
        }
    
    def get_quote_status_summary(self):
        """Get quote status breakdown"""
        from app import Quote
        
        status_counts = self.db.session.query(
            Quote.status,
            func.count(Quote.id).label('count')
        ).group_by(Quote.status).all()
        
        return {row.status: row.count for row in status_counts}
    
    def get_trend_analysis(self):
        """Get month-over-month trends"""
        from app import Quote
        
        # Get last 6 months of data
        monthly_stats = self.db.session.query(
            func.date_trunc('month', Quote.created_at).label('month'),
            func.count(Quote.id).label('quote_count'),
            func.sum(Quote.final_price).label('revenue')
        ).filter(
            Quote.created_at >= datetime.now() - timedelta(days=180)
        ).group_by(
            func.date_trunc('month', Quote.created_at)
        ).order_by('month').all()
        
        return {
            'months': [row.month.strftime('%Y-%m') for row in monthly_stats],
            'quote_counts': [row.quote_count for row in monthly_stats],
            'revenues': [float(row.revenue or 0) for row in monthly_stats]
        }