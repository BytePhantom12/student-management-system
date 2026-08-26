from rest_framework import serializers
from .models import Guardian, Student, StudentNote
class GuardianSummarySerializer(serializers.ModelSerializer):
    class Meta: model = Guardian; fields = ("id", "name", "phone", "email", "is_active")
class TeacherSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(source="user.get_full_name")
    email = serializers.EmailField(source="user.email")
    phone = serializers.CharField()
class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(); teacher_name = serializers.SerializerMethodField()
    teacher = TeacherSummarySerializer(source="assigned_teacher", read_only=True)
    parent = GuardianSummarySerializer(source="primary_guardian", read_only=True)
    has_profile_image = serializers.SerializerMethodField()
    class Meta:
        model = Student
        fields = (
            "id", "student_id", "first_name", "last_name", "full_name", "gender", "date_of_birth",
            "phone", "email", "address", "guardian_name", "guardian_phone", "guardian_relationship",
            "enrollment_date", "status", "assigned_teacher", "primary_guardian", "teacher_name", "teacher",
            "parent", "notes", "has_profile_image", "created_at", "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
        extra_kwargs = {
            "guardian_name": {"required": False},
            "guardian_phone": {"required": False},
            "guardian_relationship": {"required": False},
        }
    def get_full_name(self, obj) -> str: return f"{obj.first_name} {obj.last_name}"
    def get_teacher_name(self, obj): return obj.assigned_teacher.user.get_full_name() if obj.assigned_teacher_id else None
    def get_has_profile_image(self, obj) -> bool: return bool(obj.profile_image_pathname)
    def validate(self, attrs):
        teacher = attrs.get("assigned_teacher")
        guardian = attrs.get("primary_guardian")
        if teacher is not None and not teacher.is_active:
            raise serializers.ValidationError({"assigned_teacher": "An inactive teacher cannot be assigned."})
        if guardian is not None and not guardian.is_active:
            raise serializers.ValidationError({"primary_guardian": "An inactive guardian cannot be assigned."})
        return attrs
    def _sync_guardian_snapshot(self, validated_data):
        if "primary_guardian" not in validated_data:
            return validated_data
        guardian = validated_data["primary_guardian"]
        if guardian is not None:
            validated_data["guardian_name"] = guardian.name
            validated_data["guardian_phone"] = guardian.phone
        else:
            validated_data["guardian_name"] = ""
            validated_data["guardian_phone"] = ""
            validated_data["guardian_relationship"] = ""
        return validated_data
    def create(self, validated_data): return super().create(self._sync_guardian_snapshot(validated_data))
    def update(self, instance, validated_data): return super().update(instance, self._sync_guardian_snapshot(validated_data))
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_admin:
            fields["assigned_teacher"].read_only = True
        return fields
class GuardianSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(read_only=True)
    students = serializers.SerializerMethodField()
    class Meta: model = Guardian; fields = ("id", "name", "phone", "email", "address", "is_active", "student_count", "students", "created_at", "updated_at"); read_only_fields = ("created_at", "updated_at")
    def get_students(self, obj):
        students = obj.students.all()
        request = self.context.get("request")
        if request and not request.user.is_admin:
            students = students.filter(assigned_teacher__user=request.user)
        return [{"id": s.id, "student_id": s.student_id, "name": f"{s.first_name} {s.last_name}"} for s in students]
class NoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    class Meta: model = StudentNote; fields = "__all__"; read_only_fields = ("author", "created_at", "updated_at")
