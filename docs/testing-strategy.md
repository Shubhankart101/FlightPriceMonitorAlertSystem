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

## Current Commands

```powershell
python manage.py test -v 2
python manage.py check
python manage.py makemigrations --check --dry-run
```

## CI Coverage

- Validation pipeline executes compile and configuration checks.
- Test pipeline executes Django tests in Python-version matrix.

## Recommended Enhancements

- Add contract tests that compare API responses against OpenAPI schema.
- Add Celery integration tests with eager mode enabled in test settings.
- Add performance smoke tests for high alert volume routes.
