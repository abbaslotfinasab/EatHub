from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, local
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
from django.db.models import Sum
from django.http import Http404
from django.test import TestCase, TransactionTestCase
from rest_framework.exceptions import ValidationError as APIValidationError
from unittest import skipUnless

from accounts.models import Business, User
from core.enums import PermissionCode
from inventory.infrastructure.django.models import (
    InventoryReservation,
    InventoryReservationLine,
    InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import OperationConflict, ResourceNotFound
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.domain.entities.reservation import MANUAL_RESERVATION_SOURCE
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from composition.order_reservation_source import DjangoOrderReservationSource
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.models import Ingredient, Recipe, RecipeInput, RecipeOutput, Warehouse
from products.models import (
    Customer,
    CustomerAccount,
    CustomerTransaction,
    Menu,
    MenuItem,
    Order,
    OrderInventoryConsumption,
    OrderItemIngredientRequirement,
    OrderItem,
    OrderRefund,
    OrderStatusHistory,
)
from products.services.order_inventory_service import OrderInventoryService
from products.services.order_service import OrderService
from products.views import OrderActualConsumptionAPIView


class OrderInventoryLifecycleTests(TestCase):
    """Order inventory behavior uses real ORM/ledger paths; run only on an isolated test DB."""

    def setUp(self):
        self.business = Business.objects.create(name="Order Inventory Business")
        self.actor = User.objects.create_user(
            email="order-inventory@example.test", password="test-password", name="Operator"
        )
        self.warehouse = Warehouse.objects.create(
            business=self.business, name="Main", is_active=True, is_default=True
        )
        self.flour = Ingredient.objects.create(
            business=self.business, name="Flour", unit="kg", preparation_level="raw"
        )
        self.dish = Ingredient.objects.create(
            business=self.business, name="Dish", unit="pc", preparation_level="raw"
        )
        self.stock = InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.warehouse, ingredient=self.flour,
            unit="kg", quantity=Decimal("10"), average_cost=Decimal("2"),
        )
        self.recipe = Recipe.objects.create(
            business=self.business, name="Dish recipe", type=Recipe.Type.PREPARATION
        )
        self.input_line = RecipeInput.objects.create(
            recipe=self.recipe, ingredient=self.flour, quantity=Decimal("1500"), unit="g"
        )
        RecipeOutput.objects.create(
            recipe=self.recipe, ingredient=self.dish, quantity=Decimal("1"), unit="pc", is_primary=True
        )
        self.menu = Menu.objects.create(business=self.business, name="Menu", category="Test")
        self.menu_item = MenuItem.objects.create(
            business=self.business, menu=self.menu, name="Dish", price=Decimal("10"), recipe=self.recipe
        )
        self.order = Order.objects.create(
            business=self.business, order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CASH, total_amount=Decimal("20"),
        )
        self.order_item = OrderItem.objects.create(
            order=self.order, menu_item=self.menu_item, menu_item_name=self.menu_item.name,
            quantity=2, unit_price=Decimal("10"), total_price=Decimal("20"),
        )

    def confirm(self):
        return OrderService.update_status(
            business=self.business, order_id=self.order.pk,
            status=Order.Status.CONFIRMED, user=self.actor,
        )

    def start_preparation(self):
        OrderService.update_status(
            business=self.business, order_id=self.order.pk,
            status=Order.Status.PREPARING, user=self.actor,
        )

    def requirement(self):
        return self.order_item.inventory_recipe_snapshot.requirements.get()

    def test_inventory_application_prepares_active_order_reservation_scope(self):
        self.confirm()
        self.start_preparation()
        use_case = ManageReservations(
            DjangoReservationRepository(), DjangoInventoryUnitOfWork(), DjangoOrderReservationSource()
        )

        prepared = use_case.prepare_order_consumption(
            InventoryExecutionContext(self.business.pk, self.actor.pk),
            self.order.pk,
        )

        self.assertEqual(prepared.business_id, self.business.pk)
        self.assertEqual(prepared.source_type, "order")
        self.assertEqual(prepared.source_id, self.order.pk)
        self.assertEqual(prepared.warehouse_id, self.warehouse.pk)
        self.assertEqual(len(prepared.lines), 1)
        self.assertEqual(prepared.lines[0].ingredient_id, self.flour.pk)
        self.assertEqual(prepared.lines[0].quantity, Decimal("3.000000000000"))
        self.assertEqual(prepared.lines[0].unit.value, "kg")

    def test_inventory_application_rejects_order_reservation_from_another_business(self):
        self.confirm()
        other_business = Business.objects.create(name="Foreign Reservation Business")
        use_case = ManageReservations(
            DjangoReservationRepository(), DjangoInventoryUnitOfWork(), DjangoOrderReservationSource()
        )

        with self.assertRaises(ResourceNotFound):
            use_case.prepare_order_consumption(
                InventoryExecutionContext(other_business.pk, self.actor.pk),
                self.order.pk,
            )

    def test_inventory_application_validates_confirmation_retry_reservation(self):
        self.confirm()
        use_case = ManageReservations(
            DjangoReservationRepository(), DjangoInventoryUnitOfWork(), DjangoOrderReservationSource()
        )

        prepared = use_case.validate_order_reservation_for_confirmation(
            InventoryExecutionContext(self.business.pk, self.actor.pk),
            self.order.pk,
        )

        self.assertEqual(prepared.business_id, self.business.pk)
        self.assertEqual(prepared.source_id, self.order.pk)
        self.assertEqual(prepared.lines[0].quantity, Decimal("3.000000000000"))

    def test_inventory_application_rejects_mismatched_confirmation_retry_reservation(self):
        self.confirm()
        InventoryReservation.objects.get(source_id=self.order.pk).lines.update(
            quantity=Decimal("2")
        )
        use_case = ManageReservations(
            DjangoReservationRepository(), DjangoInventoryUnitOfWork(), DjangoOrderReservationSource()
        )

        with self.assertRaises(OperationConflict):
            use_case.validate_order_reservation_for_confirmation(
                InventoryExecutionContext(self.business.pk, self.actor.pk),
                self.order.pk,
            )

    def test_confirmation_scales_and_converts_then_reserves_without_physical_deduction(self):
        self.confirm()

        self.stock.refresh_from_db()
        requirement = self.requirement()
        reservation = InventoryReservation.objects.get(source_type="order", source_id=self.order.pk)
        line = reservation.lines.get(ingredient=self.flour)
        self.assertEqual(requirement.standard_quantity, Decimal("3.000000000000"))
        self.assertEqual(requirement.unit, "kg")
        self.assertEqual(line.quantity, Decimal("3.000000000000"))
        self.assertEqual(self.stock.quantity, Decimal("10"))
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)

    def test_recipe_edit_does_not_change_confirmed_requirement_snapshot(self):
        self.confirm()
        requirement = self.requirement()
        self.input_line.quantity = Decimal("9000")
        self.input_line.save(update_fields=("quantity",))

        requirement.refresh_from_db()
        self.assertEqual(requirement.standard_quantity, Decimal("3.000000000000"))

    def test_insufficient_stock_rolls_back_order_snapshot_and_all_reservation_lines(self):
        self.stock.quantity = Decimal("2")
        self.stock.save(update_fields=("quantity",))

        with self.assertRaises(APIValidationError):
            self.confirm()

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertFalse(self.order.recipe_snapshots.exists())
        self.assertFalse(InventoryReservation.objects.filter(source_id=self.order.pk).exists())

    def test_order_without_a_usable_recipe_is_not_confirmed_as_zero_requirements(self):
        self.menu_item.recipe = None
        self.menu_item.save(update_fields=("recipe",))

        with self.assertRaises(APIValidationError):
            self.confirm()

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertFalse(self.order.recipe_snapshots.exists())
        self.assertFalse(InventoryReservation.objects.filter(source_id=self.order.pk).exists())


    def test_one_insufficient_line_rejects_entire_multi_ingredient_reservation(self):
        oil = Ingredient.objects.create(
            business=self.business, name="Oil", unit="ml", preparation_level="raw"
        )
        RecipeInput.objects.create(recipe=self.recipe, ingredient=oil, quantity=Decimal("100"), unit="ml")
        InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.warehouse, ingredient=oil,
            unit="ml", quantity=Decimal("0"), average_cost=Decimal("0"),
        )

        with self.assertRaises(APIValidationError):
            self.confirm()

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertFalse(self.order.recipe_snapshots.exists())
        self.assertFalse(InventoryReservation.objects.filter(source_id=self.order.pk).exists())

    def test_confirmation_retry_is_idempotent(self):
        self.confirm()
        first_snapshot = self.order_item.inventory_recipe_snapshot.pk
        first_reservation = InventoryReservation.objects.get(source_id=self.order.pk).pk
        self.confirm()

        self.assertEqual(self.order_item.inventory_recipe_snapshot.pk, first_snapshot)
        self.assertEqual(InventoryReservation.objects.filter(source_id=self.order.pk).count(), 1)
        self.assertEqual(InventoryReservation.objects.get(source_id=self.order.pk).pk, first_reservation)

    def test_confirmation_retry_rejects_snapshots_without_active_reservation(self):
        self.confirm()
        OrderInventoryService.release_remaining(
            order=self.order,
            actor_id=self.actor.pk,
            reason="Simulate a missing reservation during confirmation retry",
        )

        with self.assertRaises(APIValidationError):
            self.confirm()

        self.assertFalse(InventoryReservation.objects.filter(
            source_type="order",
            source_id=self.order.pk,
            status=InventoryReservation.Status.ACTIVE,
        ).exists())

    def test_confirmation_retry_rejects_reservation_that_differs_from_remaining_requirements(self):
        self.confirm()
        reservation = InventoryReservation.objects.get(
            source_type="order", source_id=self.order.pk,
            status=InventoryReservation.Status.ACTIVE,
        )
        reservation.lines.update(quantity=Decimal("2"))

        with self.assertRaises(APIValidationError):
            self.confirm()

        self.assertEqual(
            InventoryReservation.objects.filter(
                source_type="order",
                source_id=self.order.pk,
                status=InventoryReservation.Status.ACTIVE,
            ).count(),
            1,
        )

    def test_actual_consumption_posts_issue_once_and_replaces_reservation_with_remainder(self):
        self.confirm()
        self.start_preparation()
        requirement = self.requirement()
        key = uuid4()
        payload = [{"requirement_id": requirement.pk, "quantity": "2", "unit": "kg"}]

        lock_events = []
        original_lock_scope = DjangoReservationRepository.lock_scope
        original_lock_stock = DjangoReservationRepository.lock_stock_positions
        original_release = DjangoReservationRepository.release

        def tracked_lock_scope(repository, *args, **kwargs):
            lock_events.append("scope")
            return original_lock_scope(repository, *args, **kwargs)

        def tracked_lock_stock(repository, *args, **kwargs):
            lock_events.append("stock")
            return original_lock_stock(repository, *args, **kwargs)

        def tracked_release(repository, *args, **kwargs):
            lock_events.append("release")
            return original_release(repository, *args, **kwargs)

        with patch.object(DjangoReservationRepository, "lock_scope", tracked_lock_scope), \
             patch.object(DjangoReservationRepository, "lock_stock_positions", tracked_lock_stock), \
             patch.object(DjangoReservationRepository, "release", tracked_release):
            first = OrderInventoryService.record_consumption(
                business_id=self.business.pk, order_id=self.order.pk, actor_id=self.actor.pk,
                idempotency_key=key, lines=payload,
            )

        self.assertLess(lock_events.index("scope"), lock_events.index("stock"))
        self.assertLess(lock_events.index("stock"), lock_events.index("release"))

        retry = OrderInventoryService.record_consumption(
            business_id=self.business.pk, order_id=self.order.pk, actor_id=self.actor.pk,
            idempotency_key=key, lines=payload,
        )
        with self.assertRaises(OperationConflict):
            OrderInventoryService.record_consumption(
                business_id=self.business.pk, order_id=self.order.pk, actor_id=self.actor.pk,
                idempotency_key=key,
                lines=[{"requirement_id": requirement.pk, "quantity": "1.5", "unit": "kg"}],
            )

        self.stock.refresh_from_db()
        self.assertEqual(first.pk, retry.pk)
        self.assertEqual(self.stock.quantity, Decimal("8.000000000000"))
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="issue").count(), 1)
        self.assertEqual(first.lines.get().inventory_movement_id, InventoryV1StockMovement.objects.get().pk)
        active = InventoryReservation.objects.get(source_id=self.order.pk, status="active")
        self.assertEqual(active.lines.get().quantity, Decimal("1.000000000000"))

    def test_ready_requires_explicit_actual_consumption_and_releases_unused_remainder(self):
        self.confirm()
        self.start_preparation()
        with self.assertRaises(APIValidationError):
            OrderService.update_status(
                business=self.business, order_id=self.order.pk,
                status=Order.Status.READY, user=self.actor,
            )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PREPARING)

        requirement = self.requirement()
        OrderInventoryService.record_consumption(
            business_id=self.business.pk, order_id=self.order.pk, actor_id=self.actor.pk,
            idempotency_key=uuid4(),
            lines=[{"requirement_id": requirement.pk, "quantity": "2.5", "unit": "kg"}],
        )
        OrderService.update_status(
            business=self.business, order_id=self.order.pk,
            status=Order.Status.READY, user=self.actor,
        )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.READY)
        self.assertFalse(InventoryReservation.objects.filter(
            source_id=self.order.pk, status=InventoryReservation.Status.ACTIVE
        ).exists())

    def test_incompatible_or_excess_actual_consumption_is_rejected(self):
        self.confirm()
        self.start_preparation()
        requirement = self.requirement()
        with self.assertRaises(APIValidationError):
            OrderInventoryService.record_consumption(
                business_id=self.business.pk, order_id=self.order.pk, actor_id=self.actor.pk,
                idempotency_key=uuid4(),
                lines=[{"requirement_id": requirement.pk, "quantity": "1", "unit": "pc"}],
            )
        with self.assertRaises(OperationConflict):
            OrderInventoryService.record_consumption(
                business_id=self.business.pk, order_id=self.order.pk, actor_id=self.actor.pk,
                idempotency_key=uuid4(),
                lines=[{"requirement_id": requirement.pk, "quantity": "4", "unit": "kg"}],
            )
        self.assertEqual(OrderInventoryConsumption.objects.count(), 0)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)

    def test_cancellation_after_partial_consumption_releases_only_remainder_and_keeps_movement(self):
        self.confirm()
        self.start_preparation()
        requirement = self.requirement()
        OrderInventoryService.record_consumption(
            business_id=self.business.pk, order_id=self.order.pk, actor_id=self.actor.pk,
            idempotency_key=uuid4(),
            lines=[{"requirement_id": requirement.pk, "quantity": "2", "unit": "kg"}],
        )
        movement_id = InventoryV1StockMovement.objects.get().pk

        OrderService.update_status(
            business=self.business, order_id=self.order.pk,
            status=Order.Status.CANCELLED, user=self.actor,
        )

        self.assertEqual(InventoryV1StockMovement.objects.get().pk, movement_id)
        self.assertEqual(
            InventoryReservation.objects.filter(source_id=self.order.pk, status="released").count(), 2
        )
        self.assertFalse(InventoryReservation.objects.filter(source_id=self.order.pk, status="active").exists())
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("8.000000000000"))

    def test_cancellation_before_consumption_releases_hold_without_stock_movement(self):
        self.confirm()
        OrderService.update_status(
            business=self.business, order_id=self.order.pk,
            status=Order.Status.CANCELLED, user=self.actor,
        )

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("10"))
        self.assertFalse(InventoryV1StockMovement.objects.exists())
        self.assertEqual(
            InventoryReservation.objects.get(source_id=self.order.pk).status,
            InventoryReservation.Status.RELEASED,
        )

    def test_actual_consumption_failure_rolls_back_event_reservation_and_stock(self):
        self.confirm()
        self.start_preparation()
        requirement = self.requirement()
        reservation_id = InventoryReservation.objects.get(source_id=self.order.pk).pk

        with patch("inventory.infrastructure.django.order_consumption_repository.post_issue", side_effect=RuntimeError("ledger failed")):
            with self.assertRaisesRegex(RuntimeError, "ledger failed"):
                OrderInventoryService.record_consumption(
                    business_id=self.business.pk, order_id=self.order.pk, actor_id=self.actor.pk,
                    idempotency_key=uuid4(),
                    lines=[{"requirement_id": requirement.pk, "quantity": "2", "unit": "kg"}],
                )

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("10"))
        self.assertFalse(OrderInventoryConsumption.objects.filter(order=self.order).exists())
        reservation = InventoryReservation.objects.get(pk=reservation_id)
        self.assertEqual(reservation.status, "active")
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)

    def test_consumption_cannot_access_requirement_from_another_business_order(self):
        other_business = Business.objects.create(name="Other Order Business")
        other_order = Order.objects.create(
            business=other_business, order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CASH,
        )
        with self.assertRaises(ResourceNotFound):
            OrderInventoryService.record_consumption(
                business_id=self.business.pk, order_id=other_order.pk, actor_id=self.actor.pk,
                idempotency_key=uuid4(), lines=[{"requirement_id": 1, "quantity": "1"}],
            )

    def test_pending_to_completed_is_rejected_without_estimated_consumption(self):
        with self.assertRaises(APIValidationError):
            OrderService.update_status(
                business=self.business, order_id=self.order.pk,
                status=Order.Status.COMPLETED, user=self.actor,
            )

        self.order.refresh_from_db()
        self.stock.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.stock.quantity, Decimal("10"))
        self.assertEqual(OrderInventoryConsumption.objects.count(), 0)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)

    def test_confirmed_order_cannot_be_reopened_to_pending_and_mutated(self):
        self.confirm()
        with self.assertRaises(APIValidationError):
            OrderService.update_status(
                business=self.business, order_id=self.order.pk,
                status=Order.Status.PENDING, user=self.actor,
            )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        with self.assertRaises(APIValidationError):
            OrderService.update_order(
                business=self.business, order_id=self.order.pk,
                validated_data={"items": []},
            )

    def test_confirmation_failure_after_reservation_rolls_back_everything(self):
        original = OrderInventoryService.confirm

        def fail_after_confirmation(*, order, actor_id):
            original(order=order, actor_id=actor_id)
            raise RuntimeError("injected confirmation failure")

        with patch.object(OrderInventoryService, "confirm", side_effect=fail_after_confirmation):
            with self.assertRaisesRegex(RuntimeError, "injected"):
                self.confirm()

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertFalse(self.order.recipe_snapshots.exists())
        self.assertFalse(InventoryReservation.objects.filter(source_id=self.order.pk).exists())

    def test_orders_only_business_confirms_without_recipe_or_warehouse(self):
        self.business.inventory_enabled = False
        self.business.save(update_fields=("inventory_enabled",))
        Warehouse.objects.filter(pk=self.warehouse.pk).update(is_active=False, is_default=False)
        self.confirm()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertFalse(self.order.recipe_snapshots.exists())
        self.assertFalse(InventoryReservation.objects.filter(
            business=self.business, source_type="order", source_id=self.order.pk
        ).exists())

    def test_orders_only_business_can_complete_without_actual_consumption(self):
        self.business.inventory_enabled = False
        self.business.save(update_fields=("inventory_enabled",))
        Warehouse.objects.filter(pk=self.warehouse.pk).update(is_active=False, is_default=False)
        self.confirm()
        self.start_preparation()
        OrderService.update_status(
            business=self.business, order_id=self.order.pk,
            status=Order.Status.READY, user=self.actor,
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.READY)
        self.assertFalse(self.order.recipe_snapshots.exists())

    def test_orders_only_mode_is_frozen_for_an_order_when_business_setting_changes(self):
        self.business.inventory_enabled = False
        self.business.save(update_fields=("inventory_enabled",))
        self.confirm()
        self.order.refresh_from_db()
        self.assertFalse(self.order.inventory_tracking_enabled)

        self.business.inventory_enabled = True
        self.business.save(update_fields=("inventory_enabled",))
        self.start_preparation()
        OrderService.update_status(
            business=self.business, order_id=self.order.pk,
            status=Order.Status.READY, user=self.actor,
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.READY)
        self.assertFalse(self.order.recipe_snapshots.exists())

    def test_inventory_enabled_business_still_requires_default_warehouse(self):
        Warehouse.objects.filter(pk=self.warehouse.pk).update(is_active=False, is_default=False)
        with self.assertRaisesMessage(APIValidationError,
            "Configure exactly one active default warehouse before confirming recipe-based orders."):
            self.confirm()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)


class OrderInventoryRefundTests(TestCase):
    confirm = OrderInventoryLifecycleTests.confirm
    start_preparation = OrderInventoryLifecycleTests.start_preparation
    requirement = OrderInventoryLifecycleTests.requirement
    """Refund inventory release stays atomic with the existing wallet refund."""

    def setUp(self):
        OrderInventoryLifecycleTests.setUp(self)
        self.customer = Customer.objects.create(
            business=self.business, name="Refund Customer", phone="5550100"
        )
        CustomerAccount.objects.create(
            business=self.business,
            customer=self.customer,
            balance=Decimal("100.00"),
            ledger_opening_balance=Decimal("100.00"),
            ledger_opening_balance_verified=True,
        )
        self.order.customer = self.customer
        self.order.payment_method = Order.PaymentMethod.CUSTOMER_ACCOUNT
        self.order.save(update_fields=("customer", "payment_method"))
        OrderService.update_status(
            business=self.business,
            order_id=self.order.pk,
            payment_status=Order.PaymentStatus.PAID,
            user=self.actor,
        )

    def refund(self, key=None):
        return OrderService.refund_order(
            business=self.business,
            order_id=self.order.pk,
            user=self.actor,
            idempotency_key=key or uuid4(),
            reason="Refund requested",
        )

    def test_refund_of_confirmed_order_releases_reservation_without_stock_movement(self):
        self.confirm()
        reservation = InventoryReservation.objects.get(source_id=self.order.pk, status="active")
        self.stock.refresh_from_db()
        physical_before = self.stock.quantity

        self.refund()

        reservation.refresh_from_db()
        self.stock.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(reservation.status, InventoryReservation.Status.RELEASED)
        self.assertEqual(self.stock.quantity, physical_before)
        self.assertFalse(InventoryV1StockMovement.objects.exists())
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.REFUNDED)
        history = OrderStatusHistory.objects.filter(order=self.order).order_by("created_at", "pk").last()
        self.assertEqual(history.from_status, Order.Status.CONFIRMED)
        self.assertEqual(history.to_status, Order.Status.CANCELLED)
        self.assertEqual(history.actor_id, self.actor.pk)

    def test_refund_after_partial_consumption_releases_only_remaining_hold(self):
        self.confirm()
        self.start_preparation()
        requirement = self.requirement()
        OrderInventoryService.record_consumption(
            business_id=self.business.pk,
            order_id=self.order.pk,
            actor_id=self.actor.pk,
            idempotency_key=uuid4(),
            lines=[{"requirement_id": requirement.pk, "quantity": "2", "unit": "kg"}],
        )
        movement = InventoryV1StockMovement.objects.get()
        self.stock.refresh_from_db()
        physical_after_consumption = self.stock.quantity
        reservation = InventoryReservation.objects.get(source_id=self.order.pk, status="active")
        self.assertEqual(reservation.lines.get().quantity, Decimal("1.000000000000"))

        self.refund()

        reservation.refresh_from_db()
        self.stock.refresh_from_db()
        self.assertEqual(reservation.status, InventoryReservation.Status.RELEASED)
        self.assertEqual(self.stock.quantity, physical_after_consumption)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 1)
        self.assertEqual(InventoryV1StockMovement.objects.get().pk, movement.pk)
        self.assertEqual(movement.quantity, Decimal("2.000000000000"))

    def test_repeated_refund_does_not_repeat_release_or_wallet_accounting(self):
        self.confirm()
        key = uuid4()
        self.refund(key)
        released = InventoryReservation.objects.get(source_id=self.order.pk)
        released_at = released.released_at
        transaction_count = CustomerTransaction.objects.filter(order=self.order).count()

        self.refund(key)

        released.refresh_from_db()
        self.assertEqual(InventoryReservation.objects.filter(source_id=self.order.pk).count(), 1)
        self.assertEqual(released.status, InventoryReservation.Status.RELEASED)
        self.assertEqual(released.released_at, released_at)
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order).count(), transaction_count)
        self.assertEqual(OrderRefund.objects.filter(order=self.order).count(), 1)

    def test_reservation_release_failure_rolls_back_refund_and_wallet_credit(self):
        self.confirm()
        transaction_count = CustomerTransaction.objects.filter(order=self.order).count()
        account = self.customer.account
        account.refresh_from_db()
        account_balance = account.balance

        with patch(
            "products.services.order_service.OrderInventoryService.release_remaining",
            side_effect=RuntimeError("reservation release failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "reservation release failed"):
                self.refund()

        self.order.refresh_from_db()
        account.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(account.balance, account_balance)
        self.assertEqual(CustomerTransaction.objects.filter(order=self.order).count(), transaction_count)
        self.assertFalse(OrderRefund.objects.filter(order=self.order).exists())
        self.assertEqual(
            InventoryReservation.objects.get(source_id=self.order.pk).status,
            InventoryReservation.Status.ACTIVE,
        )

    def test_refund_without_inventory_reservation_remains_valid(self):
        # The order is paid but still pending, so no Inventory V1 reservation exists.
        self.assertFalse(InventoryReservation.objects.filter(source_id=self.order.pk).exists())

        refund = self.refund()

        self.order.refresh_from_db()
        self.assertEqual(refund.order_id, self.order.pk)
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.REFUNDED)
        self.assertFalse(InventoryReservation.objects.filter(source_id=self.order.pk).exists())


class OrderConsumptionRequirementsReadTests(TestCase):
    confirm = OrderInventoryLifecycleTests.confirm
    start_preparation = OrderInventoryLifecycleTests.start_preparation
    requirement = OrderInventoryLifecycleTests.requirement
    def setUp(self):
        OrderInventoryLifecycleTests.setUp(self)
        self.confirm()
        self.start_preparation()
        self.request = SimpleNamespace(
            business=self.business,
            permissions={PermissionCode.ORDERS_VIEW.value, PermissionCode.ORDERS_UPDATE.value, PermissionCode.INVENTORY_ORDER_FULFILL.value},
        )

    def test_read_contract_returns_snapshot_and_accumulated_actual_consumption(self):
        requirement = self.requirement()
        OrderInventoryService.record_consumption(
            business_id=self.business.pk,
            order_id=self.order.pk,
            actor_id=self.actor.pk,
            idempotency_key=uuid4(),
            lines=[{"requirement_id": requirement.pk, "quantity": "0.5", "unit": "kg"}],
        )

        response = OrderActualConsumptionAPIView().get(self.request, order_id=self.order.pk)

        self.assertEqual(response.data["order_id"], self.order.pk)
        self.assertEqual(response.data["requirements"], [{
            "requirement_id": requirement.pk,
            "order_item_id": self.order_item.pk,
            "menu_item_name": self.order_item.menu_item_name,
            "ingredient_id": self.flour.pk,
            "ingredient_name": self.flour.name,
            "standard_quantity": "3.000000000000",
            "actual_quantity": "0.500000000000",
            "unit": "kg",
            "has_actual_record": True,
        }])

    def test_read_contract_hides_another_business_order(self):
        other_business = Business.objects.create(name="Other Requirements Business")
        other_order = Order.objects.create(
            business=other_business,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CASH,
        )

        with self.assertRaises(Http404):
            OrderActualConsumptionAPIView().get(self.request, order_id=other_order.pk)

    def test_read_contract_hides_foreign_business_ingredient_reference(self):
        requirement = self.requirement()
        other_business = Business.objects.create(name="Foreign Ingredient Business")
        foreign_ingredient = Ingredient.objects.create(
            business=other_business,
            name="Foreign confidential ingredient",
            unit="kg",
            preparation_level="raw",
        )
        OrderItemIngredientRequirement.objects.filter(pk=requirement.pk).update(
            ingredient=foreign_ingredient,
        )

        with self.assertRaises(Http404):
            OrderActualConsumptionAPIView().get(self.request, order_id=self.order.pk)


@skipUnless(connection.vendor == "postgresql", "Requires isolated PostgreSQL row-lock semantics")
class ConcurrentOrderConfirmationTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.business = Business.objects.create(name="Concurrent Order Business")
        self.actor = User.objects.create_user(
            email="concurrent-order@example.test", password="test-password",
            name="Concurrent Operator", number="7011",
        )
        warehouse = Warehouse.objects.create(
            business=self.business, name="Main", is_active=True, is_default=True
        )
        flour = Ingredient.objects.create(business=self.business, name="Flour", unit="kg")
        dish = Ingredient.objects.create(business=self.business, name="Dish", unit="pc")
        InventoryV1Stock.objects.create(
            business=self.business, warehouse=warehouse, ingredient=flour,
            unit="kg", quantity=Decimal("3"), average_cost=Decimal("1"),
        )
        menu = Menu.objects.create(business=self.business, name="Menu", category="Test")
        self.orders = []
        for index in range(2):
            recipe = Recipe.objects.create(business=self.business, name=f"Dish recipe {index}")
            RecipeInput.objects.create(
                recipe=recipe, ingredient=flour, quantity=Decimal("3"), unit="kg"
            )
            RecipeOutput.objects.create(
                recipe=recipe, ingredient=dish, quantity=Decimal("1"), unit="pc", is_primary=True
            )
            menu_item = MenuItem.objects.create(
                business=self.business, menu=menu, name=f"Dish {index}",
                price=Decimal("1"), recipe=recipe,
            )
            order = Order.objects.create(
                business=self.business, order_type=Order.OrderType.TAKEAWAY,
                payment_method=Order.PaymentMethod.CASH,
            )
            OrderItem.objects.create(
                order=order, menu_item=menu_item, menu_item_name=menu_item.name,
                quantity=1, unit_price=Decimal("1"), total_price=Decimal("1"),
            )
            self.orders.append(order.pk)

    def test_two_confirmations_cannot_reserve_the_last_available_quantity(self):
        barrier = Barrier(2)

        def confirm(order_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                OrderService.update_status(
                    business=Business.objects.get(pk=self.business.pk),
                    order_id=order_id,
                    status=Order.Status.CONFIRMED,
                    user=User.objects.get(pk=self.actor.pk),
                )
                return "confirmed"
            except APIValidationError:
                return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(confirm, self.orders))

        self.assertCountEqual(outcomes, ["confirmed", "rejected"])
        self.assertEqual(
            InventoryReservationLine.objects.filter(
                reservation__business=self.business,
                reservation__status=InventoryReservation.Status.ACTIVE,
            ).aggregate(total=Sum("quantity"))["total"],
            Decimal("3.000000000000"),
        )
        self.assertEqual(
            Order.objects.filter(pk__in=self.orders, status=Order.Status.CONFIRMED).count(), 1
        )


@skipUnless(connection.vendor == "postgresql", "Requires isolated PostgreSQL row-lock semantics")
class ConcurrentOrderConfirmationReleaseTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.business = Business.objects.create(name="Confirm Release Race Business")
        self.actor = User.objects.create_user(
            email="confirm-release-race@example.test",
            password="test-password",
            name="Concurrent Operator",
            number="7012",
        )
        warehouse = Warehouse.objects.create(
            business=self.business, name="Main", is_active=True, is_default=True
        )
        flour = Ingredient.objects.create(
            business=self.business, name="Flour", unit="kg"
        )
        dish = Ingredient.objects.create(
            business=self.business, name="Dish", unit="pc"
        )
        self.stock = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=warehouse,
            ingredient=flour,
            unit="kg",
            quantity=Decimal("3"),
            average_cost=Decimal("1"),
        )
        recipe = Recipe.objects.create(
            business=self.business, name="Race test recipe"
        )
        RecipeInput.objects.create(
            recipe=recipe, ingredient=flour, quantity=Decimal("3"), unit="kg"
        )
        RecipeOutput.objects.create(
            recipe=recipe, ingredient=dish, quantity=Decimal("1"),
            unit="pc", is_primary=True,
        )
        menu = Menu.objects.create(
            business=self.business, name="Race test menu", category="Test"
        )
        menu_item = MenuItem.objects.create(
            business=self.business, menu=menu, name="Race test dish",
            price=Decimal("1"), recipe=recipe,
        )
        self.order = Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CASH,
        )
        OrderItem.objects.create(
            order=self.order, menu_item=menu_item,
            menu_item_name=menu_item.name, quantity=1,
            unit_price=Decimal("1"), total_price=Decimal("1"),
        )

    def test_concurrent_confirm_and_cancel_never_leave_an_active_reservation(self):
        barrier = Barrier(2)

        def confirm():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                OrderService.update_status(
                    business=Business.objects.get(pk=self.business.pk),
                    order_id=self.order.pk,
                    status=Order.Status.CONFIRMED,
                    user=User.objects.get(pk=self.actor.pk),
                )
                return "confirmed"
            except APIValidationError:
                return "rejected"
            finally:
                close_old_connections()

        def cancel_and_release():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                OrderService.update_status(
                    business=Business.objects.get(pk=self.business.pk),
                    order_id=self.order.pk,
                    status=Order.Status.CANCELLED,
                    user=User.objects.get(pk=self.actor.pk),
                )
                return "released"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            confirm_future = pool.submit(confirm)
            release_future = pool.submit(cancel_and_release)
            outcomes = [confirm_future.result(), release_future.result()]

        self.assertIn(outcomes[0], ("confirmed", "rejected"))
        self.assertEqual(outcomes[1], "released")

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)

        reservations = InventoryReservation.objects.filter(
            business=self.business, source_type="order", source_id=self.order.pk
        )
        self.assertLessEqual(reservations.count(), 1)
        self.assertFalse(
            reservations.filter(status=InventoryReservation.Status.ACTIVE).exists()
        )
        if reservations.exists():
            self.assertEqual(
                reservations.get().status, InventoryReservation.Status.RELEASED
            )

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("3"))
        self.assertFalse(
            InventoryV1StockMovement.objects.filter(
                business=self.business, source_type="order",
                source_document_id=self.order.pk,
            ).exists()
        )

@skipUnless(connection.vendor == "postgresql", "Requires isolated PostgreSQL row-lock semantics")
class ConcurrentConsumptionReservationReplacementTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.business = Business.objects.create(name="Consumption Reservation Race Business")
        self.actor = User.objects.create_user(
            email="consumption-reservation-race@example.test",
            password="test-password",
            name="Inventory Operator",
            number="7013",
        )
        self.warehouse = Warehouse.objects.create(
            business=self.business, name="Main", is_active=True, is_default=True
        )
        self.flour = Ingredient.objects.create(
            business=self.business, name="Flour", unit="kg"
        )
        dish = Ingredient.objects.create(
            business=self.business, name="Dish", unit="pc"
        )
        self.stock = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.warehouse,
            ingredient=self.flour,
            unit="kg",
            quantity=Decimal("10"),
            average_cost=Decimal("1"),
        )
        recipe = Recipe.objects.create(
            business=self.business, name="Consumption race recipe"
        )
        RecipeInput.objects.create(
            recipe=recipe, ingredient=self.flour,
            quantity=Decimal("1500"), unit="g",
        )
        RecipeOutput.objects.create(
            recipe=recipe, ingredient=dish,
            quantity=Decimal("1"), unit="pc", is_primary=True,
        )
        menu = Menu.objects.create(
            business=self.business, name="Consumption race menu", category="Test"
        )
        menu_item = MenuItem.objects.create(
            business=self.business, menu=menu, name="Consumption race dish",
            price=Decimal("1"), recipe=recipe,
        )
        self.order = Order.objects.create(
            business=self.business,
            order_type=Order.OrderType.TAKEAWAY,
            payment_method=Order.PaymentMethod.CASH,
        )
        self.order_item = OrderItem.objects.create(
            order=self.order, menu_item=menu_item,
            menu_item_name=menu_item.name, quantity=2,
            unit_price=Decimal("1"), total_price=Decimal("2"),
        )
        OrderService.update_status(
            business=self.business, order_id=self.order.pk,
            status=Order.Status.CONFIRMED, user=self.actor,
        )
        OrderService.update_status(
            business=self.business, order_id=self.order.pk,
            status=Order.Status.PREPARING, user=self.actor,
        )
        self.requirement_id = self.order_item.inventory_recipe_snapshot.requirements.get().pk

    def test_consumption_replacement_serializes_before_stock_against_new_reservation(self):
        manual_scope_locked = Event()
        consumption_scope_requested = Event()
        allow_manual_to_continue = Event()
        thread_roles = local()
        original_lock_scope = DjangoReservationRepository.lock_scope

        def coordinated_lock_scope(repository, *args, **kwargs):
            role = getattr(thread_roles, "role", None)
            if role == "manual_reservation":
                result = original_lock_scope(repository, *args, **kwargs)
                manual_scope_locked.set()
                if not allow_manual_to_continue.wait(timeout=15):
                    raise TimeoutError("Timed out waiting to continue the competing reservation.")
                return result
            if role == "consumption":
                consumption_scope_requested.set()
            return original_lock_scope(repository, *args, **kwargs)

        def create_competing_reservation():
            close_old_connections()
            thread_roles.role = "manual_reservation"
            try:
                use_case = ManageReservations(
                    DjangoReservationRepository(), DjangoInventoryUnitOfWork(), DjangoOrderReservationSource()
                )
                try:
                    use_case.create(
                        InventoryExecutionContext(self.business.pk, self.actor.pk),
                        warehouse_id=self.warehouse.pk,
                        source_type=MANUAL_RESERVATION_SOURCE,
                        source_id=None,
                        reason="Concurrent manual reservation",
                        idempotency_key=uuid4(),
                        lines=[{
                            "ingredient_id": self.flour.pk,
                            "quantity": "7.5",
                            "unit": "kg",
                        }],
                    )
                    return "reserved"
                except OperationConflict:
                    return "rejected"
            finally:
                close_old_connections()

        def record_consumption():
            close_old_connections()
            thread_roles.role = "consumption"
            try:
                return OrderInventoryService.record_consumption(
                    business_id=self.business.pk,
                    order_id=self.order.pk,
                    actor_id=self.actor.pk,
                    idempotency_key=uuid4(),
                    lines=[{
                        "requirement_id": self.requirement_id,
                        "quantity": "2",
                        "unit": "kg",
                    }],
                )
            finally:
                close_old_connections()

        with patch.object(
            DjangoReservationRepository, "lock_scope", coordinated_lock_scope
        ):
            with ThreadPoolExecutor(
                max_workers=2, thread_name_prefix="consumption-reservation-race"
            ) as pool:
                manual_future = pool.submit(create_competing_reservation)
                self.assertTrue(
                    manual_scope_locked.wait(timeout=10),
                    "The competing reservation did not acquire its warehouse/ingredient scope.",
                )
                consumption_future = pool.submit(record_consumption)
                self.assertTrue(
                    consumption_scope_requested.wait(timeout=10),
                    "Consumption did not reach the shared lock scope.",
                )
                # The competing transaction now owns Warehouse/Ingredient.
                # Consumption must be waiting for that scope before it locks Stock.
                allow_manual_to_continue.set()
                manual_result = manual_future.result(timeout=20)
                consumption = consumption_future.result(timeout=20)

        self.assertEqual(manual_result, "rejected")
        self.assertIsNotNone(consumption)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("8.000000000000"))
        self.assertEqual(
            InventoryV1StockMovement.objects.filter(
                business=self.business, source_type="inventory_issue",
                operation_kind="post",
            ).count(),
            1,
        )
        self.assertEqual(
            OrderInventoryConsumption.objects.filter(
                business=self.business, order_id=self.order.pk
            ).count(),
            1,
        )
        reservations = InventoryReservation.objects.filter(
            business=self.business, source_type="order", source_id=self.order.pk
        )
        self.assertEqual(reservations.filter(status=InventoryReservation.Status.RELEASED).count(), 1)
        active = reservations.get(status=InventoryReservation.Status.ACTIVE)
        self.assertEqual(active.lines.get(ingredient=self.flour).quantity, Decimal("1.000000000000"))
        self.assertFalse(
            InventoryReservation.objects.filter(
                business=self.business, source_type=MANUAL_RESERVATION_SOURCE
            ).exists()
        )

