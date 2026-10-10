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

## Quality Gates by Change Type

- API behavior change:
	- unit/API tests updated
	- Postman collection updated
	- Swagger docs reviewed
- Celery/task change:
	- unit tests for edge cases
	- manual async verification in local or dev
- Infra change:
	- terraform validate and plan reviewed
	- environment variable compatibility verified

## PR Exit Criteria

1. Relevant tests pass in CI.
2. No unresolved migration drift for model changes.
3. Documentation updated when behavior changes.
4. Manual checks documented when full automation is not feasible.

## Regression Focus Areas

- authentication and authorization boundaries
- user-level data isolation on alert list/delete
- admin summary role enforcement
- scheduler-to-worker notification path
- DB schema compatibility after model changes
