from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import HifzProgress
from .quran import SURAH_CHOICES
from .serializers import HifzSerializer
class HifzViewSet(ModelViewSet):
    serializer_class=HifzSerializer; filterset_fields=("student","status","juz","revision_status"); ordering_fields=("updated_at","progress_percentage","surah")
    def get_queryset(self):
        qs=HifzProgress.objects.select_related("student","student__assigned_teacher__user")
        return qs if self.request.user.is_admin else qs.filter(student__assigned_teacher__user=self.request.user)
    def perform_create(self,serializer):
        student=serializer.validated_data["student"]
        if not self.request.user.is_admin and student.assigned_teacher.user_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This student is not assigned to you.")
        serializer.save()
class SurahView(APIView):
    def get(self,request): return Response([{"number":n,"name":label.split(". ",1)[1]} for n,label in SURAH_CHOICES])

