from core.services.UploadService import UploadService


class DjangoUserAvatarStorage:
    """Storage adapter for user avatar cleanup."""

    def delete(self, path: str) -> None:
        UploadService.delete(path)
