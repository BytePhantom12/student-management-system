from rest_framework import serializers
from django.db import transaction
from accounts.models import User
from accounts.services import create_teacher_account
from .models import Teacher
class TeacherSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    username = serializers.CharField(source="user.username", write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    student_count = serializers.IntegerField(read_only=True)
    students = serializers.SerializerMethodField()
    has_profile_image = serializers.SerializerMethodField()
    class Meta: model = Teacher; fields = ("id", "username", "password", "first_name", "last_name", "email", "phone", "is_active", "student_count", "students", "has_profile_image")
    def get_students(self, obj):
        return [{"id": s.id, "student_id": s.student_id, "name": f"{s.first_name} {s.last_name}"} for s in obj.students.all()]
    def get_has_profile_image(self, obj) -> bool: return bool(obj.profile_image_pathname)
    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "This field is required."})
        user_data = attrs.get("user", {})
        username = user_data.get("username") or (user_data.get("email") if self.instance is None else None)
        if username:
            users = User.objects.all()
            if self.instance is not None:
                users = users.exclude(pk=self.instance.user_id)
            if users.filter(username=username).exists():
                raise serializers.ValidationError({"username": "A user with that username already exists."})
        return attrs
    def create(self, data):
        user_data = data.pop("user"); password = data.pop("password", None); username = user_data.pop("username", None) or user_data["email"]
        _, teacher = create_teacher_account(username=username, password=password, phone=data.get("phone", ""), is_active=data.get("is_active", True), **user_data)
        return teacher
    @transaction.atomic
    def update(self, instance, data):
        user_data = data.pop("user", {}); password = data.pop("password", None)
        for key, value in user_data.items(): setattr(instance.user, key, value)
        if password: instance.user.set_password(password)
        if "is_active" in data: instance.user.is_active = data["is_active"]
        instance.user.save()
        return super().update(instance, data)


class TeacherSelfSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)
    full_name = serializers.SerializerMethodField()
    has_profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ("id", "username", "first_name", "last_name", "full_name", "email", "phone", "role", "is_active", "has_profile_image")
        read_only_fields = fields

    def get_full_name(self, obj) -> str: return obj.user.get_full_name() or obj.user.username
    def get_has_profile_image(self, obj) -> bool: return bool(obj.profile_image_pathname)
