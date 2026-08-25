from django.db.models import Count,Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from attendance.models import Attendance
from hifz.models import HifzProgress
from students.models import Student
from teachers.models import Teacher
from common import IsAdmin
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
DASHBOARD_RESPONSE = inline_serializer("Dashboard", {
    "students": inline_serializer("StudentCounts", {"total": serializers.IntegerField(), "active": serializers.IntegerField(), "inactive": serializers.IntegerField()}),
    "today_attendance": serializers.DictField(child=serializers.IntegerField()),
    "attendance_percentage": serializers.FloatField(),
    "recent_hifz": inline_serializer("RecentHifz", {"id": serializers.IntegerField(), "student__first_name": serializers.CharField(), "student__last_name": serializers.CharField(), "surah": serializers.IntegerField(), "progress_percentage": serializers.IntegerField(), "status": serializers.CharField()}, many=True),
    "teachers": serializers.IntegerField(required=False),
    "students_by_teacher": inline_serializer("StudentsByTeacher", {"id": serializers.IntegerField(), "user__first_name": serializers.CharField(), "user__last_name": serializers.CharField(), "count": serializers.IntegerField()}, many=True, required=False),
})
class DashboardView(APIView):
    @extend_schema(responses=DASHBOARD_RESPONSE)
    def get(self,request):
        students=Student.objects.all() if request.user.is_admin else Student.objects.filter(assigned_teacher__user=request.user)
        attendance=Attendance.objects.filter(student__in=students,date=timezone.localdate())
        counts=attendance.values("status").annotate(count=Count("id")); total=attendance.count(); present=attendance.filter(status__in=["present","late"]).count()
        data={"students":{"total":students.count(),"active":students.filter(status="active").count(),"inactive":students.filter(status="inactive").count()},"today_attendance":{x["status"]:x["count"] for x in counts},"attendance_percentage":round(present*100/total,1) if total else 0,"recent_hifz":list(HifzProgress.objects.filter(student__in=students).select_related("student").values("id","student__first_name","student__last_name","surah","progress_percentage","status")[:8])}
        if request.user.is_admin: data.update({"teachers":Teacher.objects.filter(is_active=True).count(),"students_by_teacher":list(Teacher.objects.values("id","user__first_name","user__last_name").annotate(count=Count("students",filter=Q(students__status="active"))))})
        return Response(data)
class AdminDashboardView(DashboardView):
    permission_classes = [IsAdmin]
