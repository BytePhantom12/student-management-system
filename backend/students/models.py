from django.conf import settings
from django.db import models
from teachers.models import Teacher
class Guardian(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "phone"], name="unique_guardian_name_phone")]
        indexes = [models.Index(fields=["name"]), models.Index(fields=["phone"])]
    def __str__(self): return f"{self.name} ({self.phone})"
class Student(models.Model):
    class Gender(models.TextChoices): MALE="male","Male"; FEMALE="female","Female"
    class Status(models.TextChoices): ACTIVE="active","Active"; INACTIVE="inactive","Inactive"
    student_id = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=100); last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=Gender.choices); date_of_birth = models.DateField()
    phone = models.CharField(max_length=30, blank=True); email = models.EmailField(blank=True); address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=200, blank=True, default=""); guardian_phone = models.CharField(max_length=30, blank=True, default=""); guardian_relationship = models.CharField(max_length=80, blank=True, default="")
    enrollment_date = models.DateField(); status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    assigned_teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT, related_name="students", null=True, blank=True)
    primary_guardian = models.ForeignKey(Guardian, on_delete=models.PROTECT, related_name="students", null=True, blank=True)
    profile_image_pathname = models.CharField(max_length=500, null=True, blank=True)
    notes = models.TextField(blank=True); created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)
    class Meta: indexes = [models.Index(fields=["last_name", "first_name"]), models.Index(fields=["assigned_teacher", "status"]), models.Index(fields=["primary_guardian", "status"])]
    def __str__(self): return f"{self.student_id} - {self.first_name} {self.last_name}"
class StudentNote(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="student_notes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="student_notes")
    content = models.TextField(); created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ["-created_at"]
