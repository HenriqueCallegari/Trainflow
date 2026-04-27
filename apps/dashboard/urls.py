"""URLs do painel."""
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="home"),
    path("calculadoras/", views.CalculatorsView.as_view(), name="calculators"),
    path("tonelagem/", views.TonnageDashboardView.as_view(), name="tonnage"),
    path("pr-log/", views.PRLogView.as_view(), name="pr_log"),
    path("rpe/", views.RPEChartView.as_view(), name="rpe_chart"),
]
