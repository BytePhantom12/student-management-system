from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls), path("api/auth/", include("accounts.urls")),
    path("api/users/", include("accounts.user_urls")),
    path("api/students/", include("students.urls")), path("api/teachers/", include("teachers.urls")),
    path("api/guardians/", include("students.guardian_urls")),
    path("api/hifz/", include("hifz.urls")), path("api/attendance/", include("attendance.urls")),
    path("api/audit/", include("audit.urls")), path("api/dashboard/", include("dashboard.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
