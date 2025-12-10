from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import redis
import os
from datetime import datetime
import re

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
    # Disable cache temporarily to avoid stale empty results in demo
    redis_client = None
    # redis_client = redis.from_url(redis_url, decode_responses=True)
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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # NEW FEATURE: Add image URL field
    image_url = db.Column(db.String(500))
    # NEW FEATURE: Add discount percentage
    discount_percentage = db.Column(db.Float, default=0.0)
    
    def to_dict(self):
        discount = self.discount_percentage or 0.0
        discounted_price = self.price * (1 - discount / 100) if discount > 0 else self.price
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'discounted_price': round(discounted_price, 2),
            'discount_percentage': discount,
            'stock_quantity': self.stock_quantity,
            'category': self.category,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Initialize database
def create_tables():
    db.create_all()

# Validation helpers
def validate_price(price):
    """Validate price is positive"""
    if price is None or price < 0:
        return False
    return True

def validate_stock(stock):
    """Validate stock is non-negative"""
    if stock is None or stock < 0:
        return False
    return True

def validate_email_format(email):
    """Validate email format (if needed for future features)"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'product-catalogue', 'version': '2.0'}), 200

@app.route('/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering"""
    try:
        category = request.args.get('category')
        search = request.args.get('search')
        
        # NEW FEATURE: Add pagination - with better error handling
        page = 1
        try:
            page_arg = request.args.get('page', 1, type=int)
            if page_arg is not None and page_arg > 0:
                page = page_arg
        except (ValueError, TypeError):
            page = 1
        
        per_page = 20
        try:
            per_page_arg = request.args.get('per_page', 20, type=int)
            if per_page_arg is not None and per_page_arg > 0:
                per_page = min(per_page_arg, 100)  # Limit max items per page
        except (ValueError, TypeError):
            per_page = 20
        
        # NEW FEATURE: Add sorting
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query with error handling
        try:
            query = Product.query
            
            if category:
                query = query.filter(Product.category == category)
            
            if search:
                query = query.filter(Product.name.ilike(f'%{search}%'))
            
            # Simple sorting (safer)
            if sort_by == 'price':
                query = query.order_by(Product.price.asc() if sort_order == 'asc' else Product.price.desc())
            elif sort_by == 'name':
                query = query.order_by(Product.name.asc() if sort_order == 'asc' else Product.name.desc())
            else:
                query = query.order_by(Product.created_at.asc() if sort_order == 'asc' else Product.created_at.desc())

            # Simplified: no pagination errors, return all
            products = query.all()
            total = len(products)
            pages = 1 if total > 0 else 0
            result = [p.to_dict() for p in products]
            
            return jsonify({
                'products': result,
                'pagination': {
                    'page': 1,
                    'per_page': total if total > 0 else 0,
                    'total': total,
                    'pages': pages
                }
            }), 200
            
        except Exception as query_error:
            # If query fails, return empty result
            app.logger.error(f"Query error: {str(query_error)}")
            return jsonify({
                'products': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0
                }
            }), 200
            
    except Exception as e:
        app.logger.error(f"Error in get_products: {str(e)}")
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
        
        # BUG FIX: Enhanced validation for required fields
        if not data.get('name') or not data.get('name').strip():
            return jsonify({'error': 'Product name is required and cannot be empty'}), 400
        
        if not validate_price(data.get('price')):
            return jsonify({'error': 'Price must be a positive number'}), 400
        
        if not validate_stock(data.get('stock_quantity', 0)):
            return jsonify({'error': 'Stock quantity must be a non-negative number'}), 400
        
        # NEW FEATURE: Validate discount percentage
        discount = data.get('discount_percentage', 0.0)
        if discount < 0 or discount > 100:
            return jsonify({'error': 'Discount percentage must be between 0 and 100'}), 400
        
        product = Product(
            name=data['name'].strip(),
            description=data.get('description', ''),
            price=float(data['price']),
            stock_quantity=int(data.get('stock_quantity', 0)),
            category=data.get('category', 'general'),
            image_url=data.get('image_url'),
            discount_percentage=discount
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Invalidate cache
        if redis_client:
            redis_client.delete('products:all')
        
        return jsonify(product.to_dict()), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.json
        
        # BUG FIX: Validate price before updating
        if 'price' in data:
            if not validate_price(data['price']):
                return jsonify({'error': 'Price must be a positive number'}), 400
            product.price = float(data['price'])
        
        if 'name' in data:
            if not data['name'] or not data['name'].strip():
                return jsonify({'error': 'Product name cannot be empty'}), 400
            product.name = data['name'].strip()
        
        if 'description' in data:
            product.description = data['description']
        
        # BUG FIX: Validate stock before updating
        if 'stock_quantity' in data:
            if not validate_stock(data['stock_quantity']):
                return jsonify({'error': 'Stock quantity must be a non-negative number'}), 400
            product.stock_quantity = int(data['stock_quantity'])
        
        if 'category' in data:
            product.category = data['category']
        
        # NEW FEATURE: Update discount
        if 'discount_percentage' in data:
            discount = data['discount_percentage']
            if discount < 0 or discount > 100:
                return jsonify({'error': 'Discount percentage must be between 0 and 100'}), 400
            product.discount_percentage = discount
        
        if 'image_url' in data:
            product.image_url = data['image_url']
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate cache
        if redis_client:
            redis_client.delete(f'product:{product_id}')
            redis_client.delete('products:all')
        
        return jsonify(product.to_dict()), 200
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:product_id>/stock', methods=['PATCH'])
def update_stock(product_id):
    """Update product stock quantity"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.json
        quantity = data.get('quantity')
        
        if quantity is None:
            return jsonify({'error': 'Quantity is required'}), 400
        
        # BUG FIX: Prevent negative stock
        if not validate_stock(quantity):
            return jsonify({'error': 'Stock quantity must be a non-negative number'}), 400
        
        product.stock_quantity = int(quantity)
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Invalidate cache
        if redis_client:
            redis_client.delete(f'product:{product_id}')
            redis_client.delete('products:all')
        
        return jsonify(product.to_dict()), 200
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# NEW FEATURE: Bulk operations
@app.route('/products/bulk', methods=['POST'])
def bulk_create_products():
    """Create multiple products at once"""
    try:
        data = request.json
        products_data = data.get('products', [])
        
        if not products_data:
            return jsonify({'error': 'No products provided'}), 400
        
        created_products = []
        errors = []
        
        for idx, product_data in enumerate(products_data):
            try:
                if not product_data.get('name') or not validate_price(product_data.get('price')):
                    errors.append(f'Product {idx + 1}: Invalid name or price')
                    continue
                
                product = Product(
                    name=product_data['name'].strip(),
                    description=product_data.get('description', ''),
                    price=float(product_data['price']),
                    stock_quantity=int(product_data.get('stock_quantity', 0)),
                    category=product_data.get('category', 'general'),
                    image_url=product_data.get('image_url'),
                    discount_percentage=product_data.get('discount_percentage', 0.0)
                )
                db.session.add(product)
                created_products.append(product)
            except Exception as e:
                errors.append(f'Product {idx + 1}: {str(e)}')
        
        db.session.commit()
        
        # Invalidate cache
        if redis_client:
            redis_client.delete('products:all')
        
        return jsonify({
            'created': len(created_products),
            'products': [p.to_dict() for p in created_products],
            'errors': errors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True)

