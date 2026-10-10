from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import NotificationLog, PriceAlert


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
