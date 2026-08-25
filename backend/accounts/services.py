from django.db import transaction

from audit.models import AuditLog
from teachers.models import Teacher

from .models import User


def audit_user_action(*, actor, action, target, metadata=None):
    safe_metadata = {"target_username": target.username, **(metadata or {})}
    return AuditLog.objects.create(
        user=actor,
        action=action,
        object_type="User",
        object_id=str(target.pk),
        metadata=safe_metadata,
    )


def audit_teacher_action(*, actor, action, teacher, metadata=None):
    safe_metadata = {
        "target_user_id": teacher.user_id,
        "target_username": teacher.user.username,
        **(metadata or {}),
    }
    return AuditLog.objects.create(
        user=actor,
        action=action,
        object_type="Teacher",
        object_id=str(teacher.pk),
        metadata=safe_metadata,
    )


def ensure_teacher_profile(*, user, phone="", is_active=None, actor=None):
    teacher = Teacher.objects.filter(user=user).first()
    desired_active = user.is_active if is_active is None else is_active
    if teacher is None:
        teacher = Teacher(user=user, phone=phone, is_active=desired_active)
        if actor:
            teacher._skip_automatic_audit = True
        teacher.save()
        if actor:
            audit_teacher_action(actor=actor, action="teacher_profile_created", teacher=teacher)
        return teacher

    before = {"phone": teacher.phone, "is_active": teacher.is_active}
    changed = []
    if phone != "" and teacher.phone != phone:
        teacher.phone = phone
        changed.append("phone")
    if teacher.is_active != desired_active:
        teacher.is_active = desired_active
        changed.append("is_active")
    if changed:
        if actor:
            teacher._skip_automatic_audit = True
        teacher.save(update_fields=[*changed, "updated_at"])
        if actor:
            audit_teacher_action(
                actor=actor,
                action="teacher_profile_updated",
                teacher=teacher,
                metadata={
                    "before": before,
                    "after": {"phone": teacher.phone, "is_active": teacher.is_active},
                },
            )
    return teacher


@transaction.atomic
def create_teacher_account(*, username, password, first_name="", last_name="", email="", phone="", is_active=True, actor=None):
    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        email=email,
        role=User.Role.TEACHER,
        is_active=is_active,
    )
    teacher = ensure_teacher_profile(user=user, phone=phone, is_active=is_active, actor=actor)
    return user, teacher
