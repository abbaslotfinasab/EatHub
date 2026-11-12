import type {
    PurchaseRequisition,
    RequisitionDecision,
    RequisitionOrderSummary,
    RequisitionStatus,
} from '../../entities/inventory/PurchaseRequisition.ts';

export interface PurchaseRequisitionRepository {
    list(status?: RequisitionStatus): Promise<PurchaseRequisition[]>;
    get(id: string): Promise<PurchaseRequisition>;
    getOrderSummary(id: string): Promise<RequisitionOrderSummary>;
    getDecisions(id: string): Promise<RequisitionDecision[]>;
}
