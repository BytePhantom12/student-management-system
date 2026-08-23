from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, NoteViewSet
router=DefaultRouter(); router.register("notes", NoteViewSet, basename="note"); router.register("", StudentViewSet, basename="student"); urlpatterns=router.urls
