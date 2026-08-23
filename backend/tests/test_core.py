from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from attendance.models import Attendance
from hifz.models import HifzProgress
from students.models import Student
from teachers.models import Teacher

class CoreAuthorizationTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user("admin",password="StrongPass123!",role="admin")
        self.teacher_user=User.objects.create_user("teacher",password="StrongPass123!",role="teacher")
        self.other_user=User.objects.create_user("other",password="StrongPass123!",role="teacher")
        self.teacher=Teacher.objects.create(user=self.teacher_user)
        self.other=Teacher.objects.create(user=self.other_user)
        defaults=dict(gender="male",date_of_birth=date(2010,1,1),guardian_name="Guardian",guardian_phone="123",guardian_relationship="Parent",enrollment_date=date.today())
        self.assigned=Student.objects.create(student_id="S001",first_name="Ali",last_name="Ahmad",assigned_teacher=self.teacher,**defaults)
        self.hidden=Student.objects.create(student_id="S002",first_name="Umar",last_name="Noor",assigned_teacher=self.other,**defaults)
        self.client=APIClient()
    def test_teacher_only_lists_assigned_students(self):
        self.client.force_authenticate(self.teacher_user); data=self.client.get("/api/students/").json()
        self.assertEqual([x["student_id"] for x in data["results"]],["S001"])
    def test_teacher_cannot_retrieve_other_student(self):
        self.client.force_authenticate(self.teacher_user)
        self.assertEqual(self.client.get(f"/api/students/{self.hidden.id}/").status_code,404)
    def test_admin_sees_all_students(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/students/").json()["count"],2)
    def test_anonymous_is_rejected(self):
        self.assertEqual(self.client.get("/api/students/").status_code,401)

class DomainValidationTests(CoreAuthorizationTests):
    def test_invalid_hifz_range(self):
        item=HifzProgress(student=self.assigned,surah=115,juz=1,progress_percentage=0)
        with self.assertRaises(ValidationError): item.full_clean()
    def test_completion_requires_100_percent(self):
        item=HifzProgress(student=self.assigned,surah=1,juz=1,status="completed",progress_percentage=90,date_started=date.today(),date_completed=date.today())
        with self.assertRaises(ValidationError): item.full_clean()
    def test_attendance_is_unique_per_day(self):
        Attendance.objects.create(student=self.assigned,date=date.today(),status="present",recorded_by=self.teacher_user)
        duplicate=Attendance(student=self.assigned,date=date.today(),status="absent",recorded_by=self.teacher_user)
        with self.assertRaises(ValidationError): duplicate.full_clean()
