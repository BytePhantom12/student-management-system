from rest_framework import serializers
from .models import Attendance
class AttendanceSerializer(serializers.ModelSerializer):
    student_name=serializers.CharField(source="student.__str__",read_only=True)
    class Meta: model=Attendance; fields="__all__"; read_only_fields=("recorded_by","created_at","updated_at")
class BulkAttendanceSerializer(serializers.Serializer):
    records=AttendanceSerializer(many=True)
    def create(self,validated_data):
        request=self.context["request"]
        return [Attendance.objects.update_or_create(student=x["student"],date=x["date"],defaults={**x,"recorded_by":request.user})[0] for x in validated_data["records"]]

