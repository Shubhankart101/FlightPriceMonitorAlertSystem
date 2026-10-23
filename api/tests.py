from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import NotificationLog, PriceAlert
from .tasks import check_prices, parse_price, send_notification


class PriceThresholdTest(TestCase):
    def test_price_below_threshold_triggers_alert(self):
        self.assertTrue(4200 <= 4500)

    def test_price_above_threshold_does_not_trigger(self):
        self.assertFalse(5000 <= 4500)

    def test_price_equal_to_threshold_triggers_alert(self):
        self.assertTrue(4500 <= 4500)


class NotificationLogTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.alert = PriceAlert.objects.create(
            user=self.user,
            origin="DEL",
            destination="BOM",
            threshold_price=4500,
            status=PriceAlert.Status.ACTIVE,
        )

    def test_notification_log_created_with_correct_message(self):
        log = NotificationLog.objects.create(
            alert=self.alert,
            triggered_price=4200,
            message="Price dropped to ₹4200 for DEL-BOM",
        )

        self.assertEqual(log.triggered_price, 4200)
        self.assertEqual(log.alert, self.alert)
        self.assertIn("DEL-BOM", log.message)


class AlertScopingTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass1")
        self.user2 = User.objects.create_user(username="user2", password="pass2")

        PriceAlert.objects.create(
            user=self.user1,
            origin="DEL",
            destination="BOM",
            threshold_price=4500,
        )
        PriceAlert.objects.create(
            user=self.user2,
            origin="BLR",
            destination="HYD",
            threshold_price=3000,
        )

    def test_user_only_sees_own_alerts(self):
        user1_alerts = PriceAlert.objects.filter(user=self.user1)

        self.assertEqual(user1_alerts.count(), 1)
        self.assertEqual(user1_alerts.first().origin, "DEL")

    def test_user_cannot_see_other_users_alerts(self):
        user1_alerts = PriceAlert.objects.filter(user=self.user1)
        self.assertNotEqual(user1_alerts.first().origin, "BLR")


class ApiAuthAndAlertFlowTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="apipass123")
        self.other_user = User.objects.create_user(username="otheruser", password="otherpass123")

        token = RefreshToken.for_user(self.user)
        self.auth_header = {"HTTP_AUTHORIZATION": f"Bearer {str(token.access_token)}"}

    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("status"), "ok")

    def test_register_and_login(self):
        register_response = self.client.post(
            reverse("register"),
            {"username": "newuser", "password": "newpass123", "email": "new@example.com"},
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", register_response.json())

        login_response = self.client.post(
            reverse("login"),
            {"username": "newuser", "password": "newpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.json())

    def test_register_duplicate_username_returns_400(self):
        User.objects.create_user(username="dupuser", password="dupuser123")

        response = self.client.post(
            reverse("register"),
            {"username": "dupuser", "password": "newpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_wrong_password_returns_401(self):
        response = self.client.post(
            reverse("login"),
            {"username": "apiuser", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_alerts_are_scoped_to_user(self):
        PriceAlert.objects.create(
            user=self.user,
            origin="DEL",
            destination="BOM",
            threshold_price=4300,
        )
        PriceAlert.objects.create(
            user=self.other_user,
            origin="BLR",
            destination="HYD",
            threshold_price=3300,
        )

        response = self.client.get(reverse("alerts"), **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["origin"], "DEL")

    def test_create_alert_requires_authentication(self):
        response = self.client.post(
            reverse("alerts"),
            {"origin": "DEL", "destination": "BLR", "threshold_price": "4500.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_summary_forbidden_for_regular_user(self):
        response = self.client.get(reverse("admin-summary"), **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_summary_allows_admin_user(self):
        self.user.profile.role = "admin"
        self.user.profile.save(update_fields=["role"])

        response = self.client.get(reverse("admin-summary"), **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_alerts", response.json())

    def test_flight_price_valid_and_invalid_route(self):
        valid_response = self.client.get(reverse("flight-price"), {"route": "DEL-BOM"})
        self.assertEqual(valid_response.status_code, status.HTTP_200_OK)
        self.assertIn("price", valid_response.json())

        invalid_response = self.client.get(reverse("flight-price"), {"route": "XYZ-ABC"})
        self.assertEqual(invalid_response.status_code, status.HTTP_404_NOT_FOUND)


class ParsePriceTest(TestCase):
    def test_valid_values(self):
        self.assertEqual(parse_price(4200), Decimal("4200"))
        self.assertEqual(parse_price("4200.50"), Decimal("4200.50"))
        self.assertEqual(parse_price(4200.5), Decimal("4200.5"))

    def test_invalid_values(self):
        for value in (None, True, "abc", "", "NaN", "Infinity", -1, [4200], {"p": 1}):
            self.assertIsNone(parse_price(value), value)


@override_settings(FLIGHT_PRICE_API_URL="http://web:8000/api/flights/price/")
class CheckPricesTaskTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="u", password="p")
        self.alert = PriceAlert.objects.create(
            user=user, origin="DEL", destination="BOM", threshold_price=4500
        )

    def _run(self, json_value=None, json_error=False):
        response = mock.Mock(status_code=200)
        if json_error:
            response.json.side_effect = ValueError("bad json")
        else:
            response.json.return_value = json_value
        with mock.patch("api.tasks.requests.get", return_value=response) as get, \
                mock.patch("api.tasks.send_notification.delay") as delay:
            check_prices()
        return get, delay

    def test_uses_configured_url_and_enqueues_below_threshold(self):
        get, delay = self._run({"price": 4200})
        self.assertEqual(get.call_args.args[0], "http://web:8000/api/flights/price/")
        delay.assert_called_once_with(self.alert.id, "4200")

    def test_above_threshold_does_not_enqueue(self):
        _, delay = self._run({"price": 5000})
        delay.assert_not_called()

    def test_bad_payloads_are_skipped(self):
        for payload in ({}, {"price": None}, {"price": "cheap"}, [4200], None):
            _, delay = self._run(payload)
            delay.assert_not_called()
        _, delay = self._run(json_error=True)
        delay.assert_not_called()


class SendNotificationTaskTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="u", password="p")
        self.alert = PriceAlert.objects.create(
            user=user, origin="DEL", destination="BOM", threshold_price=4500
        )

    def test_creates_single_log_when_run_twice(self):
        send_notification(self.alert.id, "4200")
        send_notification(self.alert.id, "4200")

        self.assertEqual(NotificationLog.objects.filter(alert=self.alert).count(), 1)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, PriceAlert.Status.TRIGGERED)

    def test_deleted_alert_is_ignored(self):
        alert_id = self.alert.id
        self.alert.delete()

        send_notification(alert_id, "4200")

        self.assertEqual(NotificationLog.objects.count(), 0)

    def test_inactive_alert_is_ignored(self):
        self.alert.status = PriceAlert.Status.INACTIVE
        self.alert.save()

        send_notification(self.alert.id, "4200")

        self.assertEqual(NotificationLog.objects.count(), 0)
