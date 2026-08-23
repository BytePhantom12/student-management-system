from rest_framework import serializers
from .models import Student, StudentNote
class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(); teacher_name = serializers.CharField(source="assigned_teacher.user.get_full_name", read_only=True)
    class Meta: model = Student; fields = "__all__"; read_only_fields = ("created_at", "updated_at")
    def get_full_name(self, obj): return f"{obj.first_name} {obj.last_name}"
class NoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    class Meta: model = StudentNote; fields = "__all__"; read_only_fields = ("author", "created_at", "updated_at")

