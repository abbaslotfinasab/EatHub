export type RequisitionStatusDTO = 'draft' | 'submitted' | 'approved' | 'rejected' | 'completed';

export interface RequisitionItemReadDTO {
    ingredient_id: number;
    quantity: string;
    note: string;
}

export interface RequisitionReadDTO {
    id: number;
    business_id: number;
    requested_by_id: number;
    status: RequisitionStatusDTO;
    reason: string;
    items: RequisitionItemReadDTO[];
    created_at: string;
    updated_at: string;
}

export interface RequisitionOrderSummaryItemDTO {
    ingredient_id: number;
    requested_quantity: string;
    ordered_quantity: string;
    remaining_quantity: string;
}

export interface RequisitionOrderSummaryDTO {
    requisition_id: number;
    business_id: number;
    status: RequisitionStatusDTO;
    items: RequisitionOrderSummaryItemDTO[];
}

export interface RequisitionDecisionDTO {
    decision: string;
    actor_id: number;
    actor_name: string;
    decided_at: string;
    previous_status: RequisitionStatusDTO;
    resulting_status: RequisitionStatusDTO;
    rejection_reason: string | null;
}
