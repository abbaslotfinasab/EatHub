from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Business
import qrcode
from io import BytesIO
from django.core.files import File


@receiver(post_save, sender=Business)
def create_business_qr(sender, instance, created, **kwargs):
    if not created:
        return

    url = f"https://eathub.ir/products/{instance.slug}/menu"

    qr = qrcode.make(url)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    filename = f"{instance.slug}-qr.png"

    instance.qr_code.save(
        filename,
        File(buffer),
        save=True
    )