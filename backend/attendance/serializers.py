from rest_framework import serializers
from django.db import transaction
from .models import Attendance,AttendanceSession
class AttendanceSessionSerializer(serializers.ModelSerializer):
    teacher_name=serializers.CharField(source="teacher.user.get_full_name",read_only=True)
    record_count=serializers.IntegerField(read_only=True)
    class Meta: model=AttendanceSession; fields="__all__"; read_only_fields=("created_by","created_at","updated_at")
class AttendanceSerializer(serializers.ModelSerializer):
    student_name=serializers.CharField(source="student.__str__",read_only=True)
    recorded_by_name=serializers.CharField(source="recorded_by.get_full_name",read_only=True)
    class Meta: model=Attendance; fields="__all__"; read_only_fields=("recorded_by","created_at","updated_at")
    def validate(self,attrs):
        session=attrs.get("session",getattr(self.instance,"session",None))
        attendance_date=attrs.get("date",getattr(self.instance,"date",None))
        if session and attendance_date != session.date:
            raise serializers.ValidationError({"date":"Attendance date must match the session date."})
        return attrs
class BulkAttendanceRecordSerializer(AttendanceSerializer):
    class Meta(AttendanceSerializer.Meta):
        validators = []
class BulkAttendanceSerializer(serializers.Serializer):
    records=BulkAttendanceRecordSerializer(many=True)
    def validate_records(self, records):
        keys = [(record["student"].pk, record["date"]) for record in records]
        if len(keys) != len(set(keys)):
            raise serializers.ValidationError("Each student may appear only once per date.")
        return records
    @transaction.atomic
    def create(self,validated_data):
        request=self.context["request"]
        records=[]
        for values in validated_data["records"]:
            existing=Attendance.objects.filter(student=values["student"],date=values["date"]).first()
            if existing and not request.user.is_admin and existing.recorded_by_id != request.user.id:
                raise serializers.ValidationError("You may only update attendance you previously recorded.")
            record,_=Attendance.objects.update_or_create(student=values["student"],date=values["date"],defaults={**values,"recorded_by":request.user})
            records.append(record)
        return records
