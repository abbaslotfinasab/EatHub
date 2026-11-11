"""Composition facade for Sales-owned order workflows backed by Inventory Application."""

from uuid import UUID

from inventory.application.context import InventoryExecutionContext
from inventory.application.use_cases.manage_reservations import ManageReservations
from inventory.application.use_cases.prepare_order_confirmation import PrepareOrderConfirmation
from inventory.application.use_cases.resolve_order_requirement_ingredients import ResolveOrderRequirementIngredients
from inventory.infrastructure.django.recipe_repository import DjangoRecipeRepository
from inventory.infrastructure.django.repositories import DjangoIngredientRepository, DjangoWarehouseRepository
from inventory.infrastructure.django.reservation_repository import DjangoReservationRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork

from composition.order_reservation_source import DjangoOrderReservationSource


def _context(business_id: int, actor_id: int) -> InventoryExecutionContext:
    return InventoryExecutionContext(business_id, actor_id)


def _reservation_use_case(unit_of_work=None) -> ManageReservations:
    uow = unit_of_work or DjangoInventoryUnitOfWork()
    return ManageReservations(DjangoReservationRepository(), uow, DjangoOrderReservationSource())


def resolve_order_requirement_ingredients(*, business_id: int, ingredient_ids: list[int]):
    use_case = ResolveOrderRequirementIngredients(DjangoIngredientRepository())
    return use_case.execute(business_id=business_id, ingredient_ids=ingredient_ids)


def prepare_order_confirmation_inventory(*, business_id: int, actor_id: int, recipe_ids: list[int]):
    uow = DjangoInventoryUnitOfWork()
    use_case = PrepareOrderConfirmation(DjangoRecipeRepository(), DjangoWarehouseRepository(), uow)
    return use_case.execute(_context(business_id, actor_id), recipe_ids)


def create_order_reservation(
    *, business_id: int, actor_id: int, warehouse_id: int, order_id: int,
    reason: str, idempotency_key: UUID, lines: list[dict],
):
    return _reservation_use_case().create_for_order(
        _context(business_id, actor_id),
        warehouse_id=warehouse_id,
        order_id=order_id,
        reason=reason,
        idempotency_key=idempotency_key,
        lines=lines,
    )


def validate_order_reservation_for_confirmation(*, business_id: int, actor_id: int, order_id: int):
    return _reservation_use_case().validate_order_reservation_for_confirmation(
        _context(business_id, actor_id), order_id
    )


def prepare_order_consumption_reservation(*, business_id: int, actor_id: int, order_id: int):
    return _reservation_use_case().prepare_order_consumption(
        _context(business_id, actor_id), order_id
    )


def release_remaining_order_reservation(
    *, business_id: int, actor_id: int, order_id: int, reason: str
) -> None:
    _reservation_use_case().release_for_order(
        _context(business_id, actor_id), order_id, reason
    )
