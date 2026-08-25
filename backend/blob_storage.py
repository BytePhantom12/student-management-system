import logging
import uuid
from dataclasses import dataclass
from io import BytesIO

from django.conf import settings
from PIL import Image, ImageOps, UnidentifiedImageError


logger = logging.getLogger(__name__)

ALLOWED_UPLOAD_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_PIXELS = 40_000_000


class ProfileImageValidationError(ValueError):
    pass


class BlobStorageConfigurationError(RuntimeError):
    pass


class BlobStorageUnavailableError(RuntimeError):
    pass


class PrivateBlobNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class NormalizedProfileImage:
    content: bytes
    content_type: str = "image/webp"
    extension: str = "webp"


@dataclass(frozen=True)
class PrivateBlob:
    content: bytes
    content_type: str
    etag: str
    status_code: int


def normalize_profile_image(uploaded_file) -> NormalizedProfileImage:
    max_bytes = settings.PROFILE_IMAGE_MAX_BYTES
    declared_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    if declared_type not in ALLOWED_UPLOAD_MIME_TYPES:
        raise ProfileImageValidationError("Use a JPEG, PNG, or WebP image.")

    raw = uploaded_file.read(max_bytes + 1)
    if not raw:
        raise ProfileImageValidationError("The selected image is empty.")
    if len(raw) > max_bytes:
        raise ProfileImageValidationError(
            f"Profile images must be {max_bytes // (1024 * 1024)} MB or smaller."
        )

    try:
        with Image.open(BytesIO(raw)) as candidate:
            detected_format = candidate.format
            candidate.verify()
        if detected_format not in ALLOWED_IMAGE_FORMATS:
            raise ProfileImageValidationError("Use a JPEG, PNG, or WebP image.")
        with Image.open(BytesIO(raw)) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise ProfileImageValidationError("The image dimensions are too large.")
            image = ImageOps.exif_transpose(source)
            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                rgba = image.convert("RGBA")
                background = Image.new("RGBA", rgba.size, "white")
                background.alpha_composite(rgba)
                image = background.convert("RGB")
            else:
                image = image.convert("RGB")
            image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="WEBP", quality=88, method=6)
    except ProfileImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ProfileImageValidationError("The selected file is not a valid image.") from exc

    return NormalizedProfileImage(output.getvalue())


def _token() -> str:
    token = settings.BLOB_READ_WRITE_TOKEN
    if not token:
        raise BlobStorageConfigurationError(
            "Private profile-image storage is not configured."
        )
    return token


def upload_profile_image(*, owner_type: str, owner_id: int, image: NormalizedProfileImage) -> str:
    from vercel.blob import BlobClient

    pathname = f"profile-images/{owner_type}/{owner_id}/{uuid.uuid4()}.{image.extension}"
    try:
        with BlobClient(token=_token()) as client:
            result = client.put(
                pathname,
                image.content,
                access="private",
                content_type=image.content_type,
                add_random_suffix=False,
                overwrite=False,
                cache_control_max_age=86400,
            )
        return result.pathname
    except BlobStorageConfigurationError:
        raise
    except Exception as exc:
        logger.warning("Private Blob upload failed (%s).", exc.__class__.__name__)
        raise BlobStorageUnavailableError("Profile-image storage is temporarily unavailable.") from exc


def fetch_private_blob(pathname: str, *, if_none_match: str | None = None) -> PrivateBlob:
    from vercel.blob import BlobClient, BlobNotFoundError

    try:
        with BlobClient(token=_token()) as client:
            result = client.get(
                pathname,
                access="private",
                timeout=settings.BLOB_REQUEST_TIMEOUT_SECONDS,
                if_none_match=if_none_match,
            )
        if result is None:
            raise PrivateBlobNotFoundError("Profile image not found.")
        return PrivateBlob(
            content=result.content,
            content_type=result.content_type or "application/octet-stream",
            etag=result.etag,
            status_code=result.status_code,
        )
    except (PrivateBlobNotFoundError, BlobNotFoundError) as exc:
        raise PrivateBlobNotFoundError("Profile image not found.") from exc
    except BlobStorageConfigurationError:
        raise
    except Exception as exc:
        logger.warning("Private Blob read failed (%s).", exc.__class__.__name__)
        raise BlobStorageUnavailableError("Profile-image storage is temporarily unavailable.") from exc


def delete_profile_image(pathname: str) -> None:
    from vercel.blob import BlobClient, BlobNotFoundError

    if not pathname:
        return
    try:
        with BlobClient(token=_token()) as client:
            client.delete(pathname)
    except BlobNotFoundError:
        return
    except BlobStorageConfigurationError:
        raise
    except Exception as exc:
        logger.warning("Private Blob cleanup failed (%s).", exc.__class__.__name__)
        raise BlobStorageUnavailableError("Profile-image cleanup failed.") from exc
