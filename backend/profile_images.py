import logging
from io import BytesIO

from django.db import transaction
from django.http import FileResponse, HttpResponse
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework import serializers

from audit.models import AuditLog
from blob_storage import (
    BlobStorageConfigurationError,
    BlobStorageUnavailableError,
    PrivateBlobNotFoundError,
    ProfileImageValidationError,
    delete_profile_image,
    fetch_private_blob,
    normalize_profile_image,
    upload_profile_image,
)


logger = logging.getLogger(__name__)


class ProfileImageStorageUnavailable(APIException):
    status_code = 503
    default_detail = "Profile-image storage is temporarily unavailable."
    default_code = "profile_image_storage_unavailable"


class ProfileImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(help_text="JPEG, PNG, or WebP profile image, maximum 3 MB.")


def uploaded_profile_image(request):
    image = request.FILES.get("image")
    if image is None:
        raise ValidationError({"image": "Select an image to upload."})
    return image


def protected_profile_image_response(*, instance, request):
    if not instance.profile_image_pathname:
        raise NotFound("No profile image is available.")
    try:
        blob = fetch_private_blob(
            instance.profile_image_pathname,
            if_none_match=request.headers.get("If-None-Match"),
        )
    except PrivateBlobNotFoundError as exc:
        raise NotFound("The profile image could not be found.") from exc
    except (BlobStorageConfigurationError, BlobStorageUnavailableError) as exc:
        raise ProfileImageStorageUnavailable() from exc

    if blob.status_code == 304:
        response = HttpResponse(status=304)
    else:
        response = FileResponse(BytesIO(blob.content), content_type=blob.content_type)
        response["Content-Length"] = str(len(blob.content))
    response["Cache-Control"] = "private, no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    if blob.etag:
        response["ETag"] = blob.etag
    return response


def replace_profile_image(*, instance, uploaded_file, actor, owner_type: str, action: str):
    try:
        normalized = normalize_profile_image(uploaded_file)
        new_pathname = upload_profile_image(
            owner_type=owner_type,
            owner_id=instance.pk,
            image=normalized,
        )
    except ProfileImageValidationError as exc:
        raise ValidationError({"image": str(exc)}) from exc
    except (BlobStorageConfigurationError, BlobStorageUnavailableError) as exc:
        raise ProfileImageStorageUnavailable() from exc
    old_pathname = instance.profile_image_pathname
    try:
        with transaction.atomic():
            instance.profile_image_pathname = new_pathname
            instance._skip_automatic_audit = True
            instance.save(update_fields=["profile_image_pathname", "updated_at"])
            AuditLog.objects.create(
                user=actor,
                action=action,
                object_type=instance.__class__.__name__,
                object_id=str(instance.pk),
                metadata={"before": bool(old_pathname), "after": True},
            )
    except Exception:
        try:
            delete_profile_image(new_pathname)
        except Exception as cleanup_error:
            logger.warning("New profile-image cleanup failed (%s).", cleanup_error.__class__.__name__)
        raise

    if old_pathname:
        try:
            delete_profile_image(old_pathname)
        except Exception as cleanup_error:
            logger.warning("Replaced profile-image cleanup failed (%s).", cleanup_error.__class__.__name__)
    return instance


def remove_profile_image(*, instance, actor, action: str) -> bool:
    old_pathname = instance.profile_image_pathname
    if not old_pathname:
        return False
    with transaction.atomic():
        instance.profile_image_pathname = None
        instance._skip_automatic_audit = True
        instance.save(update_fields=["profile_image_pathname", "updated_at"])
        AuditLog.objects.create(
            user=actor,
            action=action,
            object_type=instance.__class__.__name__,
            object_id=str(instance.pk),
            metadata={"before": True, "after": False},
        )
    try:
        delete_profile_image(old_pathname)
    except Exception as cleanup_error:
        logger.warning("Removed profile-image cleanup failed (%s).", cleanup_error.__class__.__name__)
    return True
