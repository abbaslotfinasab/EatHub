from django.db import connection
from django.test import TransactionTestCase
from django.test.runner import DiscoverRunner


class LedgerSafeDiscoverRunner(DiscoverRunner):
    """Preserve ledger immutability while allowing Django test database cleanup."""

    _original_fixture_teardown = None

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        if connection.vendor != "postgresql":
            return

        if self.__class__._original_fixture_teardown is not None:
            return

        original = TransactionTestCase._fixture_teardown
        self.__class__._original_fixture_teardown = original

        def fixture_teardown(test_case):
            with connection.cursor() as cursor:
                cursor.execute(
                    "ALTER TABLE inventory_v1_stock_movement DISABLE TRIGGER USER"
                )
            try:
                return original(test_case)
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "ALTER TABLE inventory_v1_stock_movement ENABLE TRIGGER USER"
                    )

        TransactionTestCase._fixture_teardown = fixture_teardown

    def teardown_test_environment(self, **kwargs):
        original = self.__class__._original_fixture_teardown
        if original is not None:
            TransactionTestCase._fixture_teardown = original
            self.__class__._original_fixture_teardown = None
        super().teardown_test_environment(**kwargs)
