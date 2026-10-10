# Testing Strategy

## Test Layers

1. Unit tests
- Model behavior and pure logic checks.
- Fast checks for threshold logic and model linking.

2. API tests
- Register/login flow.
- Auth boundary checks.
- Alert ownership/scoping validation.
- Admin-only authorization checks.

3. Runtime checks
- `manage.py check`
- Migration drift check
- OpenAPI generation checks through schema endpoint smoke validation.

4. Infrastructure checks
- Terraform format validation
- Terraform configuration validation
- Plan generation in CI for infra changes

## Test Ownership

- API behavior and auth tests: backend team
- Pipeline and release verification: DevOps team
- Infra module validation: platform/infra owners

## Current Commands

```powershell
python manage.py test -v 2
python manage.py check
python manage.py makemigrations --check --dry-run
```

Optional command for compile-time sanity:

```powershell
python -m compileall manage.py api pulse
```

## CI Coverage

- Validation pipeline executes compile and configuration checks.
- Test pipeline executes Django tests in Python-version matrix.
- Infra pipeline validates Terraform and creates plan output.

## What Is Explicitly Covered Today

- registration/login success and failure paths
- duplicate username handling
- alert scoping to authenticated user
- authorization requirements for alert creation
- admin summary role behavior
- mock flight route valid/invalid responses

## What Is Manual or Environment-Dependent

- Celery beat to worker to NotificationLog runtime loop
- PostgreSQL table inspection in PGAdmin
- cloud deploy smoke checks after App Service rollout

## Recommended Enhancements

- Add contract tests that compare API responses against OpenAPI schema.
- Add Celery integration tests with eager mode enabled in test settings.
- Add performance smoke tests for high alert volume routes.
- Add a lightweight deploy smoke test hitting `/api/health/` post-deploy.
