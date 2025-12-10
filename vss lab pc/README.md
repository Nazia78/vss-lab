# E-commerce Microservices Application

## Project Overview

This project implements a Dockerized e-commerce platform consisting of three microservices:
1. **Product Catalogue Service** - Manages product inventory and information
2. **User Authentication Service** - Handles user registration, authentication, and authorization
3. **Order Processing Service** - Processes and manages customer orders

## Project Scenario

An online E-commerce retail company operates a Dockerized application for managing its e-commerce platform. The application consists of multiple microservices deployed as Docker containers. The company needs to update its existing Dockerized application to introduce new features and address bugs discovered in the current version.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    E-commerce Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │   Product        │  │   Authentication│  │   Order     │ │
│  │   Catalogue      │  │   Service       │  │   Processing│ │
│  │   Service        │  │                 │  │   Service   │ │
│  │   (Port 8001)    │  │   (Port 8002)   │  │   (Port 8003)│ │
│  └────────┬─────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                      │                   │        │
│  ┌────────▼─────────┐  ┌────────▼─────────┐  ┌─────▼──────┐ │
│  │  Product DB      │  │   Auth DB        │  │  Order DB  │ │
│  │  (PostgreSQL)    │  │   (PostgreSQL)   │  │ (PostgreSQL)│ │
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Redis Cache (Port 6379)                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Services Description

### 1. Product Catalogue Service
- Manages product inventory
- Provides product search and filtering
- Handles product CRUD operations
- Implements Redis caching for performance

### 2. User Authentication Service
- User registration and login
- JWT token-based authentication
- Role-based access control (customer, admin)
- Password management

### 3. Order Processing Service
- Order creation and management
- Integration with Product and Auth services
- Order status tracking
- Payment status management

## Technology Stack

- **Backend Framework**: Flask (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Containerization**: Docker & Docker Compose
- **API Communication**: RESTful APIs

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)
- Git (for cloning the repository)

## Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ecommerce-microservices
```

### 2. Build and Run Version 1.0 (Initial Version with Bugs)
```bash
docker-compose up --build
```

### 3. Build and Run Version 2.0 (Updated Version with Fixes)
```bash
docker-compose -f docker-compose.v2.yml up --build
```

## API Endpoints

### Product Catalogue Service (Port 8001)

- `GET /health` - Health check
- `GET /products` - List all products (with pagination, sorting, filtering)
- `GET /products/<id>` - Get product by ID
- `POST /products` - Create new product
- `PUT /products/<id>` - Update product
- `PATCH /products/<id>/stock` - Update stock quantity
- `POST /products/bulk` - Bulk create products (v2.0)

### User Authentication Service (Port 8002)

- `GET /health` - Health check
- `POST /register` - Register new user
- `POST /login` - User login
- `POST /verify` - Verify JWT token
- `GET /users/<id>` - Get user information (requires auth)
- `PUT /users/<id>` - Update user (requires auth)
- `PUT /users/<id>/password` - Change password (v2.0)
- `GET /users` - List all users (admin only, v2.0)

### Order Processing Service (Port 8003)

- `GET /health` - Health check
- `POST /orders` - Create new order (requires auth)
- `GET /orders/<id>` - Get order details (requires auth)
- `GET /orders/user/<user_id>` - Get user orders (requires auth)
- `PATCH /orders/<id>/status` - Update order status (admin only)
- `PATCH /orders/<id>/payment` - Update payment status (v2.0)
- `GET /orders` - List all orders (admin only, v2.0)

## Testing the Services

### Test Product Service
```bash
# Health check
curl http://localhost:8001/health

# Create a product
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 999.99, "stock_quantity": 10, "category": "Electronics"}'

# Get all products
curl http://localhost:8001/products
```

### Test Authentication Service
```bash
# Register a user
curl -X POST http://localhost:8002/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "Test123!@#"}'

# Login
curl -X POST http://localhost:8002/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "Test123!@#"}'
```

### Test Order Service
```bash
# Create an order (use token from login)
curl -X POST http://localhost:8003/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"items": [{"product_id": 1, "quantity": 2}], "shipping_address": "123 Main St"}'
```

## Version Information

### Version 1.0 (Initial Release)
- Basic CRUD operations for all services
- Initial implementation with known bugs
- No authentication on order endpoints
- Missing input validation
- No stock validation

### Version 2.0 (Updated Release)
- **Bug Fixes:**
  - Added authentication and authorization to all endpoints
  - Fixed input validation (price, stock, email, password)
  - Added stock validation before order creation
  - Fixed Bearer token handling
  - Added proper error handling

- **New Features:**
  - Password strength validation
  - Product pagination and sorting
  - Discount percentage support
  - Product image URLs
  - Bulk product creation
  - Order tracking numbers
  - Payment status tracking
  - Last login tracking
  - Admin-only endpoints
  - Order status filtering

## Docker Images

### Version 1.0 Images
- `ecommerce/product-service:v1.0`
- `ecommerce/auth-service:v1.0`
- `ecommerce/order-service:v1.0`

### Version 2.0 Images
- `ecommerce/product-service:v2.0`
- `ecommerce/auth-service:v2.0`
- `ecommerce/order-service:v2.0`

## Project Structure

```
.
├── docker-compose.yml          # Version 1.0 deployment
├── docker-compose.v2.yml       # Version 2.0 deployment
├── product-catalogue-service/
│   ├── app.py                  # Version 1.0
│   ├── app_v2.py              # Version 2.0
│   ├── Dockerfile             # Version 1.0
│   ├── Dockerfile.v2          # Version 2.0
│   └── requirements.txt
├── user-authentication-service/
│   ├── app.py                 # Version 1.0
│   ├── app_v2.py             # Version 2.0
│   ├── Dockerfile            # Version 1.0
│   ├── Dockerfile.v2         # Version 2.0
│   └── requirements.txt
├── order-processing-service/
│   ├── app.py                # Version 1.0
│   ├── app_v2.py            # Version 2.0
│   ├── Dockerfile           # Version 1.0
│   ├── Dockerfile.v2        # Version 2.0
│   └── requirements.txt
├── PROJECT_DOCUMENTATION.md   # Detailed documentation
└── README.md                  # This file
```

## Troubleshooting

### Services not starting
- Ensure Docker Desktop is running
- Check if ports 8001, 8002, 8003, 6379 are available
- View logs: `docker-compose logs <service-name>`

### Database connection errors
- Wait for databases to initialize (may take 10-15 seconds)
- Check database container status: `docker-compose ps`

### Authentication errors
- Ensure you're using the correct token format: `Bearer <token>`
- Check token expiration (24 hours default)

## Future Enhancements

- Payment gateway integration
- Email notifications
- Product reviews and ratings
- Shopping cart functionality
- Advanced analytics and reporting
- Kubernetes deployment configuration

## Contributors

[Your Name/Group Members]

## License

This project is created for educational purposes as part of the Virtual System and Services Lab course.



