# PulseNotify Documentation Hub

This folder contains the implementation, operations, delivery, and infrastructure guides for PulseNotify.

## Intended Audience

- Backend engineers extending API and Celery logic.
- DevOps engineers managing GitHub Actions and Terraform deployments.
- QA engineers validating API behavior from Swagger and Postman.
- Support engineers troubleshooting runtime and deployment incidents.

## Documentation Map

1. [Architecture](architecture.md)
	- system components, data flow, trust boundaries, and deployment topology
2. [API and Swagger Testing](api-swagger-testing.md)
	- endpoint validation workflow, JWT auth flow, and Postman collection usage
3. [Pipelines](pipelines.md)
	- validation, test, build/deploy, and Terraform pipeline behavior
4. [Terraform Infra Deployment](infra-deployment.md)
	- module layout, variables, plan/apply flow, and rollback notes
5. [Testing Strategy](testing-strategy.md)
	- test layers, coverage intent, and CI quality gates
6. [Operations Runbook](operations-runbook.md)
	- startup, health checks, observability, and incident response playbooks

## Quick Start Paths

- Local app startup: `./start_local.ps1`
- API docs UI: `/api/docs/`
- OpenAPI schema: `/api/schema/`
- Health check endpoint: `/api/health/`
- Terraform root: `infra/terraform/environments/dev/`
- Workflow definitions: `.github/workflows/`

## Source of Truth and Change Management

- Keep docs in sync with code changes in the same pull request.
- For behavioral API changes, update:
  - this docs index
  - `docs/api-swagger-testing.md`
  - Postman collection in `postman/PulseNotify.postman_collection.json`
- For infrastructure changes, update:
  - `docs/infra-deployment.md`
  - `docs/pipelines.md`
  - affected Terraform module README/comments if introduced

## Related Project Files

- Main overview: `README.md`
- Local/cloud setup checklist: `setup.md`
- Postman collection: `postman/PulseNotify.postman_collection.json`

## Read Order for New Contributors

1. Start with `README.md` in repo root for high-level context.
2. Read `setup.md` to bootstrap local/cloud environments.
3. Read `docs/architecture.md` to understand runtime responsibilities.
4. Read `docs/api-swagger-testing.md` before changing API contracts.
5. Read `docs/pipelines.md` and `docs/infra-deployment.md` before CI/IaC changes.
6. Use `docs/operations-runbook.md` during incidents or release support.

## Definition of Done for Documentation Changes

- Any API behavior change updates endpoint and status code documentation.
- Any pipeline logic change updates trigger and secret requirements.
- Any Terraform variable/module change updates infra documentation.
- Any operational behavior change updates runbook and troubleshooting sections.

## Maintenance Cadence

- Review docs on each feature merge touching API, infra, or pipelines.
- Run a monthly docs quality pass to remove stale commands and references.
- Keep command snippets copy-paste ready for PowerShell users.
