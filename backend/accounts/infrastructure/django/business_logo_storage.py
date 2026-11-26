from core.services.UploadService import UploadService


class DjangoBusinessLogoStorage:
    """Storage adapter for business logo cleanup."""

    def delete(self, path: str) -> None:
        UploadService.delete(path)
