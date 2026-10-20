from contextlib import AbstractContextManager

from django.db import transaction

from inventory.application.ports.unit_of_work import InventoryUnitOfWork


class DjangoInventoryUnitOfWork(InventoryUnitOfWork):
    def atomic(self) -> AbstractContextManager[None]:
        """Join the active connection transaction or create its outer boundary."""
        return transaction.atomic()
