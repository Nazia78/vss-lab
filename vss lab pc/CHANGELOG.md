# Changelog

All notable changes to the E-commerce Microservices Application will be documented in this file.

## [2.0.0] - 2025-12-XX

### Added

#### Product Catalogue Service
- Pagination support for product listing (`page`, `per_page` parameters)
- Sorting capabilities (by price, name, creation date)
- Discount percentage field and automatic discounted price calculation
- Product image URL support
- Bulk product creation endpoint (`POST /products/bulk`)
- Enhanced input validation with detailed error messages
- `updated_at` timestamp tracking

#### User Authentication Service
- Password strength validation (8+ chars, uppercase, lowercase, digit, special char)
- Email format validation
- Password change endpoint (`PUT /users/<id>/password`)
- Last login timestamp tracking
- Admin user listing endpoint (`GET /users`)
- Role-based access control (RBAC) decorators
- Password reset token fields (for future implementation)

#### Order Processing Service
- Payment status tracking (`pending`, `paid`, `failed`, `refunded`)
- Automatic tracking number generation when order is shipped
- Order notes field for additional information
- Product name storage in order items for historical reference
- Order status filtering (`GET /orders/user/<id>?status=<status>`)
- Admin endpoint to list all orders (`GET /orders`)
- Payment status update endpoint (`PATCH /orders/<id>/payment`)
- Real-time stock validation before order creation
- Automatic stock updates after order creation
- Discount price support (uses discounted price if available)

### Fixed

#### Product Catalogue Service
- Fixed: Negative price validation (now rejects negative prices)
- Fixed: Negative stock validation (now rejects negative stock)
- Fixed: Empty product name validation
- Fixed: Input sanitization for product names

#### User Authentication Service
- Fixed: Bearer token parsing (properly handles "Bearer " prefix)
- Fixed: Missing authentication on user endpoints (`GET /users/<id>`, `PUT /users/<id>`)
- Fixed: Missing authorization checks (users can only access their own data)
- Fixed: Weak password policy (now enforces strong passwords)
- Fixed: Missing email format validation

#### Order Processing Service
- Fixed: Missing authentication on all order endpoints
- Fixed: Missing authorization (users can only access their own orders)
- Fixed: Stock not validated before order creation
- Fixed: Stock not updated after order creation
- Fixed: Users can view/modify any order (now requires proper authorization)
- Fixed: Admin-only operations now properly protected

### Security
- Added authentication decorator (`@require_auth`) for protected endpoints
- Added role-based authorization checks
- Implemented proper token validation
- Added input validation to prevent injection attacks
- Enhanced error messages without exposing sensitive information

### Changed
- All services now return version information in health check endpoint
- Improved error messages with more descriptive information
- Enhanced API responses with additional metadata

## [1.0.0] - 2025-12-XX

### Added
- Initial release of E-commerce Microservices Application
- Product Catalogue Service with basic CRUD operations
- User Authentication Service with registration and login
- Order Processing Service with order management
- Redis caching for product service
- PostgreSQL databases for each service
- Docker Compose configuration for easy deployment

### Known Issues
- Missing authentication on order endpoints
- No input validation for prices and stock
- Missing stock validation during order creation
- Weak password policy
- Missing email validation
- Bearer token parsing issues
- No authorization checks on user endpoints



