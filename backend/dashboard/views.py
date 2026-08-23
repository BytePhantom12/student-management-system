from django.db.models import Count,Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from attendance.models import Attendance
from hifz.models import HifzProgress
from students.models import Student
from teachers.models import Teacher
class DashboardView(APIView):
    def get(self,request):
        students=Student.objects.all() if request.user.is_admin else Student.objects.filter(assigned_teacher__user=request.user)
        attendance=Attendance.objects.filter(student__in=students,date=timezone.localdate())
        counts=attendance.values("status").annotate(count=Count("id")); total=attendance.count(); present=attendance.filter(status__in=["present","late"]).count()
        data={"students":{"total":students.count(),"active":students.filter(status="active").count(),"inactive":students.filter(status="inactive").count()},"today_attendance":{x["status"]:x["count"] for x in counts},"attendance_percentage":round(present*100/total,1) if total else 0,"recent_hifz":list(HifzProgress.objects.filter(student__in=students).select_related("student").values("id","student__first_name","student__last_name","surah","progress_percentage","status")[:8])}
        if request.user.is_admin: data.update({"teachers":Teacher.objects.filter(is_active=True).count(),"students_by_teacher":list(Teacher.objects.values("id","user__first_name","user__last_name").annotate(count=Count("students",filter=Q(students__status="active"))))})
        return Response(data)

