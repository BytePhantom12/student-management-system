from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from attendance.models import Attendance, AttendanceSession
from hifz.models import HifzProgress
from students.models import Guardian, Student, StudentNote
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
    def test_teacher_cannot_delete_assigned_student(self):
        self.client.force_authenticate(self.teacher_user)
        self.assertEqual(self.client.delete(f"/api/students/{self.assigned.id}/").status_code, 403)
        self.assertTrue(Student.objects.filter(pk=self.assigned.pk).exists())
    def test_admin_sees_all_students(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/students/").json()["count"],2)
    def test_anonymous_is_rejected(self):
        self.assertEqual(self.client.get("/api/students/").status_code,401)
    def test_teacher_cannot_reassign_student(self):
        self.client.force_authenticate(self.teacher_user)
        response=self.client.patch(f"/api/students/{self.assigned.id}/", {"assigned_teacher":self.other.id}, format="json")
        self.assertEqual(response.status_code,200)
        self.assigned.refresh_from_db()
        self.assertEqual(self.assigned.assigned_teacher,self.teacher)
    def test_teacher_cannot_move_attendance_to_other_student(self):
        attendance=Attendance.objects.create(student=self.assigned,date=date.today(),status="present",recorded_by=self.teacher_user)
        self.client.force_authenticate(self.teacher_user)
        response=self.client.patch(f"/api/attendance/{attendance.id}/", {"student":self.hidden.id}, format="json")
        self.assertEqual(response.status_code,403)
    def test_teacher_cannot_access_admin_dashboard(self):
        self.client.force_authenticate(self.teacher_user)
        self.assertEqual(self.client.get("/api/dashboard/admin/").status_code,403)
    def test_teacher_only_sees_guardians_for_assigned_students(self):
        visible = Guardian.objects.create(name="Visible Guardian", phone="100")
        hidden = Guardian.objects.create(name="Hidden Guardian", phone="200")
        self.assigned.primary_guardian = visible
        self.assigned.save(update_fields=["primary_guardian"])
        self.hidden.primary_guardian = hidden
        self.hidden.save(update_fields=["primary_guardian"])
        self.client.force_authenticate(self.teacher_user)
        response = self.client.get("/api/guardians/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data["results"]], [visible.id])
        self.assertEqual(self.client.get(f"/api/guardians/{hidden.id}/").status_code, 404)

    def test_teacher_can_only_change_notes_they_authored(self):
        own = StudentNote.objects.create(student=self.assigned, author=self.teacher_user, content="Own")
        other = StudentNote.objects.create(student=self.assigned, author=self.other_user, content="Other")
        self.client.force_authenticate(self.teacher_user)
        self.assertEqual(
            self.client.patch(f"/api/students/notes/{other.id}/", {"content": "Changed"}, format="json").status_code,
            403,
        )
        self.assertEqual(self.client.delete(f"/api/students/notes/{other.id}/").status_code, 403)
        self.assertEqual(
            self.client.patch(f"/api/students/notes/{own.id}/", {"content": "Changed"}, format="json").status_code,
            200,
        )
        self.assertEqual(self.client.delete(f"/api/students/notes/{own.id}/").status_code, 204)

class DomainValidationTests(CoreAuthorizationTests):
    def test_invalid_hifz_range(self):
        item=HifzProgress(student=self.assigned,surah=115,juz=1,progress_percentage=0)
        with self.assertRaises(ValidationError): item.full_clean()
    def test_completion_requires_100_percent(self):
        item=HifzProgress(student=self.assigned,surah=1,juz=1,status="completed",progress_percentage=90,date_started=date.today(),date_completed=date.today())
        with self.assertRaises(ValidationError): item.full_clean()
    def test_invalid_completion_returns_bad_request(self):
        self.client.force_authenticate(self.teacher_user)
        response=self.client.post("/api/hifz/", {"student":self.assigned.id,"surah":1,"juz":1,"status":"completed","progress_percentage":90}, format="json")
        self.assertEqual(response.status_code,400)
    def test_attendance_is_unique_per_day(self):
        Attendance.objects.create(student=self.assigned,date=date.today(),status="present",recorded_by=self.teacher_user)
        duplicate=Attendance(student=self.assigned,date=date.today(),status="absent",recorded_by=self.teacher_user)
        with self.assertRaises(ValidationError): duplicate.full_clean()

class StudentRelationshipTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("relationship-admin", password="StrongPass123!", role="admin")
        teacher_user = User.objects.create_user("relationship-teacher", password="StrongPass123!", role="teacher")
        self.teacher = Teacher.objects.create(user=teacher_user)
        self.guardian = Guardian.objects.create(name="Amina Ahmad", phone="555-0100")
        self.client = APIClient(); self.client.force_authenticate(self.admin)
        self.payload = {"student_id":"S100", "first_name":"Sara", "last_name":"Ahmad", "gender":"female", "date_of_birth":"2012-01-01", "guardian_relationship":"Mother", "enrollment_date":str(date.today()), "assigned_teacher":self.teacher.id, "primary_guardian":self.guardian.id}
    def test_student_can_be_created_with_existing_teacher_and_guardian(self):
        response = self.client.post("/api/students/", self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["teacher"]["id"], self.teacher.id)
        self.assertEqual(response.data["parent"]["id"], self.guardian.id)
        self.assertEqual(response.data["guardian_name"], self.guardian.name)
    def test_new_student_requires_primary_guardian(self):
        self.payload.pop("primary_guardian")
        response = self.client.post("/api/students/", self.payload, format="json")
        self.assertEqual(response.status_code, 400)
    def test_guardian_endpoint_returns_associated_students(self):
        student = Student.objects.create(student_id="S101", first_name="Musa", last_name="Ahmad", gender="male", date_of_birth=date(2011,1,1), guardian_name=self.guardian.name, guardian_phone=self.guardian.phone, guardian_relationship="Mother", enrollment_date=date.today(), assigned_teacher=self.teacher, primary_guardian=self.guardian)
        response = self.client.get(f"/api/guardians/{self.guardian.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["students"][0]["id"], student.id)

class TeacherAttendanceTests(CoreAuthorizationTests):
    def test_teacher_creates_session_for_self(self):
        self.client.force_authenticate(self.teacher_user)
        response=self.client.post("/api/attendance/sessions/",{"date":str(date.today()),"title":"Morning"},format="json")
        self.assertEqual(response.status_code,201)
        session=AttendanceSession.objects.get(pk=response.data["id"])
        self.assertEqual(session.teacher,self.teacher); self.assertEqual(session.created_by,self.teacher_user)
    def test_teacher_marks_only_assigned_students(self):
        session=AttendanceSession.objects.create(date=date.today(),teacher=self.teacher,created_by=self.teacher_user)
        self.client.force_authenticate(self.teacher_user)
        allowed=self.client.post("/api/attendance/",{"student":self.assigned.id,"date":str(date.today()),"status":"late","session":session.id},format="json")
        denied=self.client.post("/api/attendance/",{"student":self.hidden.id,"date":str(date.today()),"status":"present","session":session.id},format="json")
        self.assertEqual(allowed.status_code,201); self.assertEqual(denied.status_code,403)
    def test_bulk_attendance_creates_only_for_assigned_students(self):
        session = AttendanceSession.objects.create(date=date.today(), teacher=self.teacher, created_by=self.teacher_user)
        self.client.force_authenticate(self.teacher_user)
        allowed = self.client.post(
            "/api/attendance/bulk/",
            {"records": [{"student": self.assigned.id, "date": str(date.today()), "status": "excused", "session": session.id}]},
            format="json",
        )
        self.assertEqual(allowed.status_code, 201)
        self.assertEqual(Attendance.objects.get(student=self.assigned).status, "excused")
        denied = self.client.post(
            "/api/attendance/bulk/",
            {"records": [{"student": self.hidden.id, "date": str(date.today()), "status": "present", "session": session.id}]},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)
        self.assertFalse(Attendance.objects.filter(student=self.hidden).exists())
    def test_teacher_cannot_view_other_teacher_attendance(self):
        Attendance.objects.create(student=self.hidden,date=date.today(),status="present",recorded_by=self.other_user)
        self.client.force_authenticate(self.teacher_user)
        response=self.client.get("/api/attendance/")
        self.assertEqual(response.data["count"],0)
    def test_teacher_cannot_edit_record_created_by_another_user(self):
        record=Attendance.objects.create(student=self.assigned,date=date.today(),status="present",recorded_by=self.admin)
        self.client.force_authenticate(self.teacher_user)
        response=self.client.patch(f"/api/attendance/{record.id}/",{"status":"absent"},format="json")
        self.assertEqual(response.status_code,403)
    def test_admin_can_edit_any_attendance(self):
        record=Attendance.objects.create(student=self.assigned,date=date.today(),status="present",recorded_by=self.teacher_user)
        self.client.force_authenticate(self.admin)
        response=self.client.patch(f"/api/attendance/{record.id}/",{"status":"excused"},format="json")
        self.assertEqual(response.status_code,200)
    def test_statistics_are_scoped_to_teacher_students(self):
        Attendance.objects.create(student=self.assigned,date=date.today(),status="late",recorded_by=self.teacher_user)
        Attendance.objects.create(student=self.hidden,date=date.today(),status="absent",recorded_by=self.other_user)
        self.client.force_authenticate(self.teacher_user)
        response=self.client.get("/api/attendance/statistics/")
        self.assertEqual(response.data["total"],1); self.assertEqual(response.data["late"],1); self.assertEqual(response.data["absent"],0)
    def test_teacher_cannot_access_another_teachers_session(self):
        session = AttendanceSession.objects.create(date=date.today(), teacher=self.other, created_by=self.other_user)
        self.client.force_authenticate(self.teacher_user)
        self.assertEqual(self.client.get(f"/api/attendance/sessions/{session.id}/").status_code, 404)
        self.assertEqual(self.client.patch(f"/api/attendance/sessions/{session.id}/", {"title": "Changed"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/attendance/sessions/{session.id}/").status_code, 404)

    def test_teacher_can_update_and_delete_own_attendance(self):
        record = Attendance.objects.create(student=self.assigned, date=date.today(), status="present", recorded_by=self.teacher_user)
        self.client.force_authenticate(self.teacher_user)
        self.assertEqual(self.client.patch(f"/api/attendance/{record.id}/", {"status": "late"}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/attendance/{record.id}/").status_code, 204)

    def test_admin_can_manage_any_session(self):
        session = AttendanceSession.objects.create(date=date.today(), teacher=self.other, created_by=self.other_user)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.patch(f"/api/attendance/sessions/{session.id}/", {"title": "Admin edit"}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/attendance/sessions/{session.id}/").status_code, 204)
