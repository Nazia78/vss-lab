# Step-by-Step Demo Guide for Teacher

## Prerequisites Check
```powershell
# Make sure Docker Desktop is running
docker --version
docker-compose --version
```

---

## PART 1: Show Version 1.0 (Initial Version with Bugs)

### Step 1: Navigate to Project Directory
```powershell
cd "C:\Users\user\Desktop\vss lab pc"
```

### Step 2: Start Version 1.0 Services
```powershell
docker-compose up --build
```
**Wait 30-60 seconds for all services to start**

### Step 3: Verify Services Are Running
```powershell
# Open a NEW PowerShell window and run:
docker ps
```

### Step 4: Test Health Endpoints
```powershell
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### Step 5: Demonstrate Bug #1 - Negative Price Accepted
```powershell
curl -Method POST -Uri http://localhost:8001/products -ContentType "application/json" -Body '{"name": "Test Product", "price": -10, "stock_quantity": 5, "category": "Test"}'
```
**Show:** Product created with negative price (-10.0) - THIS IS A BUG!

### Step 6: Demonstrate Bug #2 - Weak Password Accepted
```powershell
curl -Method POST -Uri http://localhost:8002/register -ContentType "application/json" -Body '{"username": "user1", "email": "user1@test.com", "password": "123"}'
```
**Show:** User registered with weak password "123" - THIS IS A BUG!

### Step 7: Demonstrate Bug #3 - Order Without Authentication
```powershell
curl -Method POST -Uri http://localhost:8003/orders -ContentType "application/json" -Body '{"user_id": 1, "items": [{"product_id": 1, "quantity": 2}], "shipping_address": "123 Main St"}'
```
**Show:** Order created without any authentication - SECURITY BUG!

### Step 8: Stop Version 1.0
```powershell
# In the window where docker-compose is running, press Ctrl+C
# Then run:
docker-compose down
```

---

## PART 2: Show Version 2.0 (Fixed Version)

### Step 9: Start Version 2.0 Services
```powershell
docker-compose -f docker-compose.v2.yml up --build -d
```
**Wait 30-60 seconds for services to start**

### Step 10: Verify Version 2.0 Services
```powershell
# Check health endpoints show version 2.0
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```
**Show:** All services show `"version": "2.0"`

### Step 11: Demonstrate Bug #1 FIXED - Negative Price Rejected
```powershell
curl -Method POST -Uri http://localhost:8001/products -ContentType "application/json" -Body '{"name": "Test Product", "price": -10, "stock_quantity": 5, "category": "Test"}'
```
**Show:** Error message: "Price must be a positive number" - BUG FIXED!

### Step 12: Demonstrate Bug #2 FIXED - Weak Password Rejected
```powershell
curl -Method POST -Uri http://localhost:8002/register -ContentType "application/json" -Body '{"username": "user2", "email": "user2@test.com", "password": "123"}'
```
**Show:** Error message: "Password must be at least 8 characters long" - BUG FIXED!

### Step 13: Demonstrate Bug #3 FIXED - Authentication Required
```powershell
curl -Method POST -Uri http://localhost:8003/orders -ContentType "application/json" -Body '{"items": [{"product_id": 1, "quantity": 2}], "shipping_address": "123 Main St"}'
```
**Show:** Error message: "Authentication required" - BUG FIXED!

### Step 14: Demonstrate New Features - Create Valid Product
```powershell
curl -Method POST -Uri http://localhost:8001/products -ContentType "application/json" -Body '{"name": "Laptop", "price": 999.99, "stock_quantity": 10, "category": "Electronics", "discount_percentage": 10, "image_url": "https://example.com/laptop.jpg"}'
```
**Show:** Product created with discount, image URL, and proper validation

### Step 15: Demonstrate New Features - Register with Strong Password
```powershell
curl -Method POST -Uri http://localhost:8002/register -ContentType "application/json" -Body '{"username": "user2", "email": "user2@test.com", "password": "SecurePass123!@#"}'
```
**Show:** User registered successfully with strong password. **SAVE THE TOKEN from response!**

### Step 16: Demonstrate New Features - Pagination and Sorting
```powershell
curl "http://localhost:8001/products?page=1&per_page=5&sort_by=price&sort_order=asc"
```
**Show:** Response includes pagination metadata and sorted results

### Step 17: Demonstrate New Features - Create Order with Authentication
```powershell
# Use the token from Step 15 (replace YOUR_TOKEN_HERE)
curl -Method POST -Uri http://localhost:8003/orders -ContentType "application/json" -Headers @{"Authorization"="Bearer YOUR_TOKEN_HERE"} -Body '{"items": [{"product_id": 1, "quantity": 2}], "shipping_address": "123 Main St"}'
```
**Show:** Order created successfully with authentication, using discounted price

### Step 18: Show Docker Images with Version Tags
```powershell
docker images | Select-String "ecommerce"
```
**Show:** 
- `ecommerce/product-service:v1.0`
- `ecommerce/product-service:v2.0`
- `ecommerce/auth-service:v1.0`
- `ecommerce/auth-service:v2.0`
- `ecommerce/order-service:v1.0`
- `ecommerce/order-service:v2.0`

### Step 19: Show Running Containers
```powershell
docker ps
```
**Show:** All containers running with v2.0

### Step 20: Stop Version 2.0
```powershell
docker-compose -f docker-compose.v2.yml down
```

---

## Quick Reference Commands

### View Logs
```powershell
# View all logs
docker-compose -f docker-compose.v2.yml logs -f

# View specific service
docker-compose -f docker-compose.v2.yml logs -f product-service
```

### Check Service Status
```powershell
docker-compose -f docker-compose.v2.yml ps
```

### View All Containers
```powershell
docker ps -a
```

### Clean Up Everything
```powershell
docker-compose down -v
docker-compose -f docker-compose.v2.yml down -v
```

---

## Key Points to Explain to Teacher

1. **Version 1.0 Issues:**
   - No input validation (negative prices accepted)
   - Weak password policy
   - Missing authentication on order endpoints
   - Security vulnerabilities

2. **Version 2.0 Fixes:**
   - All bugs fixed
   - Proper authentication and authorization
   - Input validation implemented
   - Enhanced security

3. **New Features Added:**
   - Product pagination and sorting
   - Discount system
   - Payment status tracking
   - Order tracking numbers
   - Password strength validation
   - And more...

4. **Docker Images:**
   - Both versions tagged properly (v1.0 and v2.0)
   - Can run either version independently
   - Proper version control

---

## Troubleshooting

If services don't start:
```powershell
# Check Docker is running
docker ps

# Check logs
docker-compose -f docker-compose.v2.yml logs

# Restart services
docker-compose -f docker-compose.v2.yml restart
```

If database errors occur:
```powershell
# Recreate databases
docker-compose -f docker-compose.v2.yml down -v
docker-compose -f docker-compose.v2.yml up -d
```



