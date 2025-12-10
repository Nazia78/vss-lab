from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import redis
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database configuration
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/products')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Redis configuration
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
try:
    redis_client = redis.from_url(redis_url, decode_responses=True)
except:
    redis_client = None

# Product Model
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock_quantity': self.stock_quantity,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Initialize database
def create_tables():
    db.create_all()

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'product-catalogue'}), 200

@app.route('/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering"""
    try:
        cache_key = f"products:all"
        
        # Check cache first
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                import json
                return jsonify(json.loads(cached)), 200
        
        category = request.args.get('category')
        search = request.args.get('search')
        
        query = Product.query
        
        if category:
            query = query.filter(Product.category == category)
        
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        products = query.all()
        result = [product.to_dict() for product in products]
        
        # Cache the result
        if redis_client:
            import json
            redis_client.setex(cache_key, 300, json.dumps(result))  # Cache for 5 minutes
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    try:
        cache_key = f"product:{product_id}"
        
        # Check cache
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                import json
                return jsonify(json.loads(cached)), 200
        
        product = Product.query.get_or_404(product_id)
        result = product.to_dict()
        
        # Cache the result
        if redis_client:
            import json
            redis_client.setex(cache_key, 300, json.dumps(result))
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products', methods=['POST'])
def create_product():
    """Create a new product"""
    try:
        data = request.json
        
        # Validation - BUG: Missing validation for required fields
        if not data.get('name'):
            return jsonify({'error': 'Product name is required'}), 400
        
        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=data.get('price', 0.0),
            stock_quantity=data.get('stock_quantity', 0),
            category=data.get('category', 'general')
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Invalidate cache
        if redis_client:
            redis_client.delete('products:all')
        
        return jsonify(product.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.json
        
        # BUG: No validation - can set negative prices
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        if 'stock_quantity' in data:
            product.stock_quantity = data['stock_quantity']
        if 'category' in data:
            product.category = data['category']
        
        db.session.commit()
        
        # Invalidate cache
        if redis_client:
            redis_client.delete(f'product:{product_id}')
            redis_client.delete('products:all')
        
        return jsonify(product.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>/stock', methods=['PATCH'])
def update_stock(product_id):
    """Update product stock quantity"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.json
        quantity = data.get('quantity', 0)
        
        # BUG: Can set negative stock
        product.stock_quantity = quantity
        db.session.commit()
        
        # Invalidate cache
        if redis_client:
            redis_client.delete(f'product:{product_id}')
            redis_client.delete('products:all')
        
        return jsonify(product.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True)

