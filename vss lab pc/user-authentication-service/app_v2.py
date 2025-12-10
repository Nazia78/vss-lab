from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import jwt
import os
import re
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
CORS(app)

# Configuration
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/auth')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET'] = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=24)

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='customer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    # NEW FEATURE: Add last login tracking
    last_login = db.Column(db.DateTime)
    # NEW FEATURE: Add password reset token
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

# Initialize database
def create_tables():
    db.create_all()

# Helper functions
def generate_token(user_id, username, role):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA']
    }
    return jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one digit'
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, 'Password must contain at least one special character'
    return True, None

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # BUG FIX: Properly handle Bearer token
        if token.startswith('Bearer '):
            token = token[7:]
        else:
            return jsonify({'error': 'Invalid token format. Use: Bearer <token>'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated_function

def require_role(required_role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            if request.current_user.get('role') != required_role:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'user-authentication', 'version': '2.0'}), 200

@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        
        # Validation
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        # BUG FIX: Validate email format
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # BUG FIX: Validate password strength
        is_valid, error_msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        password_hash = generate_password_hash(data['password'])
        
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            role=data.get('role', 'customer')
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id, user.username, user.role)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'token': token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.json
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # NEW FEATURE: Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id, user.username, user.role)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify', methods=['POST'])
def verify():
    """Verify JWT token"""
    try:
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 401
        
        # BUG FIX: Properly handle Bearer token
        if token.startswith('Bearer '):
            token = token[7:]
        else:
            return jsonify({'error': 'Invalid token format. Use: Bearer <token>'}), 401
        
        payload = verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        return jsonify({
            'valid': True,
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """Get user information"""
    try:
        # BUG FIX: Require authentication and authorization
        current_user_id = request.current_user['user_id']
        current_user_role = request.current_user['role']
        
        # Users can only view their own profile unless they're admin
        if current_user_id != user_id and current_user_role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    """Update user information"""
    try:
        # BUG FIX: Require authentication and authorization
        current_user_id = request.current_user['user_id']
        current_user_role = request.current_user['role']
        
        # Users can only update their own profile unless they're admin
        if current_user_id != user_id and current_user_role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get_or_404(user_id)
        data = request.json
        
        if 'email' in data:
            # BUG FIX: Validate email format
            if not validate_email(data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            # Check if email is already taken
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                return jsonify({'error': 'Email already exists'}), 400
            user.email = data['email']
        
        # Only admins can change roles
        if 'role' in data:
            if current_user_role != 'admin':
                return jsonify({'error': 'Only admins can change user roles'}), 403
            user.role = data['role']
        
        db.session.commit()
        
        return jsonify(user.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# NEW FEATURE: Password change endpoint
@app.route('/users/<int:user_id>/password', methods=['PUT'])
@require_auth
def change_password(user_id):
    """Change user password"""
    try:
        current_user_id = request.current_user['user_id']
        
        if current_user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old password and new password are required'}), 400
        
        user = User.query.get_or_404(user_id)
        
        if not check_password_hash(user.password_hash, old_password):
            return jsonify({'error': 'Incorrect old password'}), 401
        
        # Validate new password strength
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# NEW FEATURE: List all users (admin only)
@app.route('/users', methods=['GET'])
@require_role('admin')
def list_users():
    """List all users (admin only)"""
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True)

