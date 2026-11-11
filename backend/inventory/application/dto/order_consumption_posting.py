from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrderConsumptionPostingDTO:
    operation_id: int
    movement_ids_by_ingredient: dict[int, int]
