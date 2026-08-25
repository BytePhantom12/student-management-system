from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import HifzProgress
from .quran import SURAH_CHOICES
from .serializers import HifzSerializer
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
class HifzViewSet(ModelViewSet):
    queryset=HifzProgress.objects.all()
    serializer_class=HifzSerializer; filterset_fields=("student","status","juz","revision_status"); ordering_fields=("updated_at","progress_percentage","surah")
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False): return self.queryset
        qs=HifzProgress.objects.select_related("student","student__assigned_teacher__user")
        user = self.request.user
        return qs if user.is_authenticated and user.is_admin else qs.filter(student__assigned_teacher__user=user)
    def perform_create(self,serializer):
        student=serializer.validated_data["student"]
        if not self.request.user.is_admin and (not student.assigned_teacher_id or student.assigned_teacher.user_id != self.request.user.id):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This student is not assigned to you.")
        serializer.save()
    def perform_update(self, serializer):
        student=serializer.validated_data.get("student", serializer.instance.student)
        if not self.request.user.is_admin and (not student.assigned_teacher_id or student.assigned_teacher.user_id != self.request.user.id):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This student is not assigned to you.")
        serializer.save()
class SurahView(APIView):
    @extend_schema(responses=inline_serializer("Surah", {"number": serializers.IntegerField(), "name": serializers.CharField()}, many=True))
    def get(self,request): return Response([{"number":n,"name":label.split(". ",1)[1]} for n,label in SURAH_CHOICES])
