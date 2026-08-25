from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import GuardianViewSet

router = DefaultRouter()
router.register("", GuardianViewSet, basename="guardian")
urlpatterns = router.urls
