import type {
    PurchaseRequisition,
    RequisitionDecision,
    RequisitionInput,
    RequisitionOrderSummary,
    RequisitionStatus,
} from '../../entities/inventory/PurchaseRequisition.ts';

export interface PurchaseRequisitionRepository {
    list(status?: RequisitionStatus): Promise<PurchaseRequisition[]>;
    get(id: string): Promise<PurchaseRequisition>;
    create(input: RequisitionInput): Promise<PurchaseRequisition>;
    submit(id: string): Promise<PurchaseRequisition>;
    approve(id: string): Promise<PurchaseRequisition>;
    reject(id: string, reason: string): Promise<PurchaseRequisition>;
    getOrderSummary(id: string): Promise<RequisitionOrderSummary>;
    getDecisions(id: string): Promise<RequisitionDecision[]>;
}
