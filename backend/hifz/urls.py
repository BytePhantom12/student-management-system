from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import HifzViewSet,SurahView
router=DefaultRouter(); router.register("",HifzViewSet,basename="hifz"); urlpatterns=[path("surahs/",SurahView.as_view())]+router.urls

