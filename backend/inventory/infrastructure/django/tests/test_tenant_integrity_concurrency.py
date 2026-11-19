from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event
from time import monotonic
from uuid import uuid4

from django.db import IntegrityError, close_old_connections, connections, connection, transaction
from django.test import TransactionTestCase, skipUnlessDBFeature

from accounts.models import Business
from inventory.infrastructure.django.models import (
    InventoryOperation,
    InventoryOperationLine,
    InventoryReservation,
    InventoryReservationLine,
    InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.models import (
    CompoundMaterialComponent,
    Ingredient,
    Recipe,
    RecipeInput,
    RecipeOutput,
    Stock,
    Warehouse,
)


@skipUnlessDBFeature("has_select_for_update")
class InventoryTenantIntegrityConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Tenant-integrity locking requires PostgreSQL.")
        self.business = Business.objects.create(name="Tenant lock source")
        self.other_business = Business.objects.create(name="Tenant lock target")
        self.other_warehouse = Warehouse.objects.create(
            business=self.other_business, name="Other tenant warehouse"
        )
        self.source_warehouse = Warehouse.objects.create(
            business=self.business, name="Source warehouse"
        )
        self.destination_warehouse = Warehouse.objects.create(
            business=self.business, name="Existing destination warehouse"
        )
        self.new_destination_warehouse = Warehouse.objects.create(
            business=self.business, name="New destination warehouse"
        )
        self.ingredient = Ingredient.objects.create(
            business=self.business, name="Tenant lock ingredient", unit="kg"
        )
        self.operation = InventoryOperation.objects.create(
            business=self.business,
            operation_type=InventoryOperation.Type.TRANSFER,
            status=InventoryOperation.Status.DRAFT,
            warehouse=self.source_warehouse,
            destination_warehouse=self.destination_warehouse,
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
            Event().wait(0.01)
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
                        destination_warehouse_id=self.new_destination_warehouse.pk
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
                    Warehouse.objects.filter(pk=self.new_destination_warehouse.pk).update(
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
        self.new_destination_warehouse.refresh_from_db()
        self.assertEqual(self.new_destination_warehouse.business_id, self.business.pk)
        self.operation.refresh_from_db()
        self.assertEqual(
            self.operation.destination_warehouse_id, self.new_destination_warehouse.pk
        )

    def test_operation_line_reference_lock_serializes_ingredient_tenant_change(self):
        line_attached = Event()
        release_operation = Event()

        def attach_operation_line():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        "SET application_name = %s", ["eathub-ingredient-reference"]
                    )
                with transaction.atomic():
                    InventoryOperationLine.objects.create(
                        operation_id=self.operation.pk,
                        ingredient_id=self.ingredient.pk,
                        quantity=Decimal("1"),
                        unit="kg",
                    )
                    line_attached.set()
                    if not release_operation.wait(15):
                        raise TimeoutError("test coordinator did not release operation-line insert")
                return None
            except Exception as error:
                return error
            finally:
                connections.close_all()

        def change_ingredient_tenant():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        "SET application_name = %s", ["eathub-ingredient-tenant-change"]
                    )
                with transaction.atomic():
                    Ingredient.objects.filter(pk=self.ingredient.pk).update(
                        business_id=self.other_business.pk
                    )
                return None
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            attach_future = pool.submit(attach_operation_line)
            self.assertTrue(line_attached.wait(10))
            tenant_future = pool.submit(change_ingredient_tenant)
            try:
                self._wait_for_lock_wait("eathub-ingredient-tenant-change")
            finally:
                release_operation.set()
            attach_error = attach_future.result(timeout=20)
            tenant_error = tenant_future.result(timeout=20)

        self.assertIsNone(attach_error, msg=f"operation-line insert failed: {attach_error!r}")
        self.assertIsInstance(
            tenant_error,
            IntegrityError,
            msg=f"ingredient tenant change unexpectedly succeeded: {tenant_error!r}",
        )
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.business_id, self.business.pk)
        self.assertTrue(
            InventoryOperationLine.objects.filter(
                operation_id=self.operation.pk, ingredient_id=self.ingredient.pk
            ).exists()
        )

    def _assert_child_insert_serializes_parent_tenant_change(
        self, *, insert_stock, change_tenant, child_name, parent_name, assert_persisted
    ):
        stock_inserted = Event()
        release_stock = Event()

        def insert_child():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [child_name])
                with transaction.atomic():
                    insert_stock()
                    stock_inserted.set()
                    if not release_stock.wait(15):
                        raise TimeoutError("test coordinator did not release stock insert")
                return None
            except Exception as error:
                return error
            finally:
                connections.close_all()

        def update_parent():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET application_name = %s", [parent_name])
                with transaction.atomic():
                    change_tenant()
                return None
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            child_future = pool.submit(insert_child)
            self.assertTrue(stock_inserted.wait(10))
            parent_future = pool.submit(update_parent)
            try:
                self._wait_for_lock_wait(parent_name)
            finally:
                release_stock.set()
            child_error = child_future.result(timeout=20)
            parent_error = parent_future.result(timeout=20)

        self.assertIsNone(child_error, msg=f"stock insert failed: {child_error!r}")
        self.assertIsInstance(
            parent_error,
            IntegrityError,
            msg=f"parent tenant change unexpectedly succeeded: {parent_error!r}",
        )
        assert_persisted()

    def test_legacy_stock_reference_lock_serializes_ingredient_tenant_change(self):
        def assert_persisted():
            self.assertTrue(
                Stock.objects.filter(
                    warehouse=self.source_warehouse, ingredient=self.ingredient
                ).exists()
            )
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: Stock.objects.create(
                warehouse=self.source_warehouse, ingredient=self.ingredient
            ),
            change_tenant=lambda: Ingredient.objects.filter(pk=self.ingredient.pk).update(
                business_id=self.other_business.pk
            ),
            child_name="eathub-legacy-stock-insert",
            parent_name="eathub-legacy-stock-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_v1_stock_reference_lock_serializes_warehouse_tenant_change(self):
        def assert_persisted():
            self.assertTrue(
                InventoryV1Stock.objects.filter(
                    business=self.business,
                    warehouse=self.new_destination_warehouse,
                    ingredient=self.ingredient,
                ).exists()
            )
            self.new_destination_warehouse.refresh_from_db()
            self.assertEqual(self.new_destination_warehouse.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: InventoryV1Stock.objects.create(
                business=self.business,
                warehouse=self.new_destination_warehouse,
                ingredient=self.ingredient,
                unit="kg",
            ),
            change_tenant=lambda: Warehouse.objects.filter(
                pk=self.new_destination_warehouse.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-v1-stock-insert",
            parent_name="eathub-v1-stock-tenant-change",
            assert_persisted=assert_persisted,
        )


    def test_v1_stock_reference_lock_serializes_ingredient_tenant_change(self):
        def assert_persisted():
            self.assertTrue(
                InventoryV1Stock.objects.filter(
                    business=self.business,
                    warehouse=self.source_warehouse,
                    ingredient=self.ingredient,
                ).exists()
            )
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: InventoryV1Stock.objects.create(
                business=self.business,
                warehouse=self.source_warehouse,
                ingredient=self.ingredient,
                unit="kg",
            ),
            change_tenant=lambda: Ingredient.objects.filter(
                pk=self.ingredient.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-v1-stock-ingredient-insert",
            parent_name="eathub-v1-stock-ingredient-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_reservation_line_reference_lock_serializes_ingredient_tenant_change(self):
        reservation = InventoryReservation.objects.create(
            business=self.business,
            warehouse=self.source_warehouse,
            source_type="manual",
            source_id=None,
            reason="Tenant integrity concurrency test",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="f" * 64,
            created_by_id=1,
        )

        def assert_persisted():
            self.assertTrue(
                InventoryReservationLine.objects.filter(
                    reservation=reservation, ingredient=self.ingredient
                ).exists()
            )
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: InventoryReservationLine.objects.create(
                reservation=reservation,
                ingredient=self.ingredient,
                quantity=Decimal("1"),
                unit="kg",
            ),
            change_tenant=lambda: Ingredient.objects.filter(pk=self.ingredient.pk).update(
                business_id=self.other_business.pk
            ),
            child_name="eathub-reservation-line-insert",
            parent_name="eathub-reservation-line-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_compound_component_reference_lock_serializes_ingredient_level_change(self):
        compound = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock compound",
            unit="kg",
            preparation_level="semi_prepared",
        )

        def assert_persisted():
            self.assertTrue(
                CompoundMaterialComponent.objects.filter(
                    compound=compound, ingredient=self.ingredient
                ).exists()
            )
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.preparation_level, "raw")

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: CompoundMaterialComponent.objects.create(
                compound=compound,
                ingredient=self.ingredient,
                quantity=Decimal("1"),
                unit="kg",
            ),
            change_tenant=lambda: Ingredient.objects.filter(pk=self.ingredient.pk).update(
                preparation_level="semi_prepared"
            ),
            child_name="eathub-compound-component-insert",
            parent_name="eathub-compound-ingredient-level",
            assert_persisted=assert_persisted,
        )

    def test_recipe_input_reference_lock_serializes_recipe_tenant_change(self):
        recipe = Recipe.objects.create(
            business=self.business, name="Tenant lock recipe"
        )

        def assert_persisted():
            self.assertTrue(
                RecipeInput.objects.filter(
                    recipe=recipe, ingredient=self.ingredient
                ).exists()
            )
            recipe.refresh_from_db()
            self.assertEqual(recipe.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: RecipeInput.objects.create(
                recipe=recipe,
                ingredient=self.ingredient,
                quantity=Decimal("1"),
                unit="kg",
            ),
            change_tenant=lambda: Recipe.objects.filter(pk=recipe.pk).update(
                business_id=self.other_business.pk
            ),
            child_name="eathub-recipe-input-insert",
            parent_name="eathub-recipe-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_stock_movement_reference_lock_serializes_stock_tenant_change(self):
        stock = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.source_warehouse,
            ingredient=self.ingredient,
            unit="kg",
        )
        other_ingredient = Ingredient.objects.create(
            business=self.other_business,
            name="Tenant lock foreign ingredient",
            unit="kg",
        )
        stock_updated = Event()
        release_stock_update = Event()

        def update_stock_tenant():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        "SET application_name = %s", ["eathub-stock-tenant-update"]
                    )
                with transaction.atomic():
                    InventoryV1Stock.objects.filter(pk=stock.pk).update(
                        business=self.other_business,
                        warehouse=self.other_warehouse,
                        ingredient=other_ingredient,
                    )
                    stock_updated.set()
                    if not release_stock_update.wait(15):
                        raise TimeoutError("test coordinator did not release stock update")
                return None
            except Exception as error:
                return error
            finally:
                connections.close_all()

        def insert_movement():
            close_old_connections()
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        "SET application_name = %s", ["eathub-stock-movement-insert"]
                    )
                with transaction.atomic():
                    InventoryV1StockMovement.objects.create(
                        business=self.business,
                        stock=stock,
                        movement_type="receipt",
                        direction="in",
                        quantity=Decimal("1"),
                        unit="kg",
                        unit_cost=Decimal("1"),
                        balance_after=Decimal("1"),
                        average_cost_before=Decimal("0"),
                        source_type="tenant-integrity-concurrency-test",
                        source_document_id=1,
                        source_line_id=1,
                        operation_kind="receive",
                    )
                return None
            except Exception as error:
                return error
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            stock_future = pool.submit(update_stock_tenant)
            self.assertTrue(stock_updated.wait(10))
            movement_future = pool.submit(insert_movement)
            try:
                self._wait_for_lock_wait("eathub-stock-movement-insert")
            finally:
                release_stock_update.set()
            stock_error = stock_future.result(timeout=20)
            movement_error = movement_future.result(timeout=20)

        self.assertIsNone(stock_error, msg=f"stock tenant update failed: {stock_error!r}")
        self.assertIsInstance(
            movement_error,
            IntegrityError,
            msg=f"movement insert unexpectedly succeeded: {movement_error!r}",
        )
        stock.refresh_from_db()
        self.assertEqual(stock.business_id, self.other_business.pk)
        self.assertEqual(stock.warehouse_id, self.other_warehouse.pk)
        self.assertEqual(stock.ingredient_id, other_ingredient.pk)
        self.assertFalse(InventoryV1StockMovement.objects.filter(stock=stock).exists())


    def test_operation_line_reference_update_lock_serializes_ingredient_tenant_change(self):
        source_ingredient = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock operation line source",
            unit="kg",
        )
        line = InventoryOperationLine.objects.create(
            operation=self.operation,
            ingredient=source_ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )

        def assert_persisted():
            line.refresh_from_db()
            self.assertEqual(line.ingredient_id, self.ingredient.pk)
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: InventoryOperationLine.objects.filter(
                pk=line.pk
            ).update(ingredient_id=self.ingredient.pk),
            change_tenant=lambda: Ingredient.objects.filter(
                pk=self.ingredient.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-operation-line-reference-update",
            parent_name="eathub-operation-line-ingredient-tenant-change",
            assert_persisted=assert_persisted,
        )


    def test_reservation_line_reference_update_lock_serializes_ingredient_tenant_change(self):
        reservation = InventoryReservation.objects.create(
            business=self.business,
            warehouse=self.source_warehouse,
            source_type="manual",
            source_id=None,
            reason="Tenant integrity reservation-line update test",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="r" * 64,
            created_by_id=1,
        )
        source_ingredient = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock reservation line source",
            unit="kg",
        )
        line = InventoryReservationLine.objects.create(
            reservation=reservation,
            ingredient=source_ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )

        def assert_persisted():
            line.refresh_from_db()
            self.assertEqual(line.ingredient_id, self.ingredient.pk)
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: InventoryReservationLine.objects.filter(
                pk=line.pk
            ).update(ingredient_id=self.ingredient.pk),
            change_tenant=lambda: Ingredient.objects.filter(
                pk=self.ingredient.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-reservation-line-reference-update",
            parent_name="eathub-reservation-line-ingredient-tenant-change",
            assert_persisted=assert_persisted,
        )


    def test_compound_parent_reference_lock_serializes_preparation_level_change(self):
        compound = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock compound parent",
            unit="kg",
            preparation_level="semi_prepared",
        )

        def assert_persisted():
            self.assertTrue(
                CompoundMaterialComponent.objects.filter(
                    compound=compound, ingredient=self.ingredient
                ).exists()
            )
            compound.refresh_from_db()
            self.assertEqual(compound.preparation_level, "semi_prepared")

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: CompoundMaterialComponent.objects.create(
                compound=compound,
                ingredient=self.ingredient,
                quantity=Decimal("1"),
                unit="kg",
            ),
            change_tenant=lambda: Ingredient.objects.filter(pk=compound.pk).update(
                preparation_level="raw"
            ),
            child_name="eathub-compound-parent-insert",
            parent_name="eathub-compound-parent-level-change",
            assert_persisted=assert_persisted,
        )

    def test_recipe_output_reference_lock_serializes_recipe_tenant_change(self):
        recipe = Recipe.objects.create(
            business=self.business, name="Tenant lock output recipe"
        )

        def assert_persisted():
            self.assertTrue(
                RecipeOutput.objects.filter(
                    recipe=recipe, ingredient=self.ingredient
                ).exists()
            )
            recipe.refresh_from_db()
            self.assertEqual(recipe.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: RecipeOutput.objects.create(
                recipe=recipe,
                ingredient=self.ingredient,
                quantity=Decimal("1"),
                unit="kg",
            ),
            change_tenant=lambda: Recipe.objects.filter(pk=recipe.pk).update(
                business_id=self.other_business.pk
            ),
            child_name="eathub-recipe-output-insert",
            parent_name="eathub-recipe-output-parent-change",
            assert_persisted=assert_persisted,
        )

    def test_reservation_line_reference_lock_serializes_reservation_tenant_change(self):
        reservation = InventoryReservation.objects.create(
            business=self.business,
            warehouse=self.source_warehouse,
            source_type="manual",
            source_id=None,
            reason="Tenant integrity parent race test",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="a" * 64,
            created_by_id=1,
        )

        def assert_persisted():
            self.assertTrue(
                InventoryReservationLine.objects.filter(
                    reservation=reservation, ingredient=self.ingredient
                ).exists()
            )
            reservation.refresh_from_db()
            self.assertEqual(reservation.business_id, self.business.pk)
            self.assertEqual(reservation.warehouse_id, self.source_warehouse.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: InventoryReservationLine.objects.create(
                reservation=reservation,
                ingredient=self.ingredient,
                quantity=Decimal("1"),
                unit="kg",
            ),
            change_tenant=lambda: InventoryReservation.objects.filter(
                pk=reservation.pk
            ).update(
                business_id=self.other_business.pk,
                warehouse_id=self.other_warehouse.pk,
            ),
            child_name="eathub-reservation-parent-line-insert",
            parent_name="eathub-reservation-parent-tenant-change",
            assert_persisted=assert_persisted,
        )


    def test_operation_line_reference_lock_serializes_operation_tenant_change(self):
        def assert_persisted():
            self.assertTrue(
                InventoryOperationLine.objects.filter(
                    operation=self.operation, ingredient=self.ingredient
                ).exists()
            )
            self.operation.refresh_from_db()
            self.assertEqual(self.operation.business_id, self.business.pk)
            self.assertEqual(self.operation.warehouse_id, self.source_warehouse.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: InventoryOperationLine.objects.create(
                operation=self.operation,
                ingredient=self.ingredient,
                quantity=Decimal("1"),
                unit="kg",
            ),
            change_tenant=lambda: InventoryOperation.objects.filter(
                pk=self.operation.pk
            ).update(
                business_id=self.other_business.pk,
                warehouse_id=self.other_warehouse.pk,
                destination_warehouse_id=None,
            ),
            child_name="eathub-operation-parent-line-insert",
            parent_name="eathub-operation-parent-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_operation_line_parent_reference_update_lock_serializes_operation_tenant_change(self):
        target_operation = InventoryOperation.objects.create(
            business=self.business,
            operation_type=InventoryOperation.Type.TRANSFER,
            status=InventoryOperation.Status.DRAFT,
            warehouse=self.source_warehouse,
            destination_warehouse=self.destination_warehouse,
            created_by_id=1,
        )
        line = InventoryOperationLine.objects.create(
            operation=self.operation,
            ingredient=self.ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )

        def assert_persisted():
            line.refresh_from_db()
            self.assertEqual(line.operation_id, target_operation.pk)
            target_operation.refresh_from_db()
            self.assertEqual(target_operation.business_id, self.business.pk)
            self.assertEqual(target_operation.warehouse_id, self.source_warehouse.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: InventoryOperationLine.objects.filter(
                pk=line.pk
            ).update(operation_id=target_operation.pk),
            change_tenant=lambda: InventoryOperation.objects.filter(
                pk=target_operation.pk
            ).update(
                business_id=self.other_business.pk,
                warehouse_id=self.other_warehouse.pk,
                destination_warehouse_id=None,
            ),
            child_name="eathub-operation-line-parent-reference-update",
            parent_name="eathub-operation-line-parent-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_reservation_line_parent_reference_update_lock_serializes_reservation_tenant_change(self):
        source_reservation = InventoryReservation.objects.create(
            business=self.business,
            warehouse=self.source_warehouse,
            source_type="manual",
            source_id=None,
            reason="Tenant integrity source reservation",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="s" * 64,
            created_by_id=1,
        )
        target_reservation = InventoryReservation.objects.create(
            business=self.business,
            warehouse=self.source_warehouse,
            source_type="manual",
            source_id=None,
            reason="Tenant integrity target reservation",
            status=InventoryReservation.Status.ACTIVE,
            idempotency_key=uuid4(),
            payload_fingerprint="t" * 64,
            created_by_id=1,
        )
        line = InventoryReservationLine.objects.create(
            reservation=source_reservation,
            ingredient=self.ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )

        def assert_persisted():
            line.refresh_from_db()
            self.assertEqual(line.reservation_id, target_reservation.pk)
            target_reservation.refresh_from_db()
            self.assertEqual(target_reservation.business_id, self.business.pk)
            self.assertEqual(target_reservation.warehouse_id, self.source_warehouse.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: InventoryReservationLine.objects.filter(
                pk=line.pk
            ).update(reservation_id=target_reservation.pk),
            change_tenant=lambda: InventoryReservation.objects.filter(
                pk=target_reservation.pk
            ).update(
                business_id=self.other_business.pk,
                warehouse_id=self.other_warehouse.pk,
            ),
            child_name="eathub-reservation-line-parent-reference-update",
            parent_name="eathub-reservation-line-parent-tenant-change",
            assert_persisted=assert_persisted,
        )



    def test_recipe_input_reference_lock_serializes_ingredient_tenant_change(self):
        recipe = Recipe.objects.create(
            business=self.business, name="Tenant lock recipe input ingredient race"
        )

        def assert_persisted():
            self.assertTrue(
                RecipeInput.objects.filter(
                    recipe=recipe, ingredient=self.ingredient
                ).exists()
            )
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: RecipeInput.objects.create(
                recipe=recipe,
                ingredient=self.ingredient,
                quantity=Decimal("1"),
                unit="kg",
            ),
            change_tenant=lambda: Ingredient.objects.filter(
                pk=self.ingredient.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-recipe-input-ingredient-insert",
            parent_name="eathub-recipe-input-ingredient-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_recipe_output_reference_lock_serializes_ingredient_tenant_change(self):
        recipe = Recipe.objects.create(
            business=self.business, name="Tenant lock recipe output ingredient race"
        )

        def assert_persisted():
            self.assertTrue(
                RecipeOutput.objects.filter(
                    recipe=recipe, ingredient=self.ingredient
                ).exists()
            )
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: RecipeOutput.objects.create(
                recipe=recipe,
                ingredient=self.ingredient,
                quantity=Decimal("1"),
                unit="kg",
                is_primary=True,
            ),
            change_tenant=lambda: Ingredient.objects.filter(
                pk=self.ingredient.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-recipe-output-ingredient-insert",
            parent_name="eathub-recipe-output-ingredient-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_legacy_stock_reference_lock_serializes_warehouse_tenant_change(self):
        def assert_persisted():
            self.assertTrue(
                Stock.objects.filter(
                    warehouse=self.source_warehouse, ingredient=self.ingredient
                ).exists()
            )
            self.source_warehouse.refresh_from_db()
            self.assertEqual(self.source_warehouse.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: Stock.objects.create(
                warehouse=self.source_warehouse, ingredient=self.ingredient
            ),
            change_tenant=lambda: Warehouse.objects.filter(
                pk=self.source_warehouse.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-legacy-stock-warehouse-insert",
            parent_name="eathub-legacy-stock-warehouse-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_recipe_input_ingredient_reference_update_lock_serializes_tenant_change(self):
        recipe = Recipe.objects.create(
            business=self.business, name="Tenant lock recipe input update race"
        )
        source_ingredient = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock recipe input source",
            unit="kg",
        )
        recipe_input = RecipeInput.objects.create(
            recipe=recipe,
            ingredient=source_ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )

        def assert_persisted():
            recipe_input.refresh_from_db()
            self.assertEqual(recipe_input.ingredient_id, self.ingredient.pk)
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: RecipeInput.objects.filter(
                pk=recipe_input.pk
            ).update(ingredient_id=self.ingredient.pk),
            change_tenant=lambda: Ingredient.objects.filter(
                pk=self.ingredient.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-recipe-input-ingredient-reference-update",
            parent_name="eathub-recipe-input-ingredient-update-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_recipe_output_ingredient_reference_update_lock_serializes_tenant_change(self):
        recipe = Recipe.objects.create(
            business=self.business, name="Tenant lock recipe output update race"
        )
        source_ingredient = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock recipe output source",
            unit="kg",
        )
        recipe_output = RecipeOutput.objects.create(
            recipe=recipe,
            ingredient=source_ingredient,
            quantity=Decimal("1"),
            unit="kg",
            is_primary=True,
        )

        def assert_persisted():
            recipe_output.refresh_from_db()
            self.assertEqual(recipe_output.ingredient_id, self.ingredient.pk)
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: RecipeOutput.objects.filter(
                pk=recipe_output.pk
            ).update(ingredient_id=self.ingredient.pk),
            change_tenant=lambda: Ingredient.objects.filter(
                pk=self.ingredient.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-recipe-output-ingredient-reference-update",
            parent_name="eathub-recipe-output-ingredient-update-tenant-change",
            assert_persisted=assert_persisted,
        )


    def test_compound_component_ingredient_reference_update_lock_serializes_preparation_change(self):
        compound = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock compound ingredient update",
            unit="kg",
            preparation_level="semi_prepared",
        )
        source_ingredient = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock compound ingredient source",
            unit="kg",
            preparation_level="raw",
        )
        component = CompoundMaterialComponent.objects.create(
            compound=compound,
            ingredient=source_ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )

        def assert_persisted():
            component.refresh_from_db()
            self.assertEqual(component.ingredient_id, self.ingredient.pk)
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.preparation_level, "raw")

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: CompoundMaterialComponent.objects.filter(
                pk=component.pk
            ).update(ingredient_id=self.ingredient.pk),
            change_tenant=lambda: Ingredient.objects.filter(
                pk=self.ingredient.pk
            ).update(preparation_level="semi_prepared"),
            child_name="eathub-compound-ingredient-reference-update",
            parent_name="eathub-compound-ingredient-level-update",
            assert_persisted=assert_persisted,
        )

    def test_compound_component_parent_reference_update_lock_serializes_preparation_change(self):
        source_compound = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock compound parent source",
            unit="kg",
            preparation_level="semi_prepared",
        )
        target_compound = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock compound parent target",
            unit="kg",
            preparation_level="semi_prepared",
        )
        component = CompoundMaterialComponent.objects.create(
            compound=source_compound,
            ingredient=self.ingredient,
            quantity=Decimal("1"),
            unit="kg",
        )

        def assert_persisted():
            component.refresh_from_db()
            self.assertEqual(component.compound_id, target_compound.pk)
            target_compound.refresh_from_db()
            self.assertEqual(target_compound.preparation_level, "semi_prepared")

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: CompoundMaterialComponent.objects.filter(
                pk=component.pk
            ).update(compound_id=target_compound.pk),
            change_tenant=lambda: Ingredient.objects.filter(
                pk=target_compound.pk
            ).update(preparation_level="raw"),
            child_name="eathub-compound-parent-reference-update",
            parent_name="eathub-compound-parent-level-update",
            assert_persisted=assert_persisted,
        )

    def test_legacy_stock_warehouse_reference_update_lock_serializes_tenant_change(self):
        stock = Stock.objects.create(
            warehouse=self.source_warehouse,
            ingredient=self.ingredient,
        )

        def assert_persisted():
            stock.refresh_from_db()
            self.assertEqual(stock.warehouse_id, self.new_destination_warehouse.pk)
            self.new_destination_warehouse.refresh_from_db()
            self.assertEqual(self.new_destination_warehouse.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: Stock.objects.filter(pk=stock.pk).update(
                warehouse_id=self.new_destination_warehouse.pk
            ),
            change_tenant=lambda: Warehouse.objects.filter(
                pk=self.new_destination_warehouse.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-legacy-stock-warehouse-reference-update",
            parent_name="eathub-legacy-stock-warehouse-reference-tenant-change",
            assert_persisted=assert_persisted,
        )

    def test_v1_stock_ingredient_reference_update_lock_serializes_tenant_change(self):
        source_ingredient = Ingredient.objects.create(
            business=self.business,
            name="Tenant lock V1 stock ingredient source",
            unit="kg",
        )
        stock = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.source_warehouse,
            ingredient=source_ingredient,
            unit="kg",
        )

        def assert_persisted():
            stock.refresh_from_db()
            self.assertEqual(stock.ingredient_id, self.ingredient.pk)
            self.ingredient.refresh_from_db()
            self.assertEqual(self.ingredient.business_id, self.business.pk)

        self._assert_child_insert_serializes_parent_tenant_change(
            insert_stock=lambda: InventoryV1Stock.objects.filter(pk=stock.pk).update(
                ingredient_id=self.ingredient.pk
            ),
            change_tenant=lambda: Ingredient.objects.filter(
                pk=self.ingredient.pk
            ).update(business_id=self.other_business.pk),
            child_name="eathub-v1-stock-ingredient-reference-update",
            parent_name="eathub-v1-stock-ingredient-reference-tenant-change",
            assert_persisted=assert_persisted,
        )
