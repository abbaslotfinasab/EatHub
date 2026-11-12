import type { PurchaseRequisitionRepository } from '../../../repositories/inventory/PurchaseRequisitionRepository.ts';
import type { RequisitionStatus } from '../../../entities/inventory/PurchaseRequisition.ts';

const validateId = (id: string) => {
    if (!/^\\d+$/.test(id) || Number(id) <= 0) {
        throw new Error('شناسه درخواست خرید معتبر نیست.');
    }
};

export class ListPurchaseRequisitions {
    constructor(private readonly repository: PurchaseRequisitionRepository) {}
    execute(status?: RequisitionStatus) {
        return this.repository.list(status);
    }
}

export class GetPurchaseRequisition {
    constructor(private readonly repository: PurchaseRequisitionRepository) {}
    execute(id: string) {
        validateId(id);
        return this.repository.get(id);
    }
}

export class GetPurchaseRequisitionOrderSummary {
    constructor(private readonly repository: PurchaseRequisitionRepository) {}
    execute(id: string) {
        validateId(id);
        return this.repository.getOrderSummary(id);
    }
}

export class GetPurchaseRequisitionDecisions {
    constructor(private readonly repository: PurchaseRequisitionRepository) {}
    execute(id: string) {
        validateId(id);
        return this.repository.getDecisions(id);
    }
}
