from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.accounts.views import UserViewSet
from apps.research import views as v

router = DefaultRouter()
for route, view in [
    ("users", UserViewSet),
    ("datasets", v.DatasetViewSet),
    ("images", v.ImageViewSet),
    ("versions", v.VersionViewSet),
    ("variants", v.VariantViewSet),
    ("jobs", v.JobViewSet),
    ("training-runs", v.TrainingViewSet),
    ("models", v.ModelViewSet),
    ("inspections", v.InspectionViewSet),
    ("evaluations", v.EvaluationViewSet),
    ("dashboard", v.DashboardViewSet),
    ("reports", v.ReportViewSet),
    ("audit", v.AuditViewSet),
]:
    router.register(route, view, basename=route)
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/token/", TokenObtainPairView.as_view()),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view()),
    path("api/v1/auth/logout/", TokenBlacklistView.as_view()),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/v1/", include(router.urls)),
]
