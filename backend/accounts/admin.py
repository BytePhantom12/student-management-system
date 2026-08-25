from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from attendance.models import Attendance, AttendanceSession
from audit.models import AuditLog
from hifz.models import HifzProgress
from students.models import Guardian, Student, StudentNote
from teachers.models import Teacher

from .models import User


admin.site.register(User, UserAdmin)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "is_active", "has_profile_image", "created_at")
    list_filter = ("is_active",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email", "phone")
    list_select_related = ("user",)
    @admin.display(boolean=True, description="Profile image")
    def has_profile_image(self, obj): return bool(obj.profile_image_pathname)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "first_name", "last_name", "status", "assigned_teacher", "primary_guardian", "has_profile_image", "enrollment_date")
    list_filter = ("status", "gender", "assigned_teacher", "primary_guardian", "enrollment_date")
    search_fields = ("student_id", "first_name", "last_name", "email", "phone", "guardian_name", "guardian_phone")
    list_select_related = ("assigned_teacher", "assigned_teacher__user", "primary_guardian")
    autocomplete_fields = ("assigned_teacher", "primary_guardian")
    date_hierarchy = "enrollment_date"
    @admin.display(boolean=True, description="Profile image")
    def has_profile_image(self, obj): return bool(obj.profile_image_pathname)

@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "phone", "email")


@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    list_display = ("student", "author", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("student__student_id", "student__first_name", "student__last_name", "author__username", "content")
    list_select_related = ("student", "author")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "status", "session", "recorded_by", "updated_at")
    list_filter = ("status", "date", "session")
    search_fields = ("student__student_id", "student__first_name", "student__last_name", "recorded_by__username", "notes")
    list_select_related = ("student", "recorded_by", "session")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ("date", "title", "teacher", "created_by", "created_at")
    list_filter = ("date", "teacher")
    search_fields = ("title", "teacher__user__first_name", "teacher__user__last_name", "created_by__username")
    list_select_related = ("teacher", "teacher__user", "created_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(HifzProgress)
class HifzProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "surah", "juz", "status", "progress_percentage", "revision_status", "updated_at")
    list_filter = ("status", "revision_status", "juz")
    search_fields = ("student__student_id", "student__first_name", "student__last_name", "teacher_notes")
    list_select_related = ("student",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "object_type", "object_id")
    list_filter = ("action", "object_type", "timestamp")
    search_fields = ("user__username", "action", "object_type", "object_id")
    list_select_related = ("user",)
    date_hierarchy = "timestamp"
    readonly_fields = ("user", "action", "object_type", "object_id", "metadata", "timestamp")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
