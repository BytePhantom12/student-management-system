from rest_framework.routers import DefaultRouter
from .views import AttendanceSessionViewSet,AttendanceViewSet
router=DefaultRouter(); router.register("sessions",AttendanceSessionViewSet,basename="attendance-session"); router.register("",AttendanceViewSet,basename="attendance"); urlpatterns=router.urls
