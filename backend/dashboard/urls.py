from django.urls import path
from .views import AdminDashboardView, DashboardView
urlpatterns=[path("admin/",AdminDashboardView.as_view()),path("teacher/",DashboardView.as_view())]
