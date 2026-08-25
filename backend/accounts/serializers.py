from django.contrib.auth import password_validation
from django.db import transaction
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import User
class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(read_only=True)
    has_profile_image = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "role", "is_active", "is_staff", "is_superuser", "is_admin", "has_profile_image")
        read_only_fields = ("id", "is_staff", "is_superuser", "is_admin")
    def get_has_profile_image(self, obj) -> bool:
        try:
            return bool(obj.teacher_profile.profile_image_pathname)
        except User.teacher_profile.RelatedObjectDoesNotExist:
            return False
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class SuperuserTeacherProfileSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    phone = serializers.CharField()
    is_active = serializers.BooleanField()
    student_count = serializers.IntegerField()
    has_profile_image = serializers.BooleanField()


class SuperuserUserOutputMixin:
    @extend_schema_field(SuperuserTeacherProfileSummarySerializer(allow_null=True))
    def get_teacher_profile(self, obj):
        try:
            teacher = obj.teacher_profile
        except User.teacher_profile.RelatedObjectDoesNotExist:
            return None
        return {
            "id": teacher.id,
            "phone": teacher.phone,
            "is_active": teacher.is_active,
            "student_count": getattr(obj, "teacher_student_count", teacher.students.count()),
            "has_profile_image": bool(teacher.profile_image_pathname),
        }


class SuperuserUserListSerializer(SuperuserUserOutputMixin, serializers.ModelSerializer):
    teacher_profile = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "role", "is_active", "is_staff", "is_superuser", "date_joined", "last_login", "teacher_profile")
        read_only_fields = fields


class SuperuserUserDetailSerializer(SuperuserUserListSerializer):
    is_admin = serializers.BooleanField(read_only=True)

    class Meta(SuperuserUserListSerializer.Meta):
        fields = (*SuperuserUserListSerializer.Meta.fields, "is_admin")


class SuperuserUserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=User.Role.choices)
    is_active = serializers.BooleanField(default=True)
    is_staff = serializers.BooleanField(default=False)
    is_superuser = serializers.BooleanField(default=False)
    teacher_phone = serializers.CharField(max_length=30, required=False, allow_blank=True, write_only=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        candidate = User(username=attrs["username"], first_name=attrs.get("first_name", ""), last_name=attrs.get("last_name", ""), email=attrs.get("email", ""))
        password_validation.validate_password(attrs["password"], user=candidate)
        if attrs.get("is_superuser"):
            attrs["is_staff"] = True
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        from .services import audit_user_action, ensure_teacher_profile

        actor = self.context["request"].user
        phone = validated_data.pop("teacher_phone", "")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        audit_user_action(
            actor=actor,
            action="user_created",
            target=user,
            metadata={"role": user.role, "is_active": user.is_active, "is_staff": user.is_staff, "is_superuser": user.is_superuser},
        )
        if user.role == User.Role.TEACHER:
            ensure_teacher_profile(user=user, phone=phone, is_active=user.is_active, actor=actor)
        return user


class SuperuserUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def validate_username(self, value):
        if User.objects.exclude(pk=self.instance.pk).filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value


class UserRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Role.choices)
    teacher_phone = serializers.CharField(max_length=30, required=False, allow_blank=True, write_only=True)


class UserStaffStatusSerializer(serializers.Serializer):
    is_staff = serializers.BooleanField()


class UserSuperuserStatusSerializer(serializers.Serializer):
    is_superuser = serializers.BooleanField()


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        password_validation.validate_password(attrs["password"], user=self.context.get("target_user"))
        return attrs
