from uuid import uuid4
from pathlib import Path

from django.core.files.storage import default_storage


class UploadService:

    @staticmethod
    def upload(file):

        extension = Path(file.name).suffix

        filename = f"{uuid4().hex}{extension}"

        path = default_storage.save(
            f"uploads/{filename}",
            file,
        )

        return {
            "path": path,
            "url": default_storage.url(path),
            "filename": Path(path).name,
            "size": file.size,
            "content_type": file.content_type,
        }