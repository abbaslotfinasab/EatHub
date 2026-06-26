from io import BytesIO

import qrcode
from django.core.files.base import ContentFile
from django.urls import reverse


class QRService:
    @staticmethod
    def generate_qr_for_business(business, request=None):
        path = reverse("products:public-menu", kwargs={"slug": business.slug})

        url = request.build_absolute_uri(path) if request else path

        qr = qrcode.make(url)

        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)

        filename = f"{business.slug}-qr.png"

        business.qr_code.save(
            filename,
            ContentFile(buffer.read()),
            save=True
        )