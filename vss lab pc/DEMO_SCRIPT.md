# Live Demo Script - Copy & Paste Commands

## 🎯 DEMO SCRIPT FOR TEACHER

---

## SETUP (Do this first)

```powershell
# 1. Open PowerShell
# 2. Navigate to project
cd "C:\Users\user\Desktop\vss lab pc"

# 3. Make sure Docker Desktop is running
docker ps
```

---

## 📦 PART 1: VERSION 1.0 (Show Bugs)

### Start Version 1.0
```powershell
docker-compose up --build
```
**Wait 1 minute, then open NEW PowerShell window for commands below**

### Test Health
```powershell
curl http://localhost:8001/health
curl http://localhost:8002/health  
curl http://localhost:8003/health
```

### 🐛 BUG #1: Negative Price Accepted
```powershell
curl -Method POST -Uri http://localhost:8001/products -ContentType "application/json" -Body '{"name": "Test", "price": -10, "stock_quantity": 5}'
```
**TEACHER: See? It accepts -10.00 price! BUG!**

### 🐛 BUG #2: Weak Password Accepted  
```powershell
curl -Method POST -Uri http://localhost:8002/register -ContentType "application/json" -Body '{"username": "user1", "email": "u1@test.com", "password": "123"}'
```
**TEACHER: See? Password "123" accepted! BUG!**

### 🐛 BUG #3: Order Without Auth
```powershell
curl -Method POST -Uri http://localhost:8003/orders -ContentType "application/json" -Body '{"user_id": 1, "items": [{"product_id": 1, "quantity": 2}], "shipping_address": "123 St"}'
```
**TEACHER: See? Order created without login! SECURITY BUG!**

### Stop v1.0
```powershell
# In docker-compose window: Press Ctrl+C
# Then:
docker-compose down
```

---

## ✅ PART 2: VERSION 2.0 (Show Fixes)

### Start Version 2.0
```powershell
docker-compose -f docker-compose.v2.yml up --build -d
```
**Wait 1 minute**

### Check Version
```powershell
curl http://localhost:8001/health
```
**TEACHER: See "version": "2.0"?**

### ✅ FIX #1: Negative Price REJECTED
```powershell
curl -Method POST -Uri http://localhost:8001/products -ContentType "application/json" -Body '{"name": "Test", "price": -10, "stock_quantity": 5}'
```
**TEACHER: See error? "Price must be positive" - FIXED!**

### ✅ FIX #2: Weak Password REJECTED
```powershell
curl -Method POST -Uri http://localhost:8002/register -ContentType "application/json" -Body '{"username": "user2", "email": "u2@test.com", "password": "123"}'
```
**TEACHER: See error? "Password must be 8+ chars" - FIXED!**

### ✅ FIX #3: Auth Required
```powershell
curl -Method POST -Uri http://localhost:8003/orders -ContentType "application/json" -Body '{"items": [{"product_id": 1, "quantity": 2}]}'
```
**TEACHER: See error? "Authentication required" - FIXED!**

### 🆕 NEW FEATURE: Create Valid Product
```powershell
curl -Method POST -Uri http://localhost:8001/products -ContentType "application/json" -Body '{"name": "Laptop", "price": 999.99, "stock_quantity": 10, "category": "Electronics", "discount_percentage": 10}'
```
**TEACHER: See discount_percentage? NEW FEATURE!**

### 🆕 NEW FEATURE: Register with Strong Password
```powershell
curl -Method POST -Uri http://localhost:8002/register -ContentType "application/json" -Body '{"username": "user2", "email": "u2@test.com", "password": "SecurePass123!@#"}'
```
**TEACHER: See? Strong password accepted! Copy the TOKEN from response!**

### 🆕 NEW FEATURE: Pagination
```powershell
curl "http://localhost:8001/products?page=1&per_page=5&sort_by=price"
```
**TEACHER: See pagination metadata? NEW FEATURE!**

### 🆕 NEW FEATURE: Order with Auth
```powershell
# Replace YOUR_TOKEN with token from above
curl -Method POST -Uri http://localhost:8003/orders -ContentType "application/json" -Headers @{"Authorization"="Bearer YOUR_TOKEN"} -Body '{"items": [{"product_id": 1, "quantity": 2}], "shipping_address": "123 St"}'
```
**TEACHER: See? Order created with auth! Uses discounted price!**

### Show Docker Images
```powershell
docker images | Select-String "ecommerce"
```
**TEACHER: See v1.0 and v2.0 images? Proper versioning!**

---

## 🎬 CLOSING

### Stop Everything
```powershell
docker-compose -f docker-compose.v2.yml down
```

---

## 📝 WHAT TO SAY TO TEACHER

1. **"I created a Dockerized e-commerce app with 3 microservices"**
2. **"Version 1.0 had 8 bugs - I showed you 3"**
3. **"Version 2.0 fixes all bugs and adds 17 new features"**
4. **"All Docker images are properly tagged with version numbers"**
5. **"I have complete documentation in PROJECT_DOCUMENTATION.md"**

---

## ⚡ QUICK COPY-PASTE (All in one)

```powershell
# V1.0
cd "C:\Users\user\Desktop\vss lab pc"
docker-compose up --build
# Wait, then new window:
curl http://localhost:8001/health
curl -Method POST -Uri http://localhost:8001/products -ContentType "application/json" -Body '{"name": "Test", "price": -10, "stock_quantity": 5}'
curl -Method POST -Uri http://localhost:8002/register -ContentType "application/json" -Body '{"username": "u1", "email": "u1@test.com", "password": "123"}'
curl -Method POST -Uri http://localhost:8003/orders -ContentType "application/json" -Body '{"user_id": 1, "items": [{"product_id": 1, "quantity": 2}]}'
docker-compose down

# V2.0
docker-compose -f docker-compose.v2.yml up --build -d
# Wait 1 min
curl http://localhost:8001/health
curl -Method POST -Uri http://localhost:8001/products -ContentType "application/json" -Body '{"name": "Test", "price": -10, "stock_quantity": 5}'
curl -Method POST -Uri http://localhost:8002/register -ContentType "application/json" -Body '{"username": "u2", "email": "u2@test.com", "password": "123"}'
curl -Method POST -Uri http://localhost:8003/orders -ContentType "application/json" -Body '{"items": [{"product_id": 1, "quantity": 2}]}'
curl -Method POST -Uri http://localhost:8001/products -ContentType "application/json" -Body '{"name": "Laptop", "price": 999.99, "stock_quantity": 10, "discount_percentage": 10}'
curl -Method POST -Uri http://localhost:8002/register -ContentType "application/json" -Body '{"username": "u2", "email": "u2@test.com", "password": "SecurePass123!@#"}'
curl "http://localhost:8001/products?page=1&per_page=5"
docker images | Select-String "ecommerce"
```



