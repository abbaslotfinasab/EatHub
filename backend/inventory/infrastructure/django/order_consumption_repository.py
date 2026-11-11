from inventory.application.dto.order_consumption_posting import OrderConsumptionPostingDTO
from inventory.application.exceptions import InvalidApplicationInput, OperationConflict
from inventory.infrastructure.django.models import (
    InventoryOperation,
    InventoryOperationLine,
    InventoryV1StockMovement,
)
from inventory.infrastructure.django.operations_service import (
    OperationInputError,
    create_operation,
    post_issue,
)


class DjangoOrderConsumptionPostingRepository:
    def post_order_issue(
        self,
        context,
        *,
        warehouse_id: int,
        order_id: int,
        consumption_id: int,
        lines: list[dict],
    ) -> OrderConsumptionPostingDTO:
        try:
            operation = create_operation(
                business_id=context.business_id,
                actor_id=context.actor_id,
                operation_type=InventoryOperation.Type.ISSUE,
                warehouse_id=warehouse_id,
                reference=f"Order {order_id}",
                reason=f"Actual consumption for order {order_id}",
                notes=f"OrderInventoryConsumption:{consumption_id}",
                lines=lines,
            )
            post_issue(
                business_id=context.business_id,
                actor_id=context.actor_id,
                operation_id=operation.pk,
            )
        except OperationInputError as error:
            raise InvalidApplicationInput(str(error)) from error

        operation_lines = list(
            InventoryOperationLine.objects.filter(operation_id=operation.pk)
            .order_by("ingredient_id")
            .values_list("pk", "ingredient_id")
        )
        movements = dict(
            InventoryV1StockMovement.objects.filter(
                business_id=context.business_id,
                source_type="inventory_issue",
                source_document_id=operation.pk,
                source_line_id__in=[line_id for line_id, _ingredient_id in operation_lines],
                operation_kind="post",
            ).values_list("source_line_id", "pk")
        )
        movement_ids_by_ingredient = {}
        for line_id, ingredient_id in operation_lines:
            movement_id = movements.get(line_id)
            if movement_id is None:
                raise OperationConflict("A posted order issue is missing its stock movement.")
            movement_ids_by_ingredient[ingredient_id] = movement_id
        return OrderConsumptionPostingDTO(
            operation_id=operation.pk,
            movement_ids_by_ingredient=movement_ids_by_ingredient,
        )
