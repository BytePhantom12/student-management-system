from rest_framework import serializers
from .models import HifzProgress
from .quran import SURAH_NAMES
class HifzSerializer(serializers.ModelSerializer):
    surah_name=serializers.SerializerMethodField(); student_name=serializers.CharField(source="student.__str__",read_only=True)
    class Meta: model=HifzProgress; fields="__all__"; read_only_fields=("created_at","updated_at")
    def get_surah_name(self,obj) -> str: return SURAH_NAMES[obj.surah-1]
    def validate(self, attrs):
        attrs = {**({
            "status": self.instance.status,
            "progress_percentage": self.instance.progress_percentage,
            "date_started": self.instance.date_started,
            "date_completed": self.instance.date_completed,
        } if self.instance else {}), **attrs}
        errors = {}
        if attrs.get("date_completed") and (
            not attrs.get("date_started") or attrs["date_completed"] < attrs["date_started"]
        ):
            errors["date_completed"] = "Completion must be on or after start."
        if attrs.get("status") == HifzProgress.Status.COMPLETED and attrs.get("progress_percentage") != 100:
            errors["progress_percentage"] = "Completed progress must be 100%."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
