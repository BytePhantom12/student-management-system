from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    class Role(models.TextChoices): ADMIN = "admin", "Admin"; TEACHER = "teacher", "Teacher"
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.TEACHER, db_index=True)
    @property
    def is_admin(self): return self.is_superuser or self.role == self.Role.ADMIN

