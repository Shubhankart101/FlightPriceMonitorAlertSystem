import random

from django.contrib.auth import authenticate
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import NotificationLog, PriceAlert
from .permissions import IsAdminUser
from .serializers import (
    AlertCreateSerializer,
    AlertSerializer,
    LoginSerializer,
    RegisterSerializer,
)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
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
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({"access": str(refresh.access_token)}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class AlertListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        alerts = PriceAlert.objects.filter(user=request.user)
        data = AlertSerializer(alerts, many=True)
        return Response(data.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AlertCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert = PriceAlert.objects.create(user=request.user, **serializer.validated_data)
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
    permission_classes = [IsAdminUser]

    def get(self, request):
        counts = PriceAlert.objects.aggregate(
            total_alerts=Count("id"),
            active_alerts=Count("id", filter=Q(status=PriceAlert.Status.ACTIVE)),
            triggered_alerts=Count("id", filter=Q(status=PriceAlert.Status.TRIGGERED)),
        )
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
                "total_alerts": counts["total_alerts"],
                "active_alerts": counts["active_alerts"],
                "triggered_alerts": counts["triggered_alerts"],
                "total_notifications": total_notifications,
                "top_routes": formatted_routes,
            },
            status=status.HTTP_200_OK,
        )
