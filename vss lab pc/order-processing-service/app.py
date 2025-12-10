from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
import os
from datetime import datetime

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'status': self.status,
            'total_amount': self.total_amount,
            'shipping_address': self.shipping_address
        }

# Order Item Model
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    order = db.relationship('Order', backref='items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
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

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'order-processing'}), 200

@app.route('/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    try:
        # BUG: No authentication check
        data = request.json
        
        if not data.get('user_id') or not data.get('items'):
            return jsonify({'error': 'user_id and items are required'}), 400
        
        user_id = data['user_id']
        items = data['items']
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
            
            # Get product info
            product = get_product_info(product_id)
            if not product:
                return jsonify({'error': f'Product {product_id} not found'}), 404
            
            # BUG: No stock validation
            item_price = product['price'] * quantity
            total_amount += item_price
            
            order_items_data.append({
                'product_id': product_id,
                'quantity': quantity,
                'price': product['price']
            })
        
        # Create order
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            shipping_address=shipping_address,
            status='pending'
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # Get full order details
        order_dict = order.to_dict()
        order_dict['items'] = [item.to_dict() for item in order.items]
        
        return jsonify(order_dict), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details"""
    try:
        # BUG: No authentication/authorization
        order = Order.query.get_or_404(order_id)
        order_dict = order.to_dict()
        order_dict['items'] = [item.to_dict() for item in order.items]
        return jsonify(order_dict), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    """Get all orders for a user"""
    try:
        # BUG: No authentication check - anyone can view any user's orders
        orders = Order.query.filter_by(user_id=user_id).all()
        result = []
        for order in orders:
            order_dict = order.to_dict()
            order_dict['items'] = [item.to_dict() for item in order.items]
            result.append(order_dict)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders/<int:order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    """Update order status"""
    try:
        # BUG: No authentication/authorization
        order = Order.query.get_or_404(order_id)
        data = request.json
        
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        new_status = data.get('status')
        
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        order.status = new_status
        db.session.commit()
        
        order_dict = order.to_dict()
        order_dict['items'] = [item.to_dict() for item in order.items]
        
        return jsonify(order_dict), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True)

