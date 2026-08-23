from django.db.models import Count
from rest_framework.viewsets import ModelViewSet
from common import IsAdmin
from .models import Teacher
from .serializers import TeacherSerializer
class TeacherViewSet(ModelViewSet):
    permission_classes = [IsAdmin]; serializer_class = TeacherSerializer; filterset_fields = ("is_active",); search_fields = ("user__first_name", "user__last_name", "user__email", "phone")
    def get_queryset(self): return Teacher.objects.select_related("user").annotate(student_count=Count("students")).order_by("user__first_name")

