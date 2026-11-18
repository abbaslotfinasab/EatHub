from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic

from django.db import IntegrityError, close_old_connections, connections, connection, transaction
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business
from inventory.infrastructure.django.models import InventoryOperation
from inventory.models import Warehouse


@skipUnlessDBFeature("has_select_for_update")
class InventoryTenantIntegrityConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Tenant-integrity locking requires PostgreSQL.")
        self.business = Business.objects.create(name="Tenant lock source")
        self.other_business = Business.objects.create(name="Tenant lock target")
        self.source_warehouse = Warehouse.objects.create(
            business=self.business, name="Source warehouse"
        )
        self.destination_warehouse = Warehouse.objects.create(
            business=self.business, name="Destination warehouse"
        )
        self.operation = InventoryOperation.objects.create(
            business=self.business,
            operation_type=InventoryOperation.Type.TRANSFER,
            status=InventoryOperation.Status.DRAFT,
            warehouse=self.source_warehouse,
            created_by_id=1,
        )

    def _wait_for_lock_wait(self, application_name):
        deadline = monotonic() + 15
        while monotonic() < deadline:
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    """SELECT wait_event_type, cardinality(pg_blocking_pids(pid))
                       FROM pg_stat_activity WHERE application_name = %s""",
                    [application_name],
                )
                row = cursor.fetchone()
            if row and row[0] == "Lock" and row[1] > 0:
                return
        self.fail(f"PostgreSQL did not report a lock wait for {application_name}.")

    def test_destination_reference_lock_serializes_warehouse_tenant_change(self):
        destination_attached = Event()
        release_operation = Event()

        def attach_destination():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        "SET application_name = %s", ["eathub-destination-reference"]
                    )
                with transaction.atomic():
                    InventoryOperation.objects.filter(pk=self.operation.pk).update(
                        destination_warehouse_id=self.destination_warehouse.pk
                    )
                    destination_attached.set()
                    if not release_operation.wait(15):
                        raise TimeoutError("test coordinator did not release operation update")
                return None
            except Exception as error:
                return error
            finally:
                connections.close_all()

        def change_destination_tenant():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        "SET application_name = %s", ["eathub-destination-tenant-change"]
                    )
                with transaction.atomic():
                    Warehouse.objects.filter(pk=self.destination_warehouse.pk).update(
                        business_id=self.other_business.pk
                    )
                return None
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            attach_future = pool.submit(attach_destination)
            self.assertTrue(destination_attached.wait(10))
            tenant_future = pool.submit(change_destination_tenant)
            try:
                self._wait_for_lock_wait("eathub-destination-tenant-change")
            finally:
                release_operation.set()
            attach_error = attach_future.result(timeout=20)
            tenant_error = tenant_future.result(timeout=20)

        self.assertIsNone(attach_error, msg=f"destination reference update failed: {attach_error!r}")
        self.assertIsInstance(
            tenant_error,
            IntegrityError,
            msg=f"warehouse tenant change unexpectedly succeeded: {tenant_error!r}",
        )
        self.destination_warehouse.refresh_from_db()
        self.assertEqual(self.destination_warehouse.business_id, self.business.pk)
        self.operation.refresh_from_db()
        self.assertEqual(
            self.operation.destination_warehouse_id, self.destination_warehouse.pk
        )
