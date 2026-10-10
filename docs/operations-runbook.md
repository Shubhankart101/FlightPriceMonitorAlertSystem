# Operations Runbook

## Local Startup

```powershell
.\start_local.ps1
```

Optional with Docker services:

```powershell
.\start_local.ps1 -UseDockerServices
```

## Service Startup (manual)

1. API: `python manage.py runserver`
2. Worker: `celery -A pulse worker -l info`
3. Scheduler: `celery -A pulse beat -l info`

## Health and Diagnostics

- API health: `GET /api/health/`
- Swagger docs: `GET /api/docs/`
- OpenAPI schema: `GET /api/schema/`

## Common Operational Checks

- Check pending migrations:
  `python manage.py makemigrations --check --dry-run`
- Check app config:
  `python manage.py check`
- Run tests:
  `python manage.py test -v 2`

## Incident Notes

- If price checks are not triggering, verify Redis connectivity and Celery worker logs first.
- If admin summary returns 403 for admin users, verify user profile role is `admin`.
- If deployment fails, inspect the corresponding GitHub Actions run and Terraform plan artifacts.
