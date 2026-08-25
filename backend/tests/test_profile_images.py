from datetime import date
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from accounts.models import User
from audit.models import AuditLog
from blob_storage import BlobStorageUnavailableError, PrivateBlob
from students.models import Student
from teachers.models import Teacher


def valid_image(name="profile.png"):
    output = BytesIO()
    Image.new("RGB", (32, 24), "#176b56").save(output, format="PNG")
    return SimpleUploadedFile(name, output.getvalue(), content_type="image/png")


class ProfileImageAuthorizationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("image-admin", password="StrongPass123!", role=User.Role.ADMIN)
        self.superuser = User.objects.create_superuser("image-root", "root@example.com", "StrongPass123!")
        self.teacher_user = User.objects.create_user("image-teacher", password="StrongPass123!", role=User.Role.TEACHER)
        self.other_user = User.objects.create_user("image-other", password="StrongPass123!", role=User.Role.TEACHER)
        self.teacher = Teacher.objects.create(user=self.teacher_user, profile_image_pathname="profile-images/teachers/1/current.webp")
        self.other_teacher = Teacher.objects.create(user=self.other_user, profile_image_pathname="profile-images/teachers/2/current.webp")
        defaults = dict(
            gender="male", date_of_birth=date(2010, 1, 1), guardian_name="Guardian",
            guardian_phone="123", guardian_relationship="Parent", enrollment_date=date.today(),
            profile_image_pathname="profile-images/students/1/current.webp",
        )
        self.assigned = Student.objects.create(student_id="IMG001", first_name="Ali", last_name="Ahmad", assigned_teacher=self.teacher, **defaults)
        self.hidden = Student.objects.create(student_id="IMG002", first_name="Umar", last_name="Noor", assigned_teacher=self.other_teacher, **defaults)
        self.client = APIClient()
        self.private_blob = PrivateBlob(b"image-content", "image/webp", '"etag"', 200)

    def assert_image_response(self, user, url, expected=200):
        self.client.force_authenticate(user=user)
        with patch("profile_images.fetch_private_blob", return_value=self.private_blob):
            response = self.client.get(url)
        self.assertEqual(response.status_code, expected)
        if expected == 200:
            self.assertEqual(b"".join(response.streaming_content), b"image-content")
            self.assertEqual(response["Cache-Control"], "private, no-cache")

    def test_admin_and_superuser_can_view_any_student_image(self):
        self.assert_image_response(self.admin, f"/api/students/{self.hidden.id}/profile-image/")
        self.assert_image_response(self.superuser, f"/api/students/{self.hidden.id}/profile-image/")

    def test_assigned_teacher_can_view_student_image(self):
        self.assert_image_response(self.teacher_user, f"/api/students/{self.assigned.id}/profile-image/")

    def test_unassigned_teacher_cannot_view_student_image(self):
        self.assert_image_response(self.teacher_user, f"/api/students/{self.hidden.id}/profile-image/", 404)

    def test_teacher_can_view_own_image_but_not_another_teacher(self):
        self.assert_image_response(self.teacher_user, "/api/teachers/me/profile-image/")
        self.assert_image_response(self.teacher_user, f"/api/teachers/{self.other_teacher.id}/profile-image/", 403)

    def test_anonymous_image_access_is_denied(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(f"/api/students/{self.assigned.id}/profile-image/").status_code, 401)
        self.assertEqual(self.client.get("/api/teachers/me/profile-image/").status_code, 401)

    def test_teacher_self_profile_never_exposes_blob_pathname(self):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.get("/api/teachers/me/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["has_profile_image"])
        self.assertNotIn("profile_image_pathname", response.data)
        self.assertNotIn("BLOB_READ_WRITE_TOKEN", str(response.data))


class ProfileImageUploadTests(ProfileImageAuthorizationTests):
    @patch("profile_images.upload_profile_image", return_value="profile-images/students/1/new.webp")
    def test_assigned_teacher_can_update_student_image(self, upload):
        self.assigned.profile_image_pathname = None
        self.assigned.save(update_fields=["profile_image_pathname"])
        self.client.force_authenticate(self.teacher_user)
        response = self.client.post(f"/api/students/{self.assigned.id}/profile-image/", {"image": valid_image()}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assigned.refresh_from_db()
        self.assertEqual(self.assigned.profile_image_pathname, upload.return_value)
        upload.assert_called_once()
        self.assertTrue(AuditLog.objects.filter(user=self.teacher_user, action="student_profile_image_updated", object_id=str(self.assigned.id)).exists())

    @patch("profile_images.upload_profile_image")
    def test_unassigned_teacher_cannot_upload_student_image(self, upload):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.post(f"/api/students/{self.hidden.id}/profile-image/", {"image": valid_image()}, format="multipart")
        self.assertEqual(response.status_code, 404)
        upload.assert_not_called()

    @patch("profile_images.delete_profile_image")
    @patch("profile_images.upload_profile_image", return_value="profile-images/students/1/replacement.webp")
    def test_replacement_updates_database_then_deletes_old_blob(self, upload, delete):
        old = self.assigned.profile_image_pathname
        self.client.force_authenticate(self.admin)
        response = self.client.post(f"/api/students/{self.assigned.id}/profile-image/", {"image": valid_image()}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assigned.refresh_from_db()
        self.assertEqual(self.assigned.profile_image_pathname, upload.return_value)
        delete.assert_called_once_with(old)

    @patch("profile_images.delete_profile_image", side_effect=BlobStorageUnavailableError("unavailable"))
    @patch("profile_images.upload_profile_image", return_value="profile-images/students/1/replacement.webp")
    def test_old_blob_cleanup_failure_does_not_undo_successful_replacement(self, upload, delete):
        self.client.force_authenticate(self.admin)
        response = self.client.post(f"/api/students/{self.assigned.id}/profile-image/", {"image": valid_image()}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assigned.refresh_from_db()
        self.assertEqual(self.assigned.profile_image_pathname, upload.return_value)
        delete.assert_called_once()

    @patch("profile_images.upload_profile_image", return_value="profile-images/teachers/1/new.webp")
    def test_admin_can_update_teacher_image(self, upload):
        self.client.force_authenticate(self.admin)
        response = self.client.post(f"/api/teachers/{self.teacher.id}/profile-image/", {"image": valid_image()}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.profile_image_pathname, upload.return_value)

    @patch("profile_images.upload_profile_image", return_value="profile-images/teachers/1/self.webp")
    def test_teacher_can_update_own_image(self, upload):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.post("/api/teachers/me/profile-image/", {"image": valid_image()}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.profile_image_pathname, upload.return_value)

    @patch("profile_images.upload_profile_image")
    def test_invalid_and_oversized_files_are_rejected_before_blob_upload(self, upload):
        self.client.force_authenticate(self.admin)
        invalid = SimpleUploadedFile("fake.jpg", b"not an image", content_type="image/jpeg")
        self.assertEqual(self.client.post(f"/api/students/{self.assigned.id}/profile-image/", {"image": invalid}, format="multipart").status_code, 400)
        oversized = SimpleUploadedFile("large.png", b"0" * (3 * 1024 * 1024 + 1), content_type="image/png")
        self.assertEqual(self.client.post(f"/api/students/{self.assigned.id}/profile-image/", {"image": oversized}, format="multipart").status_code, 400)
        upload.assert_not_called()

    @patch("profile_images.upload_profile_image")
    def test_missing_image_is_rejected(self, upload):
        self.client.force_authenticate(self.admin)
        response = self.client.post(f"/api/students/{self.assigned.id}/profile-image/", {}, format="multipart")
        self.assertEqual(response.status_code, 400)
        upload.assert_not_called()

    @patch("profile_images.delete_profile_image")
    def test_remove_clears_reference_and_creates_safe_audit(self, delete):
        old = self.assigned.profile_image_pathname
        self.client.force_authenticate(self.teacher_user)
        response = self.client.delete(f"/api/students/{self.assigned.id}/profile-image/")
        self.assertEqual(response.status_code, 204)
        self.assigned.refresh_from_db()
        self.assertIsNone(self.assigned.profile_image_pathname)
        delete.assert_called_once_with(old)
        log = AuditLog.objects.get(action="student_profile_image_removed", object_id=str(self.assigned.id))
        self.assertEqual(log.metadata, {"before": True, "after": False})

    @patch("profile_images.upload_profile_image", side_effect=BlobStorageUnavailableError("provider secret response"))
    def test_blob_failure_returns_clean_service_error(self, upload):
        self.client.force_authenticate(self.admin)
        response = self.client.post(f"/api/students/{self.assigned.id}/profile-image/", {"image": valid_image()}, format="multipart")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("provider secret response", str(response.data))

    def test_missing_profile_image_returns_not_found_without_blob_request(self):
        self.assigned.profile_image_pathname = None
        self.assigned.save(update_fields=["profile_image_pathname"])
        self.client.force_authenticate(self.admin)
        with patch("profile_images.fetch_private_blob") as fetch:
            response = self.client.get(f"/api/students/{self.assigned.id}/profile-image/")
        self.assertEqual(response.status_code, 404)
        fetch.assert_not_called()
