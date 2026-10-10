from django.urls import path

from .views import (
    AdminSummaryView,
    AlertDetailView,
    AlertListView,
    LoginView,
    RegisterView,
    get_flight_price,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("alerts/", AlertListView.as_view()),
    path("alerts/<int:pk>/", AlertDetailView.as_view()),
    path("flights/price/", get_flight_price),
    path("admin/summary/", AdminSummaryView.as_view()),
]
