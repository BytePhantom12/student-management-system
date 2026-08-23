from django.urls import path
from .views import DashboardView
urlpatterns=[path("admin/",DashboardView.as_view()),path("teacher/",DashboardView.as_view())]

