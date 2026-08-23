from django.conf import settings
from django.db import models
from students.models import Student
class Attendance(models.Model):
    class Status(models.TextChoices): PRESENT="present","Present"; ABSENT="absent","Absent"; LATE="late","Late"; EXCUSED="excused","Excused"
    student=models.ForeignKey(Student,on_delete=models.PROTECT,related_name="attendance")
    date=models.DateField(db_index=True); status=models.CharField(max_length=10,choices=Status.choices)
    recorded_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="attendance_recorded")
    notes=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["student","date"],name="unique_student_attendance_date")]
        ordering=["-date","student__last_name"]

