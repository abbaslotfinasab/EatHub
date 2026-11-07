from pathlib import Path
from uuid import uuid4

from django.core.files.storage import default_storage
from rest_framework.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


class UploadService:
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    ALLOWED_FORMATS = {
        "JPEG": ("jpg", "image/jpeg"),
        "PNG": ("png", "image/png"),
        "WEBP": ("webp", "image/webp"),
    }
    PURPOSE_DIRECTORIES = {
        "avatar": "uploads/avatars",
        "business_logo": "uploads/businesses/logos",
        "generic": "uploads",
    }

    @classmethod
    def validate_image(cls, file):
        if file.size > cls.MAX_IMAGE_SIZE:
            raise ValidationError({"file": "حجم تصویر نباید بیشتر از ۵ مگابایت باشد."})

        try:
            file.seek(0)
            image = Image.open(file)
            image.verify()
            image_format = image.format
        except (UnidentifiedImageError, OSError, ValueError):
            raise ValidationError({"file": "فایل انتخاب‌شده یک تصویر معتبر نیست."})
        finally:
            file.seek(0)

        if image_format not in cls.ALLOWED_FORMATS:
            raise ValidationError({"file": "فرمت تصویر باید JPG، PNG یا WEBP باشد."})

        return cls.ALLOWED_FORMATS[image_format]

    @classmethod
    def upload(cls, file, purpose="generic", user_id=None):
        directory = cls.PURPOSE_DIRECTORIES.get(purpose)
        if not directory:
            raise ValidationError({"purpose": "نوع آپلود معتبر نیست."})

        extension, content_type = cls.validate_image(file)
        filename = f"{uuid4().hex}.{extension}"
        owner_directory = f"{directory}/{user_id}" if user_id is not None else directory
        path = default_storage.save(f"{owner_directory}/{filename}", file)

        try:
            with default_storage.open(path, "rb") as stored_file:
                image = Image.open(stored_file)
                width, height = image.size
        except (OSError, UnidentifiedImageError):
            default_storage.delete(path)
            raise ValidationError({"file": "پردازش تصویر آپلودشده ناموفق بود."})

        return {
            "path": path,
            "url": default_storage.url(path),
            "filename": Path(path).name,
            "size": file.size,
            "content_type": content_type,
            "width": width,
            "height": height,
        }

    @staticmethod
    def delete(path):
        if path and default_storage.exists(path):
            default_storage.delete(path)
