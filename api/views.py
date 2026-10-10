import random

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import NotificationLog, PriceAlert
from .permissions import IsAdminUser


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password)
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "username": user.username,
                "access": str(refresh.access_token),
                "role": user.profile.role,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user = authenticate(
            username=request.data.get("username"),
            password=request.data.get("password"),
        )
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({"access": str(refresh.access_token)}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class AlertListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        alerts = PriceAlert.objects.filter(user=request.user)
        data = [
            {
                "id": alert.id,
                "origin": alert.origin,
                "destination": alert.destination,
                "threshold_price": alert.threshold_price,
                "status": alert.status,
            }
            for alert in alerts
        ]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        alert = PriceAlert.objects.create(
            user=request.user,
            origin=request.data.get("origin"),
            destination=request.data.get("destination"),
            threshold_price=request.data.get("threshold_price"),
        )
        return Response({"id": alert.id}, status=status.HTTP_201_CREATED)


class AlertDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        alert = get_object_or_404(PriceAlert, id=pk)
        if alert.user != request.user:
            return Response(status=status.HTTP_404_NOT_FOUND)

        alert.status = PriceAlert.Status.INACTIVE
        alert.save()
        return Response({"status": "Inactive"}, status=status.HTTP_200_OK)


MOCK_PRICES = {
    "DEL-BOM": (3000, 7000),
    "BLR-HYD": (1500, 4000),
    "DEL-BLR": (4000, 9000),
    "BOM-GOA": (2000, 5000),
}


def get_flight_price(request):
    route = request.GET.get("route", "")
    price_range = MOCK_PRICES.get(route)

    if not price_range:
        return JsonResponse({"error": "Route not found"}, status=404)

    price = random.randint(*price_range)
    return JsonResponse({"route": route, "price": price})


class AdminSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        active_alerts = PriceAlert.objects.filter(status=PriceAlert.Status.ACTIVE).count()
        triggered_alerts = PriceAlert.objects.filter(status=PriceAlert.Status.TRIGGERED).count()
        total_alerts = PriceAlert.objects.count()
        total_notifications = NotificationLog.objects.count()

        top_routes = list(
            PriceAlert.objects.values("origin", "destination")
            .annotate(alert_count=Count("id"))
            .order_by("-alert_count")[:5]
        )

        formatted_routes = [
            {"route": f"{route['origin']}-{route['destination']}", "alert_count": route["alert_count"]}
            for route in top_routes
        ]

        return Response(
            {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "triggered_alerts": triggered_alerts,
                "total_notifications": total_notifications,
                "top_routes": formatted_routes,
            },
            status=status.HTTP_200_OK,
        )
