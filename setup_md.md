# PulseNotify: Flight Price Monitor Alert System 
## Complete Project Setup & Specifications

This document outlines the exact specifications, data models, endpoints, background jobs, and step-by-step tasks required to build the PulseNotify backend, exactly as described in the project brief.

---

## 1. Brief

### 1. Scenario
You know that feeling when you check a flight price today, it's ₹6,200, you close the tab, and when you come back tomorrow it's ₹9,800? That is the problem PulseNotify solves.

PulseNotify is a flight price monitoring service. Users set price alerts for routes they care about - Delhi to Mumbai, Bangalore to Hyderabad, whatever. They tell the system: *If the price drops below ₹X, notify me.* PulseNotify then runs in the background, continuously checking prices, and fires a notification the moment a target is hit.

This is exactly how Google Flights alerts, Skyscanner price notifications, and Hopper's price prediction work. You are building that backend.

### 2. Context
There are three things PulseNotify needs to do well, and each one connects directly to what you have been learning:
*   **It must not make users wait.** When a user submits a price alert, the system should respond instantly - not after it has finished checking prices, not after it has sent a notification. The heavy work happens in the background. This is the Celery async pattern you studied.
*   **It must check prices automatically without anyone pressing a button.** Every 60 seconds, the system wakes up, checks the current price for every active alert, and decides whether to fire a notification. Nobody triggers this - it runs on a schedule. This is Celery Beat.
*   **It must call its own internal price feed to get current prices.** The price feed is a simple Django view inside the same project that returns a price for a given route. Your Celery task will call this endpoint using the `requests` library - exactly the backend-to-backend call pattern you studied.

*Why call your own endpoint instead of a third-party flight API?*
Real flight APIs require registration, API keys, credit cards, and often have strict rate limits. The `requests.get()` pattern is identical whether you're calling your own endpoint or an external one. For this assignment, you call your own - no blockers, full control, same learning outcome.

### 3. How It Works
Here is the complete flow of PulseNotify, end to end:

```text
User sets alert: route=DEL-BOM, threshold=₹4500
                   ↓
POST /api/alerts/  →  PriceAlert saved to DB
                   ↓
Celery Beat fires every 60 seconds
                   ↓
check_prices task wakes up
                   ↓
GET /api/flights/price/?route=DEL-BOM  (your own mock endpoint)
                   ↓
Mock endpoint returns { "route": "DEL-BOM", "price": 4200 }
                   ↓
4200 <= 4500 threshold? YES
                   ↓
send_notification.delay()  (async Celery task fires)
                   ↓
NotificationLog written to DB
                   ↓
GET /api/admin/summary/  →  Admin sees stats
```

There are two Celery tasks in this system:
*   `check_prices` - runs on a schedule (Celery Beat). Fetches current price, compares against all active alerts for that route, fires `send_notification` if threshold is met.
*   `send_notification` - runs asynchronously. Called with `.delay()` so it never blocks the Beat scheduler. Writes a NotificationLog entry to the database.

---

## 4. Data Models
These models are provided for you. Implement them exactly as specified.

### 4.1 User (extends Django's built-in User)
```python
# Use Django's built-in User model + a separate Profile
# OR extend AbstractUser - your choice, but set AUTH_USER_MODEL before migrations

class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'User'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    created_at = models.DateTimeField(auto_now_add=True)
```
*Requirement:* Wire a `post_save` signal on User to auto-create a UserProfile.

### 4.2 PriceAlert
```python
class PriceAlert(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        TRIGGERED = 'triggered', 'Triggered'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    origin = models.CharField(max_length=10) # e.g. 'DEL'
    destination = models.CharField(max_length=10) # e.g. 'BOM'
    threshold_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.origin}-{self.destination} @ ₹{self.threshold_price}'
```

### 4.3 NotificationLog
```python
class NotificationLog(models.Model):
    alert = models.ForeignKey(PriceAlert, on_delete=models.CASCADE, related_name='notifications')
    triggered_price = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField() # e.g. 'Price dropped to ₹4200 for DEL-BOM'
    notified_at = models.DateTimeField(auto_now_add=True)
```

---

## 5. What to Build
You must implement 7 endpoints. The first two are public. The rest are protected by JWT.

### 5.1 POST `/api/auth/register/`
*   **Auth:** Public
*   **Who calls it:** A new user signing up for PulseNotify
*   **Action:** Creates a Django User and auto-creates a UserProfile via `post_save` signal. Returns a JWT access token and the user's profile details.
*   **Request body:** `{ "username": "alice", "password": "securepass", "email": "alice@example.com" }`
*   **Success response (201):** `{ "username": "alice", "access": "eyJ...", "role": "user" }`
*   **Requirements:**
    *   `authentication_classes = []` and `permission_classes = []` - no token required.
    *   role must always default to USER - never accept role from the request body.
    *   Return 400 if username already exists.

### 5.2 POST `/api/auth/login/`
*   **Auth:** Public
*   **Who calls it:** Returning user logging back in
*   **Action:** Validates credentials, returns a fresh JWT access token.
*   **Requirements:**
    *   Use Django's `authenticate()` to validate credentials.
    *   Return 200 + JWT token on success.
    *   Return 401 if credentials are invalid.

### 5.4 GET `/api/alerts/`
*   **Auth:** JWT required
*   **Who calls it:** Authenticated user listing their own alerts
*   **Action:** Returns all PriceAlerts belonging to the logged-in user only. A user must never see another user's alerts.
*   **Requirements:**
    *   Filter using `get_queryset()` scoped to `request.user`.
    *   Return an empty list if the user has no alerts - not a 404.

### 5.5 DELETE `/api/alerts/<id>/`
*   **Auth:** JWT required
*   **Who calls it:** User deactivating one of their own alerts
*   **Action:** Sets the alert status to INACTIVE. Does not delete the database row.
*   **Requirements:**
    *   Fetch the alert using `get_object_or_404(PriceAlert, id=id)` - then check if `alert.user == request.user`.
    *   Return 404 if the alert does not exist or belongs to another user.
    *   Return 200 with `{ "status": "Inactive" }` on success.

### 5.6 GET `/api/flights/price/`
*   **Auth:** Public - no token required
*   **Who calls it:** Your own Celery task, internally
*   **Action:** This is your internal mock price feed. It accepts a route via query parameter and returns a simulated price.
*   **Code Example:**
```python
MOCK_PRICES = {
    "DEL-BOM": (3000, 7000),
    "BLR-HYD": (1500, 4000),
    "DEL-BLR": (4000, 9000),
    "BOM-GOA": (2000, 5000),
}

def get_flight_price(request):
    route = request.GET.get('route', '')
    price_range = MOCK_PRICES.get(route)
    
    if not price_range:
        return JsonResponse({'error': 'Route not found'}, status=404)
        
    price = random.randint(*price_range)
    return JsonResponse({'route': route, 'price': price})
```
*   **Requirements:**
    *   Return 200 with `{ "route": "DEL-BOM", "price": 4200 }` (random int in range).
    *   Return 404 if the route is not in `MOCK_PRICES`.
    *   No authentication.

### 5.7 GET `/api/admin/summary/`
*   **Auth:** JWT required - Admin only
*   **Who calls it:** Platform admin viewing system-wide alert statistics
*   **Action:** Returns platform-wide statistics. Only accessible to users with `role == ADMIN`. Regular users must receive 403.
*   **Success Response (200):**
```json
{
  "total_alerts": 34,
  "active_alerts": 18,
  "triggered_alerts": 4,
  "total_notifications": 11,
  "top_routes": [
    { "route": "DEL-BOM", "alert_count": 8 },
    { "route": "BLR-HYD", "alert_count": 6 }
  ]
}
```
*   **Requirements:**
    *   Enforce admin-only access via a custom `IsAdminUser` class in `permissions.py`.
    *   Use `.aggregate()` for counts.
    *   Use `.values('origin', 'destination').annotate(Count)` for top_routes - no Python loops for counting.
    *   Regular USER tokens must receive 403.

---

## 6. Background Jobs
This is the core of PulseNotify. Two Celery tasks. One runs on a schedule. One runs asynchronously when triggered.

### 6.1 `check_prices` & `send_notification` (tasks.py)
```python
from celery import shared_task
import requests
from .models import PriceAlert, UserProfile, NotificationLog

@shared_task
def check_prices():
    active_alerts = PriceAlert.objects.filter(status=PriceAlert.Status.ACTIVE)
    routes = active_alerts.values_list('origin', 'destination').distinct()

    for origin, destination in routes:
        route = f'{origin}-{destination}'
        response = requests.get('http://localhost:8000/api/flights/price/', params={'route': route})
        
        if response.status_code != 200:
            continue
            
        current_price = response.json().get('price')
        route_alerts = active_alerts.filter(origin=origin, destination=destination)

        for alert in route_alerts:
            if current_price <= float(alert.threshold_price):
                send_notification.delay(alert.id, current_price)

@shared_task
def send_notification(alert_id, triggered_price):
    alert = PriceAlert.objects.get(id=alert_id)
    message = f"Price alert triggered! {alert.origin}-{alert.destination} is now ₹{triggered_price} - below your threshold of ₹{alert.threshold_price}"
    
    NotificationLog.objects.create(alert=alert, triggered_price=triggered_price, message=message)
    alert.status = PriceAlert.Status.TRIGGERED
    alert.save()
```
*Important: `send_notification` is called with `.delay()` - not directly.*

### 6.2 Celery Beat Schedule (`settings/base.py`)
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-flight-prices-every-minute': {
        'task': 'your_app.tasks.check_prices',
        'schedule': 60.0, # every 60 seconds
    },
}
```

### 6.3 Redis and Celery Setup
**`docker-compose.yml`**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**`settings/base.py`**
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
```

**Running the System (3 Terminals required):**
1. `python manage.py runserver`
2. `celery -A your_project worker --loglevel=info`
3. `celery -A your_project beat --loglevel=info`

---

## 7. Environment Configuration
Split your settings into `base.py`, `local.py`, and `production.py`.
```text
your_project/
  settings/
    __init__.py
    base.py        # shared config
    local.py       # local dev overrides (DEBUG=True, local DB)
    production.py  # production overrides (DEBUG=False, prod DB)
.env               # SECRET_KEY, DB credentials, never committed
```
*Requirement:* Set `DJANGO_SETTINGS_MODULE` in your `.env` file: `DJANGO_SETTINGS_MODULE=your_project.settings.local`

---

## 8. Unit Tests
Write at least 3 unit tests in `tests.py` using Django's TestCase class.

**Test 1: PriceThresholdTest**
*   `test_price_below_threshold_triggers_alert`: `assertTrue(4200 <= 4500)`
*   `test_price_above_threshold_does_not_trigger`: `assertFalse(5000 <= 4500)`
*   `test_price_equal_to_threshold_triggers_alert`: `assertTrue(4500 <= 4500)`

**Test 2: NotificationLogTest**
*   Create a user, an alert, and a notification log manually.
*   Assert `log.triggered_price == 4200`.
*   Assert `log.alert == self.alert`.
*   Assert `'DEL-BOM' in log.message`.

**Test 3: AlertScopingTest**
*   Create two users, one alert each.
*   Filter alerts for user 1.
*   Assert count is 1, and origin is user 1's origin.
*   Assert `assertNotEqual` to make sure user 1 does not see user 2's alert.

Run via: `python manage.py test`

---

## 9. Step-by-Step Tasks

### Step 1 - Project Setup
1. Create a new Django project and app.
2. Set up PostgreSQL + Redis using Docker Compose.
3. Install: `djangorestframework`, `djangorestframework-simplejwt`, `celery`, `redis`, `requests`.
4. Create `requirements.txt` with dependencies pinned.

### Step 2 - Settings Split
1. Create `settings/` folder with init, base, local, production.
2. Move shared configs to base.
3. Add DEBUG=True and local DB creds to local.
4. Set `DJANGO_SETTINGS_MODULE` in `.env` and add `.env` to `.gitignore`.

### Step 3 - Models and Migrations
1. Create `UserProfile`, `PriceAlert`, `NotificationLog`.
2. Wire `post_save` signal on User in `signals.py`.
3. Connect signal in `AppConfig.ready()`.
4. Run migrations.

### Step 4 - Auth Endpoints
1. Implement `POST /api/auth/register/` and `POST /api/auth/login/`.
2. Configure SimpleJWT globally.
3. Set authentication and permission classes to `[]` on public endpoints.
4. Test in Postman.

### Step 5 - Alert Endpoints
1. Implement `POST /api/alerts/` (extract user from request).
2. Implement `GET /api/alerts/` (scope queryset).
3. Implement `DELETE /api/alerts/<id>/` (fetch alert, check user).

### Step 6 - Mock Price Feed
1. Implement `GET /api/flights/price/`.
2. Test manually in Postman.

### Step 7 - Celery Tasks
1. Create `tasks.py` with `check_prices` and `send_notification`.
2. Wire Celery app in `__init__.py`.
3. Add `CELERY_BEAT_SCHEDULE` to base.py.
4. Start all three processes (runserver, worker, beat) to test.

### Step 8 - Admin Summary and Tests
1. Create `permissions.py` with `IsAdminUser`.
2. Implement `GET /api/admin/summary/`.
3. Set a user's role to admin in PGAdmin, test endpoint.
4. Write all 3 required unit tests.
5. Run `python manage.py test`.

---

## 10. Technical Requirements Checklist

| Requirement | Where to Apply |
| :--- | :--- |
| `@shared_task` on both celery tasks | `tasks.py` |
| `delay()` to call send_notification async | `check_prices` task |
| Redis in Docker Compose, broker URL in settings | `docker-compose.yml` + `base.py` |
| `CELERY_BEAT_SCHEDULE` with 60 second interval | `base.py` |
| `requests.get()` with params + response.json() | `check_prices` task |
| `post_save` signal auto-creating UserProfile | `signals.py` + `AppConfig.ready()` |
| `request.user` - never user_id in body | `POST /api/alerts/` |
| `get_queryset()` scoped to request.user | `GET /api/alerts/` |
| Manual ownership check on alert delete (`alert.user == request.user`) | `DELETE /api/alerts/<id>/` |
| Custom BasePermission checking profile.role | `permissions.py` |
| `aggregate()` + `values().annotate()` on admin summary | `GET /api/admin/summary/` |
| Settings split into base/local/production | `settings/` folder |
| All secrets in `.env`, never hardcoded | `settings/local.py` |
| 3 unit tests passing via manage.py test | `tests.py` |

---

## 11. Postman Collection Scenarios
Submit a Postman collection (`.json`) covering all 13 scenarios passing:

| # | Scenario | Endpoint | Expected |
| :--- | :--- | :--- | :--- |
| 1 | Register a new user | POST `/api/auth/register/` | 201 + JWT token |
| 2 | Register with duplicate username | POST `/api/auth/register/` | 400 |
| 3 | Login with valid credentials | POST `/api/auth/login/` | 200 + JWT token |
| 4 | Login with wrong password | POST `/api/auth/login/` | 401 |
| 5 | Create a price alert - no token | POST `/api/alerts/` | 401 |
| 6 | Create a price alert - valid token | POST `/api/alerts/` | 201 |
| 7 | List own alerts | GET `/api/alerts/` | 200 + list |
| 8 | Deactivate an alert | DELETE `/api/alerts/<id>/` | 200 + Inactive status |
| 9 | Mock price feed - valid route | GET `/api/flights/price/?route=DEL-BOM` | 200 + price |
| 10 | Mock price feed - invalid route | GET `/api/flights/price/?route=XYZ-ABC` | 404 |
| 11 | Admin summary - regular user token | GET `/api/admin/summary/` | 403 |
| 12 | Admin summary - admin token | GET `/api/admin/summary/` | 200 + stats |
| 13 | Verify NotificationLog - check PGAdmin after Celery fires | * PGAdmin check * | New entry in notification_log |

---

## Deliverables
*   GitHub Repo (Working Django + DRF backend with all 7 endpoints).
*   PostgreSQL + Redis via Docker Compose.
*   `settings/` folder properly split.
*   `tasks.py` with both tasks using `@shared_task`.
*   `signals.py` connected.
*   `permissions.py` with custom class.
*   `tests.py` with all 3 tests passing.
*   `requirements.txt`.
*   Postman collection covering all 13 scenarios.
*   README.md (how to run server, worker, beat).