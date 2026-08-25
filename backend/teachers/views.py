from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from common import IsAdmin
from profile_images import ProfileImageUploadSerializer, protected_profile_image_response, remove_profile_image, replace_profile_image, uploaded_profile_image
from .models import Teacher
from .serializers import TeacherSelfSerializer, TeacherSerializer
class TeacherViewSet(ModelViewSet):
    permission_classes = [IsAdmin]; serializer_class = TeacherSerializer; filterset_fields = ("is_active",); search_fields = ("user__first_name", "user__last_name", "user__email", "phone")
    def get_queryset(self): return Teacher.objects.select_related("user").prefetch_related("students").annotate(student_count=Count("students")).order_by("user__first_name")
    def get_permissions(self):
        if self.action in ("me", "me_profile_image"):
            return [IsAuthenticated()]
        return super().get_permissions()
    def _self_teacher(self):
        try:
            return Teacher.objects.select_related("user").get(user=self.request.user)
        except Teacher.DoesNotExist as exc:
            raise NotFound("A teacher profile is not available for this account.") from exc
    @extend_schema(methods=["GET"], responses={(200, "image/webp"): OpenApiTypes.BINARY})
    @extend_schema(methods=["POST"], request=ProfileImageUploadSerializer, responses=TeacherSerializer)
    @extend_schema(methods=["DELETE"], responses={204: None})
    @action(detail=True, methods=["get", "post", "delete"], url_path="profile-image")
    def profile_image(self, request, pk=None):
        teacher = self.get_object()
        if request.method == "GET":
            return protected_profile_image_response(instance=teacher, request=request)
        if request.method == "DELETE":
            remove_profile_image(instance=teacher, actor=request.user, action="teacher_profile_image_removed")
            return Response(status=204)
        replace_profile_image(
            instance=teacher,
            uploaded_file=uploaded_profile_image(request),
            actor=request.user,
            owner_type="teachers",
            action="teacher_profile_image_updated",
        )
        return Response(self.get_serializer(teacher).data)
    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        return Response(TeacherSelfSerializer(self._self_teacher()).data)
    @extend_schema(methods=["GET"], responses={(200, "image/webp"): OpenApiTypes.BINARY})
    @extend_schema(methods=["POST"], request=ProfileImageUploadSerializer, responses=TeacherSelfSerializer)
    @extend_schema(methods=["DELETE"], responses={204: None})
    @action(detail=False, methods=["get", "post", "delete"], url_path="me/profile-image")
    def me_profile_image(self, request):
        teacher = self._self_teacher()
        if request.method == "GET":
            return protected_profile_image_response(instance=teacher, request=request)
        if request.method == "DELETE":
            remove_profile_image(instance=teacher, actor=request.user, action="teacher_profile_image_removed")
            return Response(status=204)
        replace_profile_image(
            instance=teacher,
            uploaded_file=uploaded_profile_image(request),
            actor=request.user,
            owner_type="teachers",
            action="teacher_profile_image_updated",
        )
        return Response(TeacherSelfSerializer(teacher).data)
