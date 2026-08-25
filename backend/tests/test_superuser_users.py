from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from audit.models import AuditLog
from teachers.models import Teacher


class SuperuserUserApiTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser(
            "root", "root@example.com", "StrongRootPass123!", role=User.Role.TEACHER
        )
        self.client = APIClient()
        self.client.force_authenticate(self.root)

    def create_payload(self, **overrides):
        payload = {
            "username": "new-user",
            "first_name": "New",
            "last_name": "User",
            "email": "new@example.com",
            "role": User.Role.ADMIN,
            "password": "StrongNewPass123!",
            "password_confirm": "StrongNewPass123!",
        }
        payload.update(overrides)
        return payload

    def test_only_real_superusers_can_list_users(self):
        anonymous = APIClient()
        self.assertEqual(anonymous.get("/api/users/").status_code, 401)
        denied_users = [
            User.objects.create_user("teacher-denied", password="StrongPass123!", role=User.Role.TEACHER),
            User.objects.create_user("admin-denied", password="StrongPass123!", role=User.Role.ADMIN),
            User.objects.create_user("staff-denied", password="StrongPass123!", role=User.Role.TEACHER, is_staff=True),
        ]
        for user in denied_users:
            with self.subTest(user=user.username):
                client = APIClient(); client.force_authenticate(user)
                self.assertEqual(client.get("/api/users/").status_code, 403)
        self.assertEqual(self.client.get("/api/users/").status_code, 200)

    def test_every_account_management_endpoint_requires_a_real_superuser(self):
        target = User.objects.create_user("matrix-target", password="StrongPass123!")
        denied_users = [
            None,
            User.objects.create_user("matrix-teacher", password="StrongPass123!", role=User.Role.TEACHER),
            User.objects.create_user("matrix-admin", password="StrongPass123!", role=User.Role.ADMIN),
            User.objects.create_user("matrix-staff", password="StrongPass123!", is_staff=True),
        ]
        requests = [
            ("get", "/api/users/", None),
            ("post", "/api/users/", self.create_payload(username="blocked-create")),
            ("get", f"/api/users/{target.id}/", None),
            ("patch", f"/api/users/{target.id}/", {"first_name": "Blocked"}),
            ("post", f"/api/users/{target.id}/activate/", None),
            ("post", f"/api/users/{target.id}/deactivate/", None),
            ("post", f"/api/users/{target.id}/role/", {"role": User.Role.ADMIN}),
            ("post", f"/api/users/{target.id}/staff/", {"is_staff": True}),
            ("post", f"/api/users/{target.id}/superuser/", {"is_superuser": True}),
            ("post", f"/api/users/{target.id}/set-password/", {"password": "NewStrongPass123!", "password_confirm": "NewStrongPass123!"}),
            ("get", "/api/users/dashboard/", None),
        ]
        for user in denied_users:
            client = APIClient()
            if user is not None:
                client.force_authenticate(user)
            expected = 401 if user is None else 403
            for method, url, payload in requests:
                with self.subTest(user=getattr(user, "username", "anonymous"), method=method, url=url):
                    response = getattr(client, method)(url, payload, format="json") if payload is not None else getattr(client, method)(url)
                    self.assertEqual(response.status_code, expected)

    def test_auth_me_exposes_safe_capability_flags(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], User.Role.TEACHER)
        self.assertTrue(response.data["is_staff"])
        self.assertTrue(response.data["is_superuser"])
        self.assertTrue(response.data["is_admin"])
        self.assertNotIn("password", response.data)

    def test_create_application_admin(self):
        response = self.client.post("/api/users/", self.create_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="new-user")
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertFalse(user.is_superuser)
        self.assertFalse(Teacher.objects.filter(user=user).exists())
        login = APIClient().post("/api/auth/login/", {"username": "new-user", "password": "StrongNewPass123!"}, format="json")
        self.assertEqual(login.status_code, 200); self.assertIn("access", login.data)

    def test_create_teacher_and_profile_transactionally(self):
        response = self.client.post(
            "/api/users/",
            self.create_payload(role=User.Role.TEACHER, teacher_phone="555-0101"),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="new-user")
        self.assertTrue(user.check_password("StrongNewPass123!"))
        self.assertEqual(user.teacher_profile.phone, "555-0101")
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_confirm", response.data)
        login = APIClient().post("/api/auth/login/", {"username": "new-user", "password": "StrongNewPass123!"}, format="json")
        self.assertEqual(login.status_code, 200); self.assertIn("access", login.data)
        teacher_logs = AuditLog.objects.filter(object_type="Teacher", object_id=str(user.teacher_profile.id))
        self.assertEqual(teacher_logs.filter(action="teacher_profile_created", user=self.root).count(), 1)
        self.assertFalse(teacher_logs.filter(action="teacher_created").exists())

    def test_inactive_teacher_creation_keeps_profile_state_in_sync(self):
        response = self.client.post(
            "/api/users/",
            self.create_payload(role=User.Role.TEACHER, is_active=False),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="new-user")
        self.assertFalse(user.is_active); self.assertFalse(user.teacher_profile.is_active)
        self.assertEqual(APIClient().post("/api/auth/login/", {"username": "new-user", "password": "StrongNewPass123!"}, format="json").status_code, 401)

    def test_existing_teacher_endpoint_still_creates_user_and_profile(self):
        response = self.client.post(
            "/api/teachers/",
            {"username": "legacy-teacher", "password": "StrongTeacherPass123!", "first_name": "Legacy", "last_name": "Teacher", "email": "legacy@example.com", "phone": "789", "is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        teacher = Teacher.objects.get(user__username="legacy-teacher")
        self.assertTrue(teacher.user.check_password("StrongTeacherPass123!"))
        self.assertEqual(teacher.phone, "789")

    def test_invalid_teacher_data_does_not_create_user(self):
        before = User.objects.count()
        response = self.client.post(
            "/api/users/",
            self.create_payload(role=User.Role.TEACHER, teacher_phone="x" * 31),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), before)

    def test_create_superuser_sets_sensible_flags(self):
        response = self.client.post(
            "/api/users/",
            self.create_payload(is_superuser=True, is_staff=False),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="new-user")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user("new-user", password="StrongPass123!")
        response = self.client.post("/api/users/", self.create_payload(), format="json")
        self.assertEqual(response.status_code, 400)

    def test_list_search_filter_order_and_teacher_summary(self):
        teacher_user = User.objects.create_user("z-teacher", password="StrongPass123!", first_name="Zayd", role=User.Role.TEACHER)
        teacher = Teacher.objects.create(user=teacher_user, phone="123")
        response = self.client.get("/api/users/?search=Zayd&role=teacher&ordering=-username")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["teacher_profile"]["id"], teacher.id)

    def test_generic_patch_cannot_mass_assign_privileged_flags(self):
        target = User.objects.create_user("patch-target", password="StrongPass123!")
        response = self.client.patch(
            f"/api/users/{target.id}/",
            {"first_name": "Changed", "is_superuser": True, "is_staff": True, "role": User.Role.ADMIN, "is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        target.refresh_from_db()
        self.assertEqual(target.first_name, "Changed")
        self.assertFalse(target.is_superuser); self.assertFalse(target.is_staff)
        self.assertTrue(target.is_active); self.assertEqual(target.role, User.Role.TEACHER)

    def test_activate_and_deactivate_sync_teacher_profile(self):
        user = User.objects.create_user("status-teacher", password="StrongPass123!", role=User.Role.TEACHER)
        teacher = Teacher.objects.create(user=user)
        response = self.client.post(f"/api/users/{user.id}/deactivate/")
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db(); teacher.refresh_from_db()
        self.assertFalse(user.is_active); self.assertFalse(teacher.is_active)
        response = self.client.post(f"/api/users/{user.id}/activate/")
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db(); teacher.refresh_from_db()
        self.assertTrue(user.is_active); self.assertTrue(teacher.is_active)
        deactivated = AuditLog.objects.get(action="user_deactivated", object_id=str(user.id))
        activated = AuditLog.objects.get(action="user_activated", object_id=str(user.id))
        self.assertEqual(deactivated.metadata["before"], True); self.assertEqual(deactivated.metadata["after"], False)
        self.assertEqual(activated.metadata["before"], False); self.assertEqual(activated.metadata["after"], True)

    def test_self_deactivation_is_blocked(self):
        self.assertEqual(self.client.post(f"/api/users/{self.root.id}/deactivate/").status_code, 400)
        self.root.refresh_from_db(); self.assertTrue(self.root.is_active)

    def test_final_active_superuser_cannot_be_deactivated(self):
        inactive_actor = User.objects.create_superuser("inactive-root", "inactive@example.com", "StrongPass123!")
        inactive_actor.is_active = False; inactive_actor.save(update_fields=["is_active"])
        client = APIClient(); client.force_authenticate(inactive_actor)
        response = client.post(f"/api/users/{self.root.id}/deactivate/")
        self.assertEqual(response.status_code, 400)

    def test_role_changes_preserve_or_create_teacher_profile(self):
        teacher_user = User.objects.create_user("role-teacher", password="StrongPass123!", role=User.Role.TEACHER)
        teacher = Teacher.objects.create(user=teacher_user)
        response = self.client.post(f"/api/users/{teacher_user.id}/role/", {"role": User.Role.ADMIN}, format="json")
        self.assertEqual(response.status_code, 200)
        teacher.refresh_from_db(); self.assertFalse(teacher.is_active)
        self.assertTrue(Teacher.objects.filter(pk=teacher.pk).exists())

        admin_user = User.objects.create_user("role-admin", password="StrongPass123!", role=User.Role.ADMIN)
        response = self.client.post(f"/api/users/{admin_user.id}/role/", {"role": User.Role.TEACHER, "teacher_phone": "456"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(admin_user.teacher_profile.phone, "456")

    def test_invalid_role_is_rejected(self):
        target = User.objects.create_user("invalid-role", password="StrongPass123!")
        self.assertEqual(self.client.post(f"/api/users/{target.id}/role/", {"role": "student"}, format="json").status_code, 400)

    def test_password_is_hashed_and_never_returned(self):
        target = User.objects.create_user("credential-target", password="OldStrongPass123!")
        response = self.client.post(
            f"/api/users/{target.id}/set-password/",
            {"password": "NewStrongPass123!", "password_confirm": "NewStrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        target.refresh_from_db(); self.assertTrue(target.check_password("NewStrongPass123!"))
        self.assertNotIn("password", response.data)
        log = AuditLog.objects.get(action="user_password_changed", object_id=str(target.id))
        self.assertNotIn("NewStrongPass123!", str(log.metadata))
        self.assertNotIn("OldStrongPass123!", str(log.metadata))

    def test_password_confirmation_mismatch_is_rejected(self):
        target = User.objects.create_user("password-mismatch", password="OldStrongPass123!")
        response = self.client.post(
            f"/api/users/{target.id}/set-password/",
            {"password": "NewStrongPass123!", "password_confirm": "DifferentPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_application_admin_cannot_grant_superuser(self):
        admin = User.objects.create_user("ordinary-admin", password="StrongPass123!", role=User.Role.ADMIN)
        target = User.objects.create_user("grant-target", password="StrongPass123!")
        client = APIClient(); client.force_authenticate(admin)
        response = client.post(f"/api/users/{target.id}/superuser/", {"is_superuser": True}, format="json")
        self.assertEqual(response.status_code, 403)
        target.refresh_from_db(); self.assertFalse(target.is_superuser)

    def test_superuser_status_and_staff_have_dedicated_audited_actions(self):
        target = User.objects.create_user("privilege-target", password="StrongPass123!")
        self.assertEqual(self.client.post(f"/api/users/{target.id}/staff/", {"is_staff": True}, format="json").status_code, 200)
        self.assertEqual(self.client.post(f"/api/users/{target.id}/superuser/", {"is_superuser": True}, format="json").status_code, 200)
        target.refresh_from_db(); self.assertTrue(target.is_staff); self.assertTrue(target.is_superuser)
        self.assertTrue(AuditLog.objects.filter(user=self.root, action="user_staff_status_changed", object_id=str(target.id)).exists())
        self.assertTrue(AuditLog.objects.filter(user=self.root, action="user_superuser_status_changed", object_id=str(target.id)).exists())

    def test_staff_and_superuser_privileges_can_be_granted_and_revoked(self):
        target = User.objects.create_user("transition-target", password="StrongPass123!")
        second_root = User.objects.create_superuser("transition-root", "transition@example.com", "StrongPass123!")
        self.assertEqual(self.client.post(f"/api/users/{target.id}/staff/", {"is_staff": True}, format="json").status_code, 200)
        self.assertEqual(self.client.post(f"/api/users/{target.id}/staff/", {"is_staff": False}, format="json").status_code, 200)
        self.assertEqual(self.client.post(f"/api/users/{target.id}/superuser/", {"is_superuser": True}, format="json").status_code, 200)
        second_client = APIClient(); second_client.force_authenticate(second_root)
        self.assertEqual(second_client.post(f"/api/users/{target.id}/superuser/", {"is_superuser": False}, format="json").status_code, 200)
        target.refresh_from_db()
        self.assertFalse(target.is_staff); self.assertFalse(target.is_superuser)
        staff_logs = AuditLog.objects.filter(action="user_staff_status_changed", object_id=str(target.id)).order_by("timestamp")
        self.assertEqual([(log.metadata["before"], log.metadata["after"]) for log in staff_logs], [(False, True), (True, False)])
        superuser_logs = AuditLog.objects.filter(action="user_superuser_status_changed", object_id=str(target.id)).order_by("timestamp")
        self.assertEqual([(log.metadata["before"], log.metadata["after"]) for log in superuser_logs], [(False, True), (True, False)])

    def test_self_superuser_demotion_is_blocked(self):
        response = self.client.post(f"/api/users/{self.root.id}/superuser/", {"is_superuser": False}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_final_active_superuser_cannot_be_demoted(self):
        inactive_actor = User.objects.create_superuser("inactive-demoter", "demoter@example.com", "StrongPass123!")
        inactive_actor.is_active = False; inactive_actor.save(update_fields=["is_active"])
        client = APIClient(); client.force_authenticate(inactive_actor)
        response = client.post(f"/api/users/{self.root.id}/superuser/", {"is_superuser": False}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_creation_and_update_audits_identify_actor(self):
        created = self.client.post("/api/users/", self.create_payload(), format="json")
        self.assertEqual(created.status_code, 201)
        target_id = created.data["id"]
        self.client.patch(f"/api/users/{target_id}/", {"last_name": "Updated"}, format="json")
        self.assertTrue(AuditLog.objects.filter(user=self.root, action="user_created", object_id=str(target_id)).exists())
        self.assertTrue(AuditLog.objects.filter(user=self.root, action="user_updated", object_id=str(target_id)).exists())

    def test_teacher_audit_suppression_is_one_save_only(self):
        response = self.client.post("/api/users/", self.create_payload(role=User.Role.TEACHER), format="json")
        teacher = Teacher.objects.get(user_id=response.data["id"])
        self.assertFalse(hasattr(teacher, "_skip_automatic_audit"))
        teacher.phone = "555"
        teacher.save(update_fields=["phone", "updated_at"])
        self.assertTrue(AuditLog.objects.filter(action="teacher_updated", object_id=str(teacher.id)).exists())

    def test_superuser_dashboard_returns_account_metrics(self):
        User.objects.create_user("dashboard-admin", password="StrongPass123!", role=User.Role.ADMIN, is_active=False)
        response = self.client.get("/api/users/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["total_users"], 2)
        self.assertGreaterEqual(response.data["superusers"], 1)
        self.assertIn("recent_users", response.data)

    def test_superuser_with_teacher_role_can_use_admin_dashboard(self):
        response = self.client.get("/api/dashboard/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("teachers", response.data)
