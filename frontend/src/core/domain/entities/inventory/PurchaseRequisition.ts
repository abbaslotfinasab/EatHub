export type RequisitionStatus = 'draft' | 'submitted' | 'approved' | 'rejected' | 'completed';

export interface RequisitionItem {
    ingredientId: string;
    quantity: string;
    note: string;
}

export interface RequisitionInput {
    reason: string;
    items: RequisitionItem[];
}

export interface PurchaseRequisition {
    id: string;
    businessId: string;
    requestedById: string;
    status: RequisitionStatus;
    reason: string;
    items: RequisitionItem[];
    createdAt: string;
    updatedAt: string;
}

export interface RequisitionOrderSummaryItem {
    ingredientId: string;
    requestedQuantity: string;
    orderedQuantity: string;
    remainingQuantity: string;
}

export interface RequisitionOrderSummary {
    requisitionId: string;
    businessId: string;
    status: RequisitionStatus;
    items: RequisitionOrderSummaryItem[];
}

export interface RequisitionDecision {
    decision: string;
    actorId: string;
    actorName: string;
    decidedAt: string;
    previousStatus: RequisitionStatus;
    resultingStatus: RequisitionStatus;
    rejectionReason: string | null;
}
