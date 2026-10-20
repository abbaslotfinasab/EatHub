from contextlib import AbstractContextManager
from typing import Protocol


class InventoryUnitOfWork(Protocol):
    def atomic(self) -> AbstractContextManager[None]:
        """Provide an atomic boundary for reads, projection saves, and ledger append."""
