from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied,ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Attendance,AttendanceSession
from .serializers import AttendanceSerializer,AttendanceSessionSerializer,BulkAttendanceSerializer
def ensure_assigned(user,student):
    if not user.is_admin and (not student.assigned_teacher_id or student.assigned_teacher.user_id != user.id):
        raise PermissionDenied("This student is not assigned to you.")
class AttendanceViewSet(ModelViewSet):
    queryset=Attendance.objects.all()
    serializer_class=AttendanceSerializer; filterset_fields=("student","status","date","session","student__assigned_teacher"); ordering_fields=("date","status","created_at")
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False): return self.queryset
        qs=Attendance.objects.select_related("student","recorded_by","student__assigned_teacher","session")
        start=self.request.query_params.get("date_after"); end=self.request.query_params.get("date_before")
        if start: qs=qs.filter(date__gte=start)
        if end: qs=qs.filter(date__lte=end)
        user = self.request.user
        return qs if user.is_authenticated and user.is_admin else qs.filter(student__assigned_teacher__user=user)
    def perform_create(self,serializer):
        student=serializer.validated_data["student"]
        ensure_assigned(self.request.user,student)
        session=serializer.validated_data.get("session")
        if session and not self.request.user.is_admin and session.created_by_id != self.request.user.id: raise PermissionDenied("This attendance session does not belong to you.")
        serializer.save(recorded_by=self.request.user)
    def perform_update(self, serializer):
        student=serializer.validated_data.get("student", serializer.instance.student)
        ensure_assigned(self.request.user,student)
        if not self.request.user.is_admin and serializer.instance.recorded_by_id != self.request.user.id: raise PermissionDenied("You may only edit attendance you previously recorded.")
        session=serializer.validated_data.get("session",serializer.instance.session)
        if session and not self.request.user.is_admin and session.created_by_id != self.request.user.id: raise PermissionDenied("This attendance session does not belong to you.")
        serializer.save()
    def perform_destroy(self,instance):
        ensure_assigned(self.request.user,instance.student)
        if not self.request.user.is_admin and instance.recorded_by_id != self.request.user.id: raise PermissionDenied("You may only delete attendance you previously recorded.")
        instance.delete()
    @action(detail=False,methods=["post"])
    def bulk(self,request):
        serializer=BulkAttendanceSerializer(data=request.data,context={"request":request}); serializer.is_valid(raise_exception=True)
        for record in serializer.validated_data["records"]:
            ensure_assigned(request.user,record["student"])
            session=record.get("session")
            if session and not request.user.is_admin and session.created_by_id != request.user.id: raise PermissionDenied("An attendance session does not belong to you.")
        records=serializer.save(); return Response(AttendanceSerializer(records,many=True).data, status=201)
    @action(detail=False,methods=["get"])
    def statistics(self,request):
        qs=self.get_queryset()
        total=qs.count(); counts={row["status"]:row["count"] for row in qs.values("status").annotate(count=Count("id"))}
        attended=counts.get("present",0)+counts.get("late",0)
        return Response({"total":total,"present":counts.get("present",0),"absent":counts.get("absent",0),"late":counts.get("late",0),"excused":counts.get("excused",0),"attendance_percentage":round(attended*100/total,1) if total else 0})
class AttendanceSessionViewSet(ModelViewSet):
    serializer_class=AttendanceSessionSerializer
    filterset_fields=("date","teacher")
    ordering_fields=("date","created_at")
    def get_queryset(self):
        qs=AttendanceSession.objects.select_related("teacher__user","created_by").annotate(record_count=Count("records"))
        return qs if self.request.user.is_admin else qs.filter(created_by=self.request.user,teacher__user=self.request.user)
    def perform_create(self,serializer):
        user=self.request.user
        if user.is_admin: serializer.save(created_by=user)
        else:
            if not hasattr(user,"teacher_profile"): raise ValidationError("A teacher profile is required.")
            serializer.save(created_by=user,teacher=user.teacher_profile)
    def perform_update(self,serializer):
        if not self.request.user.is_admin and serializer.instance.created_by_id != self.request.user.id: raise PermissionDenied("This attendance session does not belong to you.")
        serializer.save(teacher=serializer.instance.teacher if not self.request.user.is_admin else serializer.validated_data.get("teacher",serializer.instance.teacher))
