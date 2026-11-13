import type { PurchaseRequisitionRepository } from '../../../repositories/inventory/PurchaseRequisitionRepository.ts';
import type { RequisitionInput, RequisitionStatus } from '../../../entities/inventory/PurchaseRequisition.ts';

const validateId = (id: string) => {
    if (!/^\d+$/.test(id) || Number(id) <= 0) {
        throw new Error('شناسه درخواست خرید معتبر نیست.');
    }
};

const validateInput = (input: RequisitionInput) => {
    if (!input.items.length) throw new Error('حداقل یک قلم برای درخواست خرید لازم است.');
    input.items.forEach((item, index) => {
        if (!/^\d+$/.test(item.ingredientId) || Number(item.ingredientId) <= 0) {
            throw new Error(`ماده اولیه قلم ${index + 1} را انتخاب کنید.`);
        }
        if (!/^\d+(?:\.\d{1,3})?$/.test(item.quantity) || Number(item.quantity) <= 0) {
            throw new Error(`مقدار قلم ${index + 1} باید مثبت و حداکثر سه رقم اعشار داشته باشد.`);
        }
    });
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

export class CreatePurchaseRequisition {
    constructor(private readonly repository: PurchaseRequisitionRepository) {}
    execute(input: RequisitionInput) {
        validateInput(input);
        return this.repository.create(input);
    }
}

export class SubmitPurchaseRequisition {
    constructor(private readonly repository: PurchaseRequisitionRepository) {}
    execute(id: string) {
        validateId(id);
        return this.repository.submit(id);
    }
}

export class ApprovePurchaseRequisition {
    constructor(private readonly repository: PurchaseRequisitionRepository) {}
    execute(id: string) {
        validateId(id);
        return this.repository.approve(id);
    }
}

export class RejectPurchaseRequisition {
    constructor(private readonly repository: PurchaseRequisitionRepository) {}
    execute(id: string, reason: string) {
        validateId(id);
        return this.repository.reject(id, reason.trim());
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
