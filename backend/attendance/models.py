from django.conf import settings
from django.db import models
from students.models import Student
from teachers.models import Teacher
class AttendanceSession(models.Model):
    date=models.DateField(db_index=True)
    title=models.CharField(max_length=150,blank=True)
    teacher=models.ForeignKey(Teacher,on_delete=models.PROTECT,related_name="attendance_sessions",null=True,blank=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="attendance_sessions_created")
    notes=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=["-date","-created_at"]
        indexes=[models.Index(fields=["teacher","date"])]
    def __str__(self): return self.title or f"Attendance - {self.date}"
class Attendance(models.Model):
    class Status(models.TextChoices): PRESENT="present","Present"; ABSENT="absent","Absent"; LATE="late","Late"; EXCUSED="excused","Excused"
    student=models.ForeignKey(Student,on_delete=models.PROTECT,related_name="attendance")
    date=models.DateField(db_index=True); status=models.CharField(max_length=10,choices=Status.choices)
    recorded_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="attendance_recorded")
    session=models.ForeignKey(AttendanceSession,on_delete=models.PROTECT,related_name="records",null=True,blank=True)
    notes=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["student","date"],name="unique_student_attendance_date")]
        ordering=["-date","student__last_name"]
