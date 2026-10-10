# API and Swagger Testing

## Swagger Enablement

Swagger and OpenAPI are enabled via DRF Spectacular:

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`

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

## Suggested Postman Regression Set

- Register and duplicate-register checks
- Login valid/invalid
- Create alert with and without token
- List alerts per user
- Deactivate own alert and foreign alert access denial
- Mock price endpoint valid and invalid route
- Admin summary with USER (403) and ADMIN (200)

## CI Validation Hooks

GitHub validation pipeline executes:

- Django system checks
- Migration drift check (`makemigrations --check --dry-run`)
- Python compile check
