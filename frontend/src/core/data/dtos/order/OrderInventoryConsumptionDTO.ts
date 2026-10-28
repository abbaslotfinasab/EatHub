export interface OrderConsumptionRequirementDTO {
    requirement_id: number;
    order_item_id: number;
    menu_item_name: string;
    ingredient_id: number;
    ingredient_name: string;
    standard_quantity: string;
    actual_quantity: string;
    unit: string;
    has_actual_record: boolean;
}

export interface OrderConsumptionRequirementsDTO {
    order_id: number;
    requirements: OrderConsumptionRequirementDTO[];
}

export interface RecordOrderConsumptionDTO {
    idempotency_key: string;
    lines: Array<{
        requirement_id: number;
        quantity: string;
        unit: string;
    }>;
}

export interface RecordOrderConsumptionResultDTO {
    id: number;
    order_id: number;
    idempotency_key: string;
    created_at: string;
    inventory_operation_id: number | null;
    lines: Array<{
        requirement_id: number;
        order_item_id: number;
        ingredient_id: number;
        actual_quantity: string;
        unit: string;
        movement_id: number | null;
    }>;
}
