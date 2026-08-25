from rest_framework.routers import DefaultRouter

from .views import SuperuserUserViewSet


router = DefaultRouter()
router.register("", SuperuserUserViewSet, basename="superuser-user")
urlpatterns = router.urls
