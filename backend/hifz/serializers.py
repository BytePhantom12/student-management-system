from rest_framework import serializers
from .models import HifzProgress
from .quran import SURAH_NAMES
class HifzSerializer(serializers.ModelSerializer):
    surah_name=serializers.SerializerMethodField(); student_name=serializers.CharField(source="student.__str__",read_only=True)
    class Meta: model=HifzProgress; fields="__all__"; read_only_fields=("created_at","updated_at")
    def get_surah_name(self,obj): return SURAH_NAMES[obj.surah-1]

