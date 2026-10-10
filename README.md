# PulseNotify - Flight Price Monitor Alert System

PulseNotify is a backend service for monitoring flight prices and sending alerts when a target price is reached. It continuously checks prices in the background and fires a notification the moment a target is hit, similar to Google Flights alerts or Skyscanner price notifications.

## Project Brief

### 1. Scenario
Users set price alerts for routes they care about (e.g., Delhi to Mumbai, Bangalore to Hyderabad). They set a threshold price ("If the price drops below ₹X, notify me"). PulseNotify runs in the background, continuously checking prices, and fires a notification when a target is hit.

### 2. Context
PulseNotify needs to perform three tasks well:
1.  **Instant Response:** Respond instantly when a user submits a price alert, without waiting for the system to finish checking prices.
2.  **Automatic Price Checking:** Wake up every 60 seconds, check the current price for every active alert, and decide whether to fire a notification (using Celery Beat).
3.  **Internal Price Feed:** Call its own internal mock price feed to get current prices using the `requests` library.

### 3. How It Works (The Complete Flow)
1.  User sets alert: `route=DEL-BOM`, `threshold=₹4500`
2.  `POST /api/alerts/` -> PriceAlert saved to DB
3.  Celery Beat fires every 60 seconds
4.  `check_prices` task wakes up
5.  `GET /api/flights/price/?route=DEL-BOM` (calls own mock endpoint)
6.  Mock endpoint returns `{ "route": "DEL-BOM", "price": 4200 }`
7.  Check: `4200 <= 4500` (threshold)? YES
8.  `send_notification.delay()` (async Celery task fires)
9.  NotificationLog written to DB
10. `GET /api/admin/summary/` -> Admin sees stats

There are two Celery tasks:
*   `check_prices`: Runs on a schedule (Celery Beat). Fetches current price, compares against active alerts, fires `send_notification` if threshold is met.
*   `send_notification`: Runs asynchronously (`.delay()`). Writes a NotificationLog entry to the database.

## Data Models

The following data models are implemented:

### UserProfile
Extends Django's built-in User model using a OneToOneField. Includes a `role` field (Admin or User) and a `created_at` timestamp. A `post_save` signal is used to auto-create a UserProfile when a User is created.

### PriceAlert
*   `user`: ForeignKey to User
*   `origin`: CharField (e.g., 'DEL')
*   `destination`: CharField (e.g., 'BOM')
*   `threshold_price`: DecimalField
*   `status`: CharField (Active, Inactive, Triggered)
*   `created_at`: DateTimeField

### NotificationLog
*   `alert`: ForeignKey to PriceAlert
*   `triggered_price`: DecimalField
*   `message`: TextField
*   `notified_at`: DateTimeField

## Endpoints

### Public Endpoints (No JWT required)
1.  `POST /api/auth/register/`: Creates a new user and returns a JWT access token.
2.  `POST /api/auth/login/`: Validates credentials and returns a fresh JWT access token.
3.  `GET /api/flights/price/`: Internal mock price feed. Accepts a `route` query parameter and returns a simulated price.

### Protected Endpoints (JWT required)
4.  `GET /api/alerts/`: Returns all PriceAlerts belonging to the logged-in user.
5.  `POST /api/alerts/`: Creates a new PriceAlert for the logged-in user.
6.  `DELETE /api/alerts/<id>/`: Sets the alert status to INACTIVE for a specific alert belonging to the logged-in user.
7.  `GET /api/admin/summary/`: Returns platform-wide statistics. Accessible only to Admin users.

## Background Jobs (Celery)
*   **`check_prices`**: Scheduled via `CELERY_BEAT_SCHEDULE` to run every 60 seconds.
*   **`send_notification`**: Called asynchronously using `.delay()` from `check_prices`.

## Environment Setup & Execution

### Prerequisites
*   Docker & Docker Compose (for Redis and PostgreSQL)
*   Python 3.8+

### Steps to Run
1.  **Clone the repository and extract the contents.**
2.  **Start Services (Redis & DB):**
    ```bash
    docker-compose up -d
    ```
3.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Run Migrations:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```
6.  **Run the application (requires 3 terminals):**
    *   **Terminal 1 (Django Server):**
        ```bash
        python manage.py runserver
        ```
    *   **Terminal 2 (Celery Worker):**
        ```bash
        celery -A pulse worker --loglevel=info
        ```
    *   **Terminal 3 (Celery Beat):**
        ```bash
        celery -A pulse beat --loglevel=info
        ```

## Local Execution Improvements

This repository now has a standard runnable Django layout:

- `pulse/` is the Django project package (settings, urls, celery).
- `api/` is the Django app package (models, views, tasks, tests).

### Quick Start (Windows PowerShell)

```powershell
.\start_local.ps1
```

### Manual Start (Windows PowerShell)

1. Create and activate a virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy env template:

```powershell
Copy-Item .env.example .env
```

4. Optional: start Redis and PostgreSQL via Docker:

```powershell
docker compose up -d
```

5. Run migrations:

```powershell
python manage.py makemigrations api
python manage.py migrate
```

6. Start the API:

```powershell
python manage.py runserver
```

API base URL: `http://127.0.0.1:8000/api/`

## Database Modes

- Default local mode uses SQLite (`DB_ENGINE=sqlite` in `.env`) so the app can run without Docker.
- To use PostgreSQL, set `DB_ENGINE=postgres` and keep DB credentials aligned with `docker-compose.yml`.

## Unit Tests
Three unit tests are included in `api/tests.py`:
1.  `PriceThresholdTest`: Tests the threshold comparison logic.
2.  `NotificationLogTest`: Tests that the NotificationLog is created correctly.
3.  `AlertScopingTest`: Tests that users can only see their own alerts.

Run tests using: `python manage.py test`

## Documentation

Comprehensive documentation now lives in the `docs/` folder:

- `docs/README.md` (entrypoint)
- `docs/architecture.md`
- `docs/api-swagger-testing.md`
- `docs/pipelines.md`
- `docs/infra-deployment.md`
- `docs/testing-strategy.md`
- `docs/operations-runbook.md`

## Swagger and OpenAPI

- Swagger UI: `/api/docs/`
- OpenAPI schema: `/api/schema/`

## GitHub Pipelines

Workflows are under `.github/workflows/`:

- `validate.yml`: validation gate for app and Terraform
- `test.yml`: dedicated Python test pipeline (matrix)
- `build-deploy.yml`: build container and deploy to Azure Web App
- `infra-terraform.yml`: Terraform plan/apply workflow

## Terraform Infrastructure

Terraform modules and environment definitions are in `infra/terraform/`.

- Reusable modules: `infra/terraform/modules/*`
- Dev environment composition: `infra/terraform/environments/dev/`
