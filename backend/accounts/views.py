from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from drf_spectacular.utils import extend_schema, inline_serializer
from teachers.models import Teacher
from .models import User
from .permissions import IsSuperuser
from .serializers import (
    LogoutSerializer,
    SetPasswordSerializer,
    SuperuserUserCreateSerializer,
    SuperuserUserDetailSerializer,
    SuperuserUserListSerializer,
    SuperuserUserUpdateSerializer,
    UserRoleSerializer,
    UserSerializer,
    UserStaffStatusSerializer,
    UserSuperuserStatusSerializer,
)
from .services import audit_teacher_action, audit_user_action, ensure_teacher_profile
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(responses=UserSerializer)
    def get(self, request): return Response(UserSerializer(request.user).data)
class LogoutView(APIView):
    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        try: RefreshToken(request.data["refresh"]).blacklist()
        except (KeyError, TokenError): pass
        return Response(status=204)


USER_DASHBOARD_SCHEMA = inline_serializer("SuperuserAccountDashboard", {
    "total_users": serializers.IntegerField(),
    "active_users": serializers.IntegerField(),
    "inactive_users": serializers.IntegerField(),
    "teacher_role_accounts": serializers.IntegerField(),
    "application_admin_accounts": serializers.IntegerField(),
    "staff_accounts": serializers.IntegerField(),
    "superusers": serializers.IntegerField(),
    "active_teacher_profiles": serializers.IntegerField(),
    "recent_users": SuperuserUserListSerializer(many=True),
})


class SuperuserUserViewSet(CreateModelMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsSuperuser]
    filterset_fields = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering_fields = ("username", "first_name", "last_name", "date_joined", "last_login")
    ordering = ("username",)

    def get_queryset(self):
        return User.objects.select_related("teacher_profile").annotate(
            teacher_student_count=Count("teacher_profile__students", distinct=True)
        )

    def get_serializer_class(self):
        if self.action == "list": return SuperuserUserListSerializer
        if self.action == "create": return SuperuserUserCreateSerializer
        if self.action == "partial_update": return SuperuserUserUpdateSerializer
        if self.action == "role": return UserRoleSerializer
        if self.action == "staff": return UserStaffStatusSerializer
        if self.action == "superuser_status": return UserSuperuserStatusSerializer
        if self.action == "set_password": return SetPasswordSerializer
        return SuperuserUserDetailSerializer

    @extend_schema(request=SuperuserUserCreateSerializer, responses={201: SuperuserUserDetailSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output = SuperuserUserDetailSerializer(self.get_queryset().get(pk=user.pk), context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=SuperuserUserUpdateSerializer, responses=SuperuserUserDetailSerializer)
    @transaction.atomic
    def partial_update(self, request, pk=None):
        user = get_object_or_404(User.objects.select_for_update(), pk=pk)
        serializer = SuperuserUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        before = {field: getattr(user, field) for field in serializer.validated_data}
        serializer.save()
        after = {field: getattr(user, field) for field in serializer.validated_data}
        audit_user_action(actor=request.user, action="user_updated", target=user, metadata={"before": before, "after": after})
        return Response(SuperuserUserDetailSerializer(self.get_queryset().get(pk=user.pk)).data)

    def _lock_target(self, pk):
        return get_object_or_404(User.objects.select_for_update(), pk=pk)

    def _active_superuser_ids(self):
        return list(User.objects.select_for_update().filter(is_superuser=True, is_active=True).values_list("id", flat=True))

    @extend_schema(request=None, responses=SuperuserUserDetailSerializer)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def activate(self, request, pk=None):
        user = self._lock_target(pk)
        before_active = user.is_active
        user.is_active = True
        user.save(update_fields=["is_active"])
        teacher = Teacher.objects.filter(user=user).first()
        if teacher:
            desired = user.role == User.Role.TEACHER
            if teacher.is_active != desired:
                before = teacher.is_active
                teacher.is_active = desired
                teacher._skip_automatic_audit = True
                teacher.save(update_fields=["is_active", "updated_at"])
                audit_teacher_action(actor=request.user, action="teacher_profile_updated", teacher=teacher, metadata={"before": {"is_active": before}, "after": {"is_active": desired}})
        if not before_active:
            audit_user_action(actor=request.user, action="user_activated", target=user, metadata={"before": False, "after": True})
        return Response(SuperuserUserDetailSerializer(self.get_queryset().get(pk=user.pk)).data)

    @extend_schema(request=None, responses=SuperuserUserDetailSerializer)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def deactivate(self, request, pk=None):
        user = self._lock_target(pk)
        if user.pk == request.user.pk:
            raise serializers.ValidationError("You cannot deactivate your own account.")
        active_superusers = self._active_superuser_ids()
        if user.is_superuser and user.is_active and len(active_superusers) <= 1:
            raise serializers.ValidationError("The final active superuser cannot be deactivated.")
        before_active = user.is_active
        user.is_active = False
        user.save(update_fields=["is_active"])
        teacher = Teacher.objects.filter(user=user).first()
        if teacher and teacher.is_active:
            teacher.is_active = False
            teacher._skip_automatic_audit = True
            teacher.save(update_fields=["is_active", "updated_at"])
            audit_teacher_action(actor=request.user, action="teacher_profile_updated", teacher=teacher, metadata={"before": {"is_active": True}, "after": {"is_active": False}})
        if before_active:
            audit_user_action(actor=request.user, action="user_deactivated", target=user, metadata={"before": True, "after": False})
        return Response(SuperuserUserDetailSerializer(self.get_queryset().get(pk=user.pk)).data)

    @extend_schema(request=UserRoleSerializer, responses=SuperuserUserDetailSerializer)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def role(self, request, pk=None):
        user = self._lock_target(pk)
        serializer = UserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_role = user.role
        new_role = serializer.validated_data["role"]
        user.role = new_role
        user.save(update_fields=["role"])
        if new_role == User.Role.TEACHER:
            ensure_teacher_profile(user=user, phone=serializer.validated_data.get("teacher_phone", ""), is_active=user.is_active, actor=request.user)
        else:
            teacher = Teacher.objects.filter(user=user).first()
            if teacher and teacher.is_active:
                teacher.is_active = False
                teacher._skip_automatic_audit = True
                teacher.save(update_fields=["is_active", "updated_at"])
                audit_teacher_action(actor=request.user, action="teacher_profile_updated", teacher=teacher, metadata={"before": {"is_active": True}, "after": {"is_active": False}})
        if old_role != new_role:
            audit_user_action(actor=request.user, action="user_role_changed", target=user, metadata={"before": old_role, "after": new_role})
        return Response(SuperuserUserDetailSerializer(self.get_queryset().get(pk=user.pk)).data)

    @extend_schema(request=UserStaffStatusSerializer, responses=SuperuserUserDetailSerializer)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def staff(self, request, pk=None):
        user = self._lock_target(pk)
        serializer = UserStaffStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        before = user.is_staff
        user.is_staff = serializer.validated_data["is_staff"]
        user.save(update_fields=["is_staff"])
        if before != user.is_staff:
            audit_user_action(actor=request.user, action="user_staff_status_changed", target=user, metadata={"before": before, "after": user.is_staff})
        return Response(SuperuserUserDetailSerializer(self.get_queryset().get(pk=user.pk)).data)

    @extend_schema(request=UserSuperuserStatusSerializer, responses=SuperuserUserDetailSerializer)
    @action(detail=True, methods=["post"], url_path="superuser")
    @transaction.atomic
    def superuser_status(self, request, pk=None):
        user = self._lock_target(pk)
        serializer = UserSuperuserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        desired = serializer.validated_data["is_superuser"]
        if user.pk == request.user.pk and not desired:
            raise serializers.ValidationError("You cannot remove your own superuser status.")
        if user.is_superuser and not desired and user.is_active and len(self._active_superuser_ids()) <= 1:
            raise serializers.ValidationError("The final active superuser cannot be demoted.")
        before = user.is_superuser
        user.is_superuser = desired
        user.save(update_fields=["is_superuser"])
        if before != desired:
            audit_user_action(actor=request.user, action="user_superuser_status_changed", target=user, metadata={"before": before, "after": desired})
        return Response(SuperuserUserDetailSerializer(self.get_queryset().get(pk=user.pk)).data)

    @extend_schema(request=SetPasswordSerializer, responses={200: inline_serializer("PasswordSetResponse", {"detail": serializers.CharField()})})
    @action(detail=True, methods=["post"], url_path="set-password")
    @transaction.atomic
    def set_password(self, request, pk=None):
        user = self._lock_target(pk)
        serializer = SetPasswordSerializer(data=request.data, context={"target_user": user})
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        audit_user_action(actor=request.user, action="user_password_changed", target=user)
        return Response({"detail": "Password updated successfully."})

    @extend_schema(responses=USER_DASHBOARD_SCHEMA)
    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        metrics = User.objects.aggregate(
            total_users=Count("id"),
            active_users=Count("id", filter=Q(is_active=True)),
            inactive_users=Count("id", filter=Q(is_active=False)),
            teacher_role_accounts=Count("id", filter=Q(role=User.Role.TEACHER)),
            application_admin_accounts=Count("id", filter=Q(role=User.Role.ADMIN)),
            staff_accounts=Count("id", filter=Q(is_staff=True)),
            superusers=Count("id", filter=Q(is_superuser=True)),
        )
        recent = self.get_queryset().order_by("-date_joined")[:5]
        return Response({
            **metrics,
            "active_teacher_profiles": Teacher.objects.filter(is_active=True).count(),
            "recent_users": SuperuserUserListSerializer(recent, many=True).data,
        })
