from rest_framework import serializers
from accounts.models import User
from .models import Teacher
class TeacherSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    username = serializers.CharField(source="user.username", write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    student_count = serializers.IntegerField(read_only=True)
    class Meta: model = Teacher; fields = ("id", "username", "password", "first_name", "last_name", "email", "phone", "is_active", "student_count")
    def create(self, data):
        user_data = data.pop("user"); password = data.pop("password", None); username = user_data.pop("username", None) or user_data["email"]
        user = User.objects.create_user(username=username, password=password, role=User.Role.TEACHER, **user_data)
        return Teacher.objects.create(user=user, **data)
    def update(self, instance, data):
        user_data = data.pop("user", {}); password = data.pop("password", None)
        for key, value in user_data.items(): setattr(instance.user, key, value)
        if password: instance.user.set_password(password)
        instance.user.save()
        return super().update(instance, data)

