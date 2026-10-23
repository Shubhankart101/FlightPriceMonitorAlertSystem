import logging
from decimal import Decimal, InvalidOperation

import requests
from celery import shared_task
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from requests import RequestException

from .models import NotificationLog, PriceAlert

logger = logging.getLogger(__name__)


def parse_price(value):
    """Return a finite, non-negative Decimal, or None if the value is unusable."""
    # bool is a subclass of int, so reject it explicitly.
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        price = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    if not price.is_finite() or price < 0:
        return None
    return price


@shared_task
def check_prices():
    price_api_url = getattr(settings, "FLIGHT_PRICE_API_URL", None)
    if not price_api_url:
        raise ImproperlyConfigured("FLIGHT_PRICE_API_URL is not configured.")

    active_alerts = PriceAlert.objects.filter(status=PriceAlert.Status.ACTIVE)
    routes = active_alerts.values_list("origin", "destination").distinct()

    for origin, destination in routes:
        route = f"{origin}-{destination}"
        try:
            response = requests.get(
                price_api_url,
                params={"route": route},
                timeout=settings.FLIGHT_PRICE_API_TIMEOUT,
            )
        except RequestException as exc:
            logger.warning("Price lookup failed for %s: %s", route, exc)
            continue

        if response.status_code != 200:
            logger.warning("Price lookup for %s returned HTTP %s", route, response.status_code)
            continue

        try:
            payload = response.json()
        except ValueError:
            logger.warning("Price lookup for %s returned invalid JSON", route)
            continue

        if not isinstance(payload, dict):
            logger.warning("Price lookup for %s returned unexpected payload type", route)
            continue

        current_price = parse_price(payload.get("price"))
        if current_price is None:
            logger.warning("Price lookup for %s returned missing or invalid price: %r", route, payload.get("price"))
            continue

        route_alerts = active_alerts.filter(
            origin=origin,
            destination=destination,
            threshold_price__gte=current_price,
        )
        for alert_id in route_alerts.values_list("id", flat=True):
            # Pass as str: Decimal is not JSON-serializable for the Celery payload.
            send_notification.delay(alert_id, str(current_price))


@shared_task
def send_notification(alert_id, triggered_price):
    price = parse_price(triggered_price)
    if price is None:
        logger.error("Invalid triggered price %r for alert %s", triggered_price, alert_id)
        return

    with transaction.atomic():
        alert = (
            PriceAlert.objects.select_for_update()
            .filter(id=alert_id)
            .first()
        )
        if alert is None:
            logger.info("Alert %s no longer exists; skipping notification", alert_id)
            return

        # Recheck under the row lock so concurrent workers can't both notify.
        if alert.status != PriceAlert.Status.ACTIVE:
            return

        if price > alert.threshold_price:
            return

        message = (
            f"Price alert triggered! {alert.origin}-{alert.destination} "
            f"is now ₹{price} - below your threshold of "
            f"₹{alert.threshold_price}"
        )

        NotificationLog.objects.create(
            alert=alert,
            triggered_price=price,
            message=message,
        )

        alert.status = PriceAlert.Status.TRIGGERED
        alert.save(update_fields=["status"])
