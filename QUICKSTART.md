# Quick Start Guide

## Initial Setup

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file** with your configuration (at minimum, set a strong SECRET_KEY)

3. **Start the services:**
   ```bash
   docker-compose up --build
   ```

4. **Run migrations** (in a new terminal):
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Create superuser** (optional):
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## Access Points

- **Django API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **n8n**: http://localhost:5678 (admin/admin123)
- **Health Check**: http://localhost:8000/health/

## Testing the API

### Register a User (Customer)
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/user/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "phone_number": "+1234567890",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Register a Courier
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/courier/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "courier@example.com",
    "phone_number": "+1234567891",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "Jane",
    "last_name": "Driver"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Access Protected Endpoint
```bash
curl -X GET http://localhost:8000/api/v1/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## n8n Setup

1. Access n8n at http://localhost:5678
2. Login with credentials (admin/admin123)
3. Create workflows that can:
   - Call Django webhook: `POST http://web:8000/api/v1/automation/webhook/`
   - Be triggered from Django using workflow IDs

## Project Structure

- `apps/accounts/` - User authentication and management
- `apps/users/` - Customer-specific features
- `apps/couriers/` - Courier-specific features
- `apps/automation/` - n8n integration
- `apps/core/` - Shared utilities

## Next Steps

1. Add your business models (orders, deliveries, etc.)
2. Configure n8n workflows for your automation needs
3. Set up production environment variables
4. Configure CI/CD pipeline
5. Add API documentation (Swagger/OpenAPI)

