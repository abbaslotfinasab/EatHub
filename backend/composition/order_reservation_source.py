"""Composition adapter for Sales-owned order facts consumed by Inventory."""

from decimal import Decimal

from products.models import (
    Order,
    OrderInventoryConsumptionLine,
    OrderItemIngredientRequirement,
)


class DjangoOrderReservationSource:
    """Expose tenant-scoped order state and remaining requirements to Inventory."""

    @staticmethod
    def is_active(business_id: int, order_id: int) -> bool:
        return Order.objects.filter(
            pk=order_id,
            business_id=business_id,
            status__in=(Order.Status.CONFIRMED, Order.Status.PREPARING),
        ).exists()

    @staticmethod
    def reservation_matches(business_id: int, order_id: int, lines) -> bool:
        expected = {}
        requirements = OrderItemIngredientRequirement.objects.filter(
            snapshot__business_id=business_id,
            snapshot__order_id=order_id,
            snapshot__order__business_id=business_id,
            ingredient__business_id=business_id,
        ).values_list("pk", "ingredient_id", "standard_quantity", "unit")
        requirement_ids = set()
        for requirement_id, ingredient_id, quantity, unit in requirements:
            requirement_ids.add(requirement_id)
            previous, previous_unit = expected.get(ingredient_id, (Decimal("0"), unit))
            if previous_unit != unit:
                return False
            expected[ingredient_id] = (previous + Decimal(quantity), unit)
        if not expected:
            return False

        consumption_lines = OrderInventoryConsumptionLine.objects.filter(
            consumption__business_id=business_id,
            consumption__order_id=order_id,
            requirement_id__in=requirement_ids,
        ).select_related("requirement")
        for line in consumption_lines:
            ingredient_id = line.requirement.ingredient_id
            current, unit = expected.get(ingredient_id, (Decimal("0"), line.unit))
            if unit != line.unit:
                return False
            expected[ingredient_id] = (current - Decimal(line.actual_quantity), unit)

        remaining = {key: value for key, value in expected.items() if value[0] > 0}
        provided = {}
        for line in lines:
            if line.ingredient_id in provided:
                return False
            provided[line.ingredient_id] = (line.quantity.amount, line.quantity.unit.value)
        return provided == {key: (value[0], value[1]) for key, value in remaining.items()}
