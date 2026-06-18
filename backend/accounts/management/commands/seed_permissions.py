from django.core.management.base import BaseCommand

from accounts.models import Permission
from core.enums import PermissionCode


class Command(BaseCommand):

    def handle(self, *args, **options):

        for permission in PermissionCode:

            Permission.objects.get_or_create(
                code=permission.value,
                defaults={
                    "name": permission.label
                }
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Permissions seeded successfully."
            )
        )