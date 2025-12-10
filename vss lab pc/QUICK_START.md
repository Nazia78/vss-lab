# Quick Start Guide

## Prerequisites
- Docker Desktop installed and running
- Git (optional, for cloning)

## Step 1: Start Version 1.0 (Initial Version with Bugs)

```bash
# Navigate to project directory
cd "vss lab pc"

# Start all services
docker-compose up --build
```

Wait for all services to start (about 30-60 seconds). You should see:
- ✅ Product Catalogue Service running on port 8001
- ✅ User Authentication Service running on port 8002
- ✅ Order Processing Service running on port 8003
- ✅ Three PostgreSQL databases
- ✅ Redis cache

## Step 2: Test Version 1.0

### Test Product Service
```bash
# Health check
curl http://localhost:8001/health

# Create a product (Note: v1.0 allows negative prices - this is a bug!)
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "price": -10, "stock_quantity": 5}'
```

### Test Authentication Service
```bash
# Register user (Note: v1.0 accepts weak passwords - this is a bug!)
curl -X POST http://localhost:8002/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "email": "user1@test.com", "password": "123"}'

# Login
curl -X POST http://localhost:8002/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "123"}'
# Save the token from the response
```

### Test Order Service (Note: v1.0 doesn't require authentication - this is a bug!)
```bash
# Create order without authentication (should work in v1.0, but is a security issue)
curl -X POST http://localhost:8003/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "items": [{"product_id": 1, "quantity": 10}], "shipping_address": "123 Main St"}'
```

## Step 3: Stop Version 1.0

```bash
# Press Ctrl+C or in another terminal:
docker-compose down
```

## Step 4: Start Version 2.0 (Updated Version with Fixes)

```bash
# Start v2.0 services
docker-compose -f docker-compose.v2.yml up --build
```

## Step 5: Test Version 2.0 (Fixed Version)

### Test Product Service (Fixed)
```bash
# Try to create product with negative price (should fail now!)
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "price": -10, "stock_quantity": 5}'
# Should return error: "Price must be a positive number"

# Create product with valid data
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 999.99, "stock_quantity": 10, "category": "Electronics", "discount_percentage": 10}'

# Get products with pagination (new feature!)
curl "http://localhost:8001/products?page=1&per_page=5&sort_by=price&sort_order=asc"
```

### Test Authentication Service (Fixed)
```bash
# Try to register with weak password (should fail now!)
curl -X POST http://localhost:8002/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user2", "email": "user2@test.com", "password": "123"}'
# Should return error about password strength

# Register with strong password
curl -X POST http://localhost:8002/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user2", "email": "user2@test.com", "password": "SecurePass123!@#"}'

# Login and save token
TOKEN=$(curl -s -X POST http://localhost:8002/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user2", "password": "SecurePass123!@#"}' | grep -o '"token":"[^"]*' | cut -d'"' -f4)

echo "Token: $TOKEN"
```

### Test Order Service (Fixed - Now Requires Authentication)
```bash
# Try to create order without token (should fail now!)
curl -X POST http://localhost:8003/orders \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": 2}], "shipping_address": "123 Main St"}'
# Should return: "Authentication required"

# Create order with authentication (use token from login)
curl -X POST http://localhost:8003/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"items": [{"product_id": 1, "quantity": 2}], "shipping_address": "123 Main St"}'

# Get user orders (requires authentication)
curl -X GET http://localhost:8003/orders/user/1 \
  -H "Authorization: Bearer $TOKEN"
```

## Step 6: View Docker Images

```bash
# List all images
docker images | grep ecommerce

# You should see:
# ecommerce/product-service:v1.0
# ecommerce/product-service:v2.0
# ecommerce/auth-service:v1.0
# ecommerce/auth-service:v2.0
# ecommerce/order-service:v1.0
# ecommerce/order-service:v2.0
```

## Step 7: View Logs

```bash
# View logs for v2.0
docker-compose -f docker-compose.v2.yml logs -f

# View logs for specific service
docker-compose -f docker-compose.v2.yml logs -f product-service
```

## Step 8: Stop Services

```bash
# Stop v2.0
docker-compose -f docker-compose.v2.yml down

# Or stop v1.0
docker-compose down
```

## Troubleshooting

### Port Already in Use
If you get "port already in use" error:
```bash
# Find process using the port
netstat -ano | findstr :8001

# Or stop all containers
docker-compose down
docker-compose -f docker-compose.v2.yml down
```

### Services Not Starting
```bash
# Check Docker Desktop is running
# Check logs for errors
docker-compose -f docker-compose.v2.yml logs

# Rebuild from scratch
docker-compose -f docker-compose.v2.yml down -v
docker-compose -f docker-compose.v2.yml up --build
```

### Database Connection Errors
Wait 10-15 seconds after starting services for databases to initialize.

## Next Steps

1. Read `README.md` for detailed API documentation
2. Read `PROJECT_DOCUMENTATION.md` for comprehensive project details
3. Review `CHANGELOG.md` for all changes between versions
4. Explore the code in `app.py` (v1.0) and `app_v2.py` (v2.0) to see the differences

## Summary of Key Differences

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Authentication on orders | ❌ | ✅ |
| Password validation | ❌ | ✅ |
| Stock validation | ❌ | ✅ |
| Price validation | ❌ | ✅ |
| Pagination | ❌ | ✅ |
| Discounts | ❌ | ✅ |
| Tracking numbers | ❌ | ✅ |
| Payment status | ❌ | ✅ |



