from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Attendance
from .serializers import AttendanceSerializer,BulkAttendanceSerializer
class AttendanceViewSet(ModelViewSet):
    serializer_class=AttendanceSerializer; filterset_fields=("student","status","date","student__assigned_teacher"); ordering_fields=("date","status","created_at")
    def get_queryset(self):
        qs=Attendance.objects.select_related("student","recorded_by","student__assigned_teacher")
        start=self.request.query_params.get("date_after"); end=self.request.query_params.get("date_before")
        if start: qs=qs.filter(date__gte=start)
        if end: qs=qs.filter(date__lte=end)
        return qs if self.request.user.is_admin else qs.filter(student__assigned_teacher__user=self.request.user)
    def perform_create(self,serializer):
        student=serializer.validated_data["student"]
        if not self.request.user.is_admin and student.assigned_teacher.user_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This student is not assigned to you.")
        serializer.save(recorded_by=self.request.user)
    @action(detail=False,methods=["post"])
    def bulk(self,request):
        serializer=BulkAttendanceSerializer(data=request.data,context={"request":request}); serializer.is_valid(raise_exception=True)
        for record in serializer.validated_data["records"]:
            if not request.user.is_admin and record["student"].assigned_teacher.user_id != request.user.id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("A student is not assigned to you.")
        records=serializer.save(); return Response(AttendanceSerializer(records,many=True).data, status=201)

