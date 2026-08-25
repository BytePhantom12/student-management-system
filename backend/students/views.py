from django.db.models import Count, Q
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from common import IsAdmin
from .models import Guardian, Student, StudentNote
from .serializers import GuardianSerializer, StudentSerializer, NoteSerializer
class AssignedQuerysetMixin:
    def restrict(self, qs):
        user = self.request.user
        return qs if user.is_authenticated and user.is_admin else qs.filter(assigned_teacher__user=user)
class StudentViewSet(AssignedQuerysetMixin, ModelViewSet):
    queryset=Student.objects.all()
    serializer_class=StudentSerializer; filterset_fields=("status","assigned_teacher","primary_guardian","gender"); ordering_fields=("student_id","first_name","last_name","enrollment_date","created_at")
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False): return self.queryset
        qs=Student.objects.select_related("assigned_teacher__user", "primary_guardian")
        term=self.request.query_params.get("search")
        if term: qs=qs.filter(Q(student_id__icontains=term)|Q(first_name__icontains=term)|Q(last_name__icontains=term)|Q(phone__icontains=term)|Q(email__icontains=term)|Q(guardian_name__icontains=term))
        return self.restrict(qs).order_by("last_name","first_name")
    def perform_create(self, serializer):
        if not self.request.user.is_admin: serializer.save(assigned_teacher=self.request.user.teacher_profile)
        else: serializer.save()
    def perform_destroy(self, instance):
        if not self.request.user.is_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators may delete students.")
        instance.delete()
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        student=self.get_object(); student.status=Student.Status.INACTIVE; student.save(update_fields=["status","updated_at"]); return Response(self.get_serializer(student).data)
class GuardianViewSet(ModelViewSet):
    serializer_class = GuardianSerializer
    filterset_fields = ("is_active",)
    search_fields = ("name", "phone", "email")
    def get_permissions(self):
        return [IsAuthenticated()] if self.action in ("list", "retrieve") else [IsAdmin()]
    def get_queryset(self):
        qs = Guardian.objects.prefetch_related("students")
        user = self.request.user
        if user.is_admin:
            return qs.annotate(student_count=Count("students", distinct=True)).order_by("name")
        return qs.filter(students__assigned_teacher__user=user).annotate(
            student_count=Count("students", filter=Q(students__assigned_teacher__user=user), distinct=True)
        ).order_by("name")
class NoteViewSet(ModelViewSet):
    queryset=StudentNote.objects.all()
    serializer_class=NoteSerializer; filterset_fields=("student",)
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False): return self.queryset
        qs=StudentNote.objects.select_related("student","author")
        user = self.request.user
        return qs if user.is_authenticated and user.is_admin else qs.filter(student__assigned_teacher__user=user)
    def perform_create(self, serializer):
        student=serializer.validated_data["student"]
        if not self.request.user.is_admin and student.assigned_teacher_id != self.request.user.teacher_profile.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This student is not assigned to you.")
        serializer.save(author=self.request.user)
    def perform_update(self, serializer):
        student=serializer.validated_data.get("student", serializer.instance.student)
        if not self.request.user.is_admin and student.assigned_teacher_id != self.request.user.teacher_profile.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This student is not assigned to you.")
        if not self.request.user.is_admin and serializer.instance.author_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You may only edit notes you authored.")
        serializer.save()
    def perform_destroy(self, instance):
        if not self.request.user.is_admin and instance.author_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You may only delete notes you authored.")
        instance.delete()
