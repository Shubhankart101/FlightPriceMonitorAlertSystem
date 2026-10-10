# Operations Runbook

## Local Startup

```powershell
.\start_local.ps1
```

Optional with Docker services:

```powershell
.\start_local.ps1 -UseDockerServices
```

## Environment Preparation

1. Ensure `.env` exists (copy from `.env.example` if needed).
2. Ensure Docker Desktop is running when using Redis/PostgreSQL containers.
3. Activate virtual environment before manual commands.

## Service Startup (manual)

1. API: `python manage.py runserver`
2. Worker: `celery -A pulse worker -l info`
3. Scheduler: `celery -A pulse beat -l info`

## Service Restart Procedure

1. Stop API, worker, and beat processes.
2. Restart Redis/PostgreSQL if container-backed:
   - `docker compose restart redis db`
3. Re-run migrations if schema changed:
   - `python manage.py migrate`
4. Start API, then worker, then beat.

## Health and Diagnostics

- API health: `GET /api/health/`
- Swagger docs: `GET /api/docs/`
- OpenAPI schema: `GET /api/schema/`

## Logging Focus Areas

- API terminal:
  - authentication failures
  - serializer validation errors
- Worker terminal:
  - task dispatch and execution errors
  - request failures to mock price endpoint
- Beat terminal:
  - periodic scheduler ticks
  - task send activity

## Common Operational Checks

- Check pending migrations:
  `python manage.py makemigrations --check --dry-run`
- Check app config:
  `python manage.py check`
- Run tests:
  `python manage.py test -v 2`

## Database Checks

- Confirm alert row states:
  - `active` before trigger
  - `triggered` after notification
- Confirm notification history:
  - inspect `NotificationLog` rows and timestamps

## Celery Validation Procedure

1. Create an alert with reachable route and threshold above likely random price.
2. Wait at least one beat interval (60 seconds).
3. Confirm worker logs show `send_notification` execution.
4. Verify `NotificationLog` row exists.

## Incident Notes

- If price checks are not triggering, verify Redis connectivity and Celery worker logs first.
- If admin summary returns 403 for admin users, verify user profile role is `admin`.
- If deployment fails, inspect the corresponding GitHub Actions run and Terraform plan artifacts.

## Common Incident Playbooks

### Incident: alerts not triggering

- Check beat process is running.
- Check worker process is connected to Redis.
- Verify `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`.
- Verify route exists in `MOCK_PRICES`.

### Incident: API returns 500 on protected endpoints

- Check JWT auth settings and token expiry.
- Check migrations are applied.
- Check `.env` values for DB and secret key.

### Incident: deploy pipeline succeeds but app unhealthy

- Verify container image tag deployed is expected SHA.
- Verify Azure app settings include required env vars.
- Verify DB and Redis connectivity from app runtime.

## Preflight Checklist Before Any Release

1. Confirm target branch has passed validation and test workflows.
2. Confirm no pending migration drift.
3. Confirm required secrets are present in CI environment.
4. Confirm Terraform plan was reviewed for infra-related changes.

## Command Cheatsheet

```powershell
# App checks
python manage.py check
python manage.py test -v 2
python manage.py makemigrations --check --dry-run

# Services
docker compose up -d
docker compose ps
docker compose logs redis
docker compose logs db

# Celery
celery -A pulse worker -l info
celery -A pulse beat -l info
```

## Escalation Guidance

- Escalate to backend owner when:
  - API errors reproduce locally with valid config
- Escalate to DevOps owner when:
  - GitHub Actions or deploy workflows fail consistently
- Escalate to infra owner when:
  - Terraform apply fails due to provider/state/resource policy issues
