from __future__ import annotations
from decimal import Decimal, localcontext
import hashlib
import json
from uuid import UUID

from inventory.application.context import InventoryExecutionContext
from inventory.application.dto.reservation import ReservationDTO, StockAvailabilityDTO
from inventory.application.exceptions import InvalidApplicationInput, OperationConflict, ResourceNotFound
from inventory.application.ports.reservations import ReservationRepository
from inventory.application.ports.unit_of_work import InventoryUnitOfWork
from inventory.domain.entities.reservation import (
    MANUAL_RESERVATION_SOURCE,
    ORDER_RESERVATION_SOURCE,
    ReservationLine,
    ReservationRequest,
)
from inventory.domain.enums.reservation import ReservationStatus
from inventory.domain.exceptions import InventoryDomainError, InvalidReservation
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.unit import Unit


class ManageReservations:
    MAX_PAGE_SIZE = 100

    def __init__(self, reservations: ReservationRepository, unit_of_work: InventoryUnitOfWork) -> None:
        self._reservations = reservations
        self._unit_of_work = unit_of_work

    def create(self, context: InventoryExecutionContext, *, warehouse_id: int, source_type: str,
               source_id: int | None, reason: str, idempotency_key: UUID,
               lines: list[dict]) -> ReservationDTO:
        if source_type != MANUAL_RESERVATION_SOURCE or source_id is not None:
            raise InvalidApplicationInput("Manual reservations cannot reference external sources.")
        if isinstance(lines, list) and any(
            isinstance(line, dict) and line.get("source_line_id") is not None for line in lines
        ):
            raise InvalidApplicationInput("Manual reservations cannot reference external source lines.")
        return self._create(
            context, warehouse_id=warehouse_id, source_type=source_type,
            source_id=source_id, reason=reason, idempotency_key=idempotency_key,
            lines=lines, order_source=False,
        )

    def create_for_order(self, context: InventoryExecutionContext, *, warehouse_id: int,
                         order_id: int, reason: str, idempotency_key: UUID,
                         lines: list[dict]) -> ReservationDTO:
        if isinstance(order_id, bool) or not isinstance(order_id, int) or order_id <= 0:
            raise InvalidApplicationInput("Order ID must be a positive integer.")
        if not isinstance(lines, list) or any(
            isinstance(line, dict) and line.get("source_line_id") is not None for line in lines
        ):
            raise InvalidApplicationInput("Order reservations are aggregated by ingredient.")
        return self._create(
            context, warehouse_id=warehouse_id, source_type=ORDER_RESERVATION_SOURCE,
            source_id=order_id, reason=reason, idempotency_key=idempotency_key,
            lines=lines, order_source=True,
        )

    def _create(self, context: InventoryExecutionContext, *, warehouse_id: int, source_type: str,
               source_id: int | None, reason: str, idempotency_key: UUID,
               lines: list[dict], order_source: bool) -> ReservationDTO:
        if not isinstance(context, InventoryExecutionContext):
            raise InvalidApplicationInput("A trusted inventory execution context is required.")
        if not isinstance(idempotency_key, UUID):
            raise InvalidApplicationInput("Idempotency key must be a UUID.")
        if context.actor_id is None:
            raise InvalidApplicationInput("A reservation actor is required.")
        if not isinstance(warehouse_id, int) or isinstance(warehouse_id, bool) or warehouse_id <= 0:
            raise InvalidApplicationInput("Warehouse ID must be a positive integer.")
        if source_type == MANUAL_RESERVATION_SOURCE:
            if source_id is not None or order_source:
                raise InvalidApplicationInput("Manual reservations cannot reference external sources.")
        elif source_type == ORDER_RESERVATION_SOURCE:
            if not order_source or source_id is None:
                raise InvalidApplicationInput("Order reservations require a tenant-resolved order source.")
        else:
            raise InvalidApplicationInput("Unsupported reservation source type.")
        if not isinstance(lines, list) or not lines or any(not isinstance(line, dict) for line in lines):
            raise InvalidApplicationInput("At least one reservation line object is required.")
        if any(line.get("source_line_id") is not None for line in lines):
            raise InvalidApplicationInput("Manual reservations cannot reference external source lines.")

        with self._unit_of_work.atomic():
            if order_source and not self._reservations.order_source_is_active(
                context.business_id, source_id
            ):
                raise ResourceNotFound("Active order was not found in this Business.")
            existing = self._reservations.get_by_idempotency_key(context.business_id, idempotency_key, lock=True)
            if existing is not None:
                ingredient_ids = self._ingredient_ids(lines)
                _warehouse, ingredients = self._reservations.lock_scope(
                    context.business_id, warehouse_id, ingredient_ids
                )
                _request, fingerprint = self._build_request(
                    context, warehouse_id, source_type, source_id, reason, idempotency_key, lines, ingredients
                )
                if order_source and not self._reservations.order_reservation_matches(
                    context.business_id, source_id, _request.lines
                ):
                    raise OperationConflict("Order reservation quantities must match its immutable requirements.")
                self._same_request(existing, fingerprint)
                return existing

            ingredient_ids = self._ingredient_ids(lines)
            warehouse, ingredients = self._reservations.lock_scope(
                context.business_id, warehouse_id, ingredient_ids
            )
            if warehouse is None:
                raise ResourceNotFound("Warehouse was not found in this Business.")
            warehouse.ensure_active()
            if any(ingredient_id not in ingredients for ingredient_id in ingredient_ids):
                raise ResourceNotFound("An ingredient was not found in this Business.")
            if any(not ingredient.is_active for ingredient in ingredients.values()):
                raise InvalidApplicationInput("Inactive ingredients cannot be reserved.")

            request, fingerprint = self._build_request(
                context, warehouse_id, source_type, source_id, reason, idempotency_key, lines, ingredients
            )
            if order_source and not self._reservations.order_reservation_matches(
                context.business_id, source_id, request.lines
            ):
                raise OperationConflict("Order reservation quantities must match its immutable requirements.")
            positions = self._reservations.lock_stock_positions(
                context.business_id, warehouse_id, ingredient_ids
            )
            # A missing projection is physical zero. It cannot support a positive
            # reservation, so reject it rather than relying on a nonexistent row lock.
            for line in request.lines:
                physical = positions.get(line.ingredient_id)
                if physical is None:
                    raise OperationConflict("No stock balance exists for an ingredient in this warehouse.")
                if physical.unit is not line.quantity.unit:
                    raise OperationConflict("Stock and ingredient canonical units do not match.")

            # Recheck after stock locks: another request using the same key may
            # have committed while this request waited for those locks.
            existing = self._reservations.get_by_idempotency_key(context.business_id, idempotency_key, lock=True)
            if existing is not None:
                self._same_request(existing, fingerprint)
                return existing

            reserved = self._reservations.get_active_reserved(context.business_id, warehouse_id, ingredient_ids)
            requested_by_ingredient = {}
            for line in request.lines:
                current = requested_by_ingredient.get(
                    line.ingredient_id, Quantity.zero(line.quantity.unit)
                )
                if current.unit is not line.quantity.unit:
                    raise OperationConflict("Reservation lines use incompatible canonical units.")
                with localcontext() as context_decimal:
                    context_decimal.prec = 80
                    requested_by_ingredient[line.ingredient_id] = Quantity(
                        current.amount + line.quantity.amount, current.unit
                    )
            for ingredient_id, requested in requested_by_ingredient.items():
                physical = positions[ingredient_id]
                already_reserved = reserved.get(ingredient_id, Quantity.zero(requested.unit))
                if already_reserved.unit is not requested.unit:
                    raise OperationConflict("Persisted reservation unit does not match the canonical unit.")
                with localcontext() as context_decimal:
                    context_decimal.prec = 80
                    exceeds = requested.amount + already_reserved.amount > physical.amount
                if exceeds:
                    raise OperationConflict("Insufficient available stock for this reservation.")

            return self._reservations.create(request, fingerprint, context.actor_id or 0)

    def release(self, context: InventoryExecutionContext, reservation_id: int,
                idempotency_key: UUID, reason: str) -> ReservationDTO:
        if not isinstance(context, InventoryExecutionContext):
            raise InvalidApplicationInput("A trusted inventory execution context is required.")
        if not isinstance(idempotency_key, UUID):
            raise InvalidApplicationInput("Idempotency key must be a UUID.")
        if context.actor_id is None:
            raise InvalidApplicationInput("A reservation actor is required.")
        reason = reason.strip() if isinstance(reason, str) else ""
        if not reason:
            raise InvalidApplicationInput("A release reason is required.")
        with self._unit_of_work.atomic():
            existing = self._reservations.get_for_business(context.business_id, reservation_id, lock=True)
            if existing is None:
                raise ResourceNotFound("Reservation was not found in this Business.")
            if existing.status is ReservationStatus.RELEASED:
                # The repository verifies the original release key and reason.
                return self._reservations.release(context.business_id, reservation_id, context.actor_id or 0, idempotency_key, reason)
            return self._reservations.release(context.business_id, reservation_id, context.actor_id or 0, idempotency_key, reason)

    def get(self, context: InventoryExecutionContext, reservation_id: int) -> ReservationDTO:
        if not isinstance(context, InventoryExecutionContext):
            raise InvalidApplicationInput("A trusted inventory execution context is required.")
        result = self._reservations.get_for_business(context.business_id, reservation_id)
        if result is None:
            raise ResourceNotFound("Reservation was not found in this Business.")
        return result

    def list(self, context: InventoryExecutionContext, *, source_type: str | None = None,
             source_id: int | None = None, status: str | None = None,
             page: int = 1, page_size: int = 20) -> tuple[int, list[ReservationDTO]]:
        if not isinstance(context, InventoryExecutionContext):
            raise InvalidApplicationInput("A trusted inventory execution context is required.")
        if page < 1 or page_size < 1 or page_size > self.MAX_PAGE_SIZE:
            raise InvalidApplicationInput("Page must be positive and page size must be between 1 and 100.")
        return self._reservations.list_for_business(
            context.business_id, source_type=source_type, source_id=source_id,
            status=status, page=page, page_size=page_size,
        )

    def availability(self, context: InventoryExecutionContext, warehouse_id: int,
                     ingredient_id: int) -> StockAvailabilityDTO:
        if not isinstance(context, InventoryExecutionContext):
            raise InvalidApplicationInput("A trusted inventory execution context is required.")
        with self._unit_of_work.atomic():
            result = self._reservations.availability(context.business_id, warehouse_id, ingredient_id)
        if result is None:
            raise ResourceNotFound("Warehouse or ingredient was not found in this Business.")
        return result

    def _build_request(self, context, warehouse_id, source_type, source_id, reason, key, lines, ingredients=None):
        if not isinstance(lines, list) or not lines:
            raise InvalidApplicationInput("At least one reservation line is required.")
        ingredients = ingredients or {}
        normalized = []
        for raw in lines:
            if not isinstance(raw, dict):
                raise InvalidApplicationInput("Reservation line must be an object.")
            ingredient_id = raw.get("ingredient_id")
            ingredient = ingredients.get(ingredient_id)
            if ingredient is None:
                raise ResourceNotFound("An ingredient was not found in this Business.")
            try:
                requested_unit = Unit(raw.get("unit", ingredient.canonical_unit.value))
                quantity = Quantity(raw.get("quantity"), requested_unit).convert_to(ingredient.canonical_unit)
            except (InventoryDomainError, TypeError, ValueError) as error:
                raise InvalidApplicationInput(str(error)) from error
            if quantity.amount <= 0:
                raise InvalidApplicationInput("Reservation quantities must be positive.")
            normalized.append(ReservationLine(
                ingredient_id=ingredient_id,
                quantity=quantity,
                source_line_id=raw.get("source_line_id"),
            ))
        try:
            request = ReservationRequest(
                business_id=context.business_id, warehouse_id=warehouse_id,
                source_type=source_type, source_id=source_id,
                reason=reason.strip() if isinstance(reason, str) else reason,
                idempotency_key=str(key), lines=tuple(normalized),
            )
        except InvalidReservation as error:
            raise InvalidApplicationInput(str(error)) from error
        fingerprint_data = {
            "warehouse_id": warehouse_id, "source_type": source_type,
            "source_id": source_id, "reason": request.reason,
            "lines": sorted([
                {"ingredient_id": line.ingredient_id, "source_line_id": line.source_line_id,
                 "quantity": format(line.quantity.amount, "f"), "unit": line.quantity.unit.value}
                for line in normalized
            ], key=lambda row: (row["ingredient_id"], row["source_line_id"] or 0)),
        }
        fingerprint = hashlib.sha256(json.dumps(fingerprint_data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return request, fingerprint

    @staticmethod
    def _ingredient_ids(lines: list[dict]) -> list[int]:
        if not isinstance(lines, list) or not lines or any(not isinstance(line, dict) for line in lines):
            raise InvalidApplicationInput("At least one reservation line object is required.")
        raw_ids = [line.get("ingredient_id") for line in lines]
        if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in raw_ids):
            raise InvalidApplicationInput("Reservation lines require valid ingredient IDs.")
        return sorted(set(raw_ids))

    @staticmethod
    def _same_request(existing: ReservationDTO, fingerprint: str) -> None:
        stored = getattr(existing, "payload_fingerprint", None)
        if stored != fingerprint:
            raise OperationConflict("This idempotency key was already used with different reservation data.")
