from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('reports', views.ReportListView.as_view(), name='reports'),

    path("reports/<int:pk>/", views.ReportDetailView.as_view(), name="report-detail"),
    path("reports/<int:pk>/missing.csv", views.download_missing_csv, name="report-missing-csv"),
    path("reports/<int:pk>/<str:source>.csv", views.download_source_csv, name="report-source-csv"),
]