from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

# Configuration
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/orders')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# External service URLs
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:8001')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:8002')

db = SQLAlchemy(app)

# Order Model
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    total_amount = db.Column(db.Float, nullable=False)
    shipping_address = db.Column(db.Text)
    # NEW FEATURE: Add payment status
    payment_status = db.Column(db.String(20), default='pending')
    # NEW FEATURE: Add tracking number
    tracking_number = db.Column(db.String(100))
    # NEW FEATURE: Add notes
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'status': self.status,
            'total_amount': self.total_amount,
            'shipping_address': self.shipping_address,
            'payment_status': self.payment_status,
            'tracking_number': self.tracking_number,
            'notes': self.notes
        }

# Order Item Model
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    # NEW FEATURE: Store product name for historical reference
    product_name = db.Column(db.String(200))
    
    order = db.relationship('Order', backref='items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': self.price
        }

# Initialize database
def create_tables():
    db.create_all()

# Helper functions
def verify_auth_token(token):
    """Verify authentication token with auth service"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(f'{AUTH_SERVICE_URL}/verify', headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        app.logger.error(f"Auth verification failed: {str(e)}")
        return None

def get_product_info(product_id):
    """Get product information from product service"""
    try:
        response = requests.get(f'{PRODUCT_SERVICE_URL}/products/{product_id}', timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        app.logger.error(f"Product service error: {str(e)}")
        return None

def update_product_stock(product_id, quantity_change):
    """Update product stock in product service"""
    try:
        product = get_product_info(product_id)
        if not product:
            return False
        
        current_stock = product.get('stock_quantity', 0)
        new_stock = current_stock - quantity_change
        
        # Update stock via product service
        response = requests.patch(
            f'{PRODUCT_SERVICE_URL}/products/{product_id}/stock',
            json={'quantity': new_stock},
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        app.logger.error(f"Stock update failed: {str(e)}")
        return False

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        else:
            return jsonify({'error': 'Invalid token format. Use: Bearer <token>'}), 401
        
        auth_info = verify_auth_token(token)
        if not auth_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.current_user = auth_info
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'order-processing', 'version': '2.0'}), 200

@app.route('/orders', methods=['POST'])
@require_auth
def create_order():
    """Create a new order"""
    try:
        # BUG FIX: Require authentication
        current_user_id = request.current_user['user_id']
        data = request.json
        
        # Use authenticated user's ID instead of provided user_id
        user_id = current_user_id
        
        items = data.get('items', [])
        shipping_address = data.get('shipping_address', '')
        
        if not items:
            return jsonify({'error': 'Order must contain at least one item'}), 400
        
        total_amount = 0.0
        order_items_data = []
        
        # Validate products and calculate total
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            if not product_id:
                return jsonify({'error': 'product_id is required for each item'}), 400
            
            if quantity <= 0:
                return jsonify({'error': 'Quantity must be greater than 0'}), 400
            
            # Get product info
            product = get_product_info(product_id)
            if not product:
                return jsonify({'error': f'Product {product_id} not found'}), 404
            
            # BUG FIX: Validate stock availability
            available_stock = product.get('stock_quantity', 0)
            if available_stock < quantity:
                return jsonify({
                    'error': f'Insufficient stock for product {product_id}. Available: {available_stock}, Requested: {quantity}'
                }), 400
            
            # NEW FEATURE: Use discounted price if available
            price = product.get('discounted_price') or product.get('price', 0)
            item_price = price * quantity
            total_amount += item_price
            
            order_items_data.append({
                'product_id': product_id,
                'product_name': product.get('name', 'Unknown Product'),
                'quantity': quantity,
                'price': price
            })
        
        # Create order
        order = Order(
            user_id=user_id,
            total_amount=round(total_amount, 2),
            shipping_address=shipping_address,
            status='pending',
            payment_status=data.get('payment_status', 'pending'),
            notes=data.get('notes', '')
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items and update stock
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            db.session.add(order_item)
            
            # BUG FIX: Update product stock
            if not update_product_stock(item_data['product_id'], item_data['quantity']):
                db.session.rollback()
                return jsonify({'error': f'Failed to update stock for product {item_data["product_id"]}'}), 500
        
        db.session.commit()
        
        # Get full order details
        order_dict = order.to_dict()
        order_dict['items'] = [item.to_dict() for item in order.items]
        
        return jsonify(order_dict), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
@require_auth
def get_order(order_id):
    """Get order details"""
    try:
        # BUG FIX: Require authentication and authorization
        current_user_id = request.current_user['user_id']
        current_user_role = request.current_user.get('role', 'customer')
        
        order = Order.query.get_or_404(order_id)
        
        # Users can only view their own orders unless they're admin
        if order.user_id != current_user_id and current_user_role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        order_dict = order.to_dict()
        order_dict['items'] = [item.to_dict() for item in order.items]
        return jsonify(order_dict), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders/user/<int:user_id>', methods=['GET'])
@require_auth
def get_user_orders(user_id):
    """Get all orders for a user"""
    try:
        # BUG FIX: Require authentication and authorization
        current_user_id = request.current_user['user_id']
        current_user_role = request.current_user.get('role', 'customer')
        
        # Users can only view their own orders unless they're admin
        if user_id != current_user_id and current_user_role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # NEW FEATURE: Add filtering by status
        status_filter = request.args.get('status')
        query = Order.query.filter_by(user_id=user_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        orders = query.order_by(Order.order_date.desc()).all()
        
        result = []
        for order in orders:
            order_dict = order.to_dict()
            order_dict['items'] = [item.to_dict() for item in order.items]
            result.append(order_dict)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders/<int:order_id>/status', methods=['PATCH'])
@require_auth
def update_order_status(order_id):
    """Update order status"""
    try:
        # BUG FIX: Require authentication and authorization
        current_user_role = request.current_user.get('role', 'customer')
        
        # Only admins can update order status
        if current_user_role != 'admin':
            return jsonify({'error': 'Only admins can update order status'}), 403
        
        order = Order.query.get_or_404(order_id)
        data = request.json
        
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        new_status = data.get('status')
        
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        order.status = new_status
        
        # NEW FEATURE: Auto-generate tracking number when shipped
        if new_status == 'shipped' and not order.tracking_number:
            order.tracking_number = f'TRACK-{order.id:06d}-{datetime.utcnow().strftime("%Y%m%d")}'
        
        db.session.commit()
        
        order_dict = order.to_dict()
        order_dict['items'] = [item.to_dict() for item in order.items]
        
        return jsonify(order_dict), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# NEW FEATURE: Update payment status
@app.route('/orders/<int:order_id>/payment', methods=['PATCH'])
@require_auth
def update_payment_status(order_id):
    """Update payment status"""
    try:
        current_user_id = request.current_user['user_id']
        current_user_role = request.current_user.get('role', 'customer')
        
        order = Order.query.get_or_404(order_id)
        
        # Users can only update their own order payment status, or admins can update any
        if order.user_id != current_user_id and current_user_role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.json
        payment_status = data.get('payment_status')
        
        valid_statuses = ['pending', 'paid', 'failed', 'refunded']
        if payment_status not in valid_statuses:
            return jsonify({'error': f'Invalid payment status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        order.payment_status = payment_status
        db.session.commit()
        
        order_dict = order.to_dict()
        order_dict['items'] = [item.to_dict() for item in order.items]
        
        return jsonify(order_dict), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# NEW FEATURE: Get all orders (admin only)
@app.route('/orders', methods=['GET'])
@require_auth
def list_all_orders():
    """List all orders (admin only)"""
    try:
        current_user_role = request.current_user.get('role', 'customer')
        
        if current_user_role != 'admin':
            return jsonify({'error': 'Only admins can view all orders'}), 403
        
        status_filter = request.args.get('status')
        query = Order.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        orders = query.order_by(Order.order_date.desc()).all()
        
        result = []
        for order in orders:
            order_dict = order.to_dict()
            order_dict['items'] = [item.to_dict() for item in order.items]
            result.append(order_dict)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True)

