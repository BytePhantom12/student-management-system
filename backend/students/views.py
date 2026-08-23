from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Student, StudentNote
from .serializers import StudentSerializer, NoteSerializer
class AssignedQuerysetMixin:
    def restrict(self, qs):
        return qs if self.request.user.is_admin else qs.filter(assigned_teacher__user=self.request.user)
class StudentViewSet(AssignedQuerysetMixin, ModelViewSet):
    serializer_class=StudentSerializer; filterset_fields=("status","assigned_teacher","gender"); ordering_fields=("student_id","first_name","last_name","enrollment_date","created_at")
    def get_queryset(self):
        qs=Student.objects.select_related("assigned_teacher__user")
        term=self.request.query_params.get("search")
        if term: qs=qs.filter(Q(student_id__icontains=term)|Q(first_name__icontains=term)|Q(last_name__icontains=term)|Q(phone__icontains=term)|Q(email__icontains=term)|Q(guardian_name__icontains=term))
        return self.restrict(qs).order_by("last_name","first_name")
    def perform_create(self, serializer):
        if not self.request.user.is_admin: serializer.save(assigned_teacher=self.request.user.teacher_profile)
        else: serializer.save()
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        student=self.get_object(); student.status=Student.Status.INACTIVE; student.save(update_fields=["status","updated_at"]); return Response(self.get_serializer(student).data)
class NoteViewSet(ModelViewSet):
    serializer_class=NoteSerializer; filterset_fields=("student",)
    def get_queryset(self):
        qs=StudentNote.objects.select_related("student","author")
        return qs if self.request.user.is_admin else qs.filter(student__assigned_teacher__user=self.request.user)
    def perform_create(self, serializer):
        student=serializer.validated_data["student"]
        if not self.request.user.is_admin and student.assigned_teacher_id != self.request.user.teacher_profile.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This student is not assigned to you.")
        serializer.save(author=self.request.user)

