# API and Swagger Testing

## Swagger Enablement

Swagger and OpenAPI are enabled via DRF Spectacular:

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`

## API Base URL

- Local default: `http://127.0.0.1:8000`
- API prefix: `/api/`

## Local API Verification

1. Start app locally:

```powershell
.\start_local.ps1
```

2. Open Swagger UI:

```text
http://127.0.0.1:8000/api/docs/
```

3. Register user:

- `POST /api/auth/register/`
- Save `access` token.

4. Authorize in Swagger:

- Click `Authorize`
- Provide `Bearer <access-token>`

5. Run key scenarios:

- `POST /api/alerts/` create alert.
- `GET /api/alerts/` validate own alerts.
- `DELETE /api/alerts/{id}/` deactivate alert.
- `GET /api/admin/summary/` verify role-based protection.

## Minimal End-to-End Manual Flow

1. Register user and capture JWT token.
2. Authorize token in Swagger UI.
3. Create one alert (`DEL -> BOM`).
4. List alerts and note returned `id`.
5. Delete alert by id and verify status response.
6. Call mock route with valid and invalid route.
7. Call admin summary as regular user and confirm `403`.

## Expected Status Codes

- Register success: `201`
- Register duplicate: `400`
- Login success: `200`
- Login invalid credentials: `401`
- Create alert without token: `401`
- Create alert with token: `201`
- List own alerts: `200`
- Deactivate own alert: `200`
- Mock price valid: `200`
- Mock price invalid route: `404`
- Admin summary regular user: `403`
- Admin summary admin user: `200`

## Postman Collection

- File: `postman/PulseNotify.postman_collection.json`
- Variables expected:
	- `baseUrl`
	- `accessToken`
	- `adminToken`
	- `alertId`

## Creating an Admin Test User

Use Django shell to promote a user profile role:

```powershell
python manage.py shell
```

```python
from django.contrib.auth.models import User
u = User.objects.get(username="demo_user")
u.profile.role = "admin"
u.profile.save()
```

## Common API Testing Failures

- `401 Unauthorized` on protected endpoints:
	- token missing or malformed
	- token belongs to deleted user
- `403 Forbidden` on admin summary:
	- user is authenticated but role is not `admin`
- `400` on register:
	- duplicate username or weak/invalid payload
- `404` on mock price route:
	- route not in `MOCK_PRICES`

## Suggested Postman Regression Set

- Register and duplicate-register checks
- Login valid/invalid
- Create alert with and without token
- List alerts per user
- Deactivate own alert and foreign alert access denial
- Mock price endpoint valid and invalid route
- Admin summary with USER (403) and ADMIN (200)
- Notification log verification through DB after Celery processing

## CI Validation Hooks

GitHub validation pipeline executes:

- Django system checks
- Migration drift check (`makemigrations --check --dry-run`)
- Python compile check

The dedicated test pipeline executes Django test suite in a Python matrix to detect runtime differences across versions.
