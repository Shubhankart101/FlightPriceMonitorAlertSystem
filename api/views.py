import random

from django.contrib.auth import authenticate
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
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

ErrorSerializer = inline_serializer("Error", {"error": serializers.CharField()})
DetailSerializer = inline_serializer("Detail", {"detail": serializers.CharField()})


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["health"],
        auth=[],
        responses={200: inline_serializer("Health", {"status": serializers.CharField()})},
    )
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["auth"],
        auth=[],
        request=RegisterSerializer,
        responses={
            201: inline_serializer(
                "RegisterResponse",
                {
                    "username": serializers.CharField(),
                    "access": serializers.CharField(),
                    "role": serializers.CharField(),
                },
            ),
            400: OpenApiResponse(description="Validation error or duplicate username"),
        },
        examples=[
            OpenApiExample(
                "Register",
                value={"username": "demo_user", "password": "demopass123", "email": "demo@example.com"},
                request_only=True,
            )
        ],
    )
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

    @extend_schema(
        tags=["auth"],
        auth=[],
        request=LoginSerializer,
        responses={
            200: inline_serializer("LoginResponse", {"access": serializers.CharField()}),
            400: OpenApiResponse(description="Validation error"),
            401: ErrorSerializer,
        },
        examples=[
            OpenApiExample(
                "Login",
                value={"username": "demo_user", "password": "demopass123"},
                request_only=True,
            )
        ],
    )
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

    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user)

    @extend_schema(
        tags=["alerts"],
        responses={200: AlertSerializer(many=True), 401: DetailSerializer},
    )
    def get(self, request):
        alerts = self.get_queryset()
        data = AlertSerializer(alerts, many=True)
        return Response(data.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["alerts"],
        request=AlertCreateSerializer,
        responses={
            201: inline_serializer("AlertCreated", {"id": serializers.IntegerField()}),
            400: OpenApiResponse(description="Validation error"),
            401: DetailSerializer,
        },
        examples=[
            OpenApiExample(
                "DEL to BOM",
                value={"origin": "DEL", "destination": "BOM", "threshold_price": "4500.00"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = AlertCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alert = PriceAlert.objects.create(user=request.user, **serializer.validated_data)
        return Response({"id": alert.id}, status=status.HTTP_201_CREATED)


class AlertDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["alerts"],
        responses={
            200: inline_serializer("AlertDeactivated", {"status": serializers.CharField()}),
            401: DetailSerializer,
            404: OpenApiResponse(description="Alert not found or not owned by user"),
        },
    )
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


@extend_schema(
    tags=["flights"],
    auth=[],
    parameters=[
        OpenApiParameter(
            "route",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=True,
            enum=list(MOCK_PRICES),
            description="Route in ORIGIN-DESTINATION format",
        )
    ],
    responses={
        200: inline_serializer(
            "FlightPrice",
            {"route": serializers.CharField(), "price": serializers.IntegerField()},
        ),
        404: ErrorSerializer,
    },
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
def get_flight_price(request):
    route = request.query_params.get("route", "")
    price_range = MOCK_PRICES.get(route)

    if not price_range:
        return Response({"error": "Route not found"}, status=status.HTTP_404_NOT_FOUND)

    price = random.randint(*price_range)
    return Response({"route": route, "price": price})


class AdminSummaryView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["admin"],
        responses={
            200: inline_serializer(
                "AdminSummary",
                {
                    "total_alerts": serializers.IntegerField(),
                    "active_alerts": serializers.IntegerField(),
                    "triggered_alerts": serializers.IntegerField(),
                    "total_notifications": serializers.IntegerField(),
                    "top_routes": inline_serializer(
                        "TopRoute",
                        {"route": serializers.CharField(), "alert_count": serializers.IntegerField()},
                        many=True,
                    ),
                },
            ),
            401: DetailSerializer,
            403: DetailSerializer,
        },
    )
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
