import type { PurchaseSupplierInput } from '../../../entities/inventory/PurchaseSupplier.ts';
import type { PurchaseSupplierRepository } from '../../../repositories/inventory/PurchaseSupplierRepository.ts';

const validateInput = (input: PurchaseSupplierInput) => {
    if (input.name.trim().length < 2) throw new Error('نام تأمین‌کننده حداقل ۲ کاراکتر است.');
    if (input.phone.trim() && input.phone.trim().length < 5) throw new Error('شماره تلفن معتبر نیست.');
    if (input.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.email.trim())) {
        throw new Error('ایمیل معتبر نیست.');
    }
};

export class ListPurchaseSuppliers {
    constructor(private readonly repository: PurchaseSupplierRepository) {}
    execute(filters?: { search?: string; isActive?: boolean }) {
        return this.repository.list(filters);
    }
}

export class CreatePurchaseSupplier {
    constructor(private readonly repository: PurchaseSupplierRepository) {}
    execute(input: PurchaseSupplierInput) {
        validateInput(input);
        return this.repository.create(input);
    }
}

export class UpdatePurchaseSupplier {
    constructor(private readonly repository: PurchaseSupplierRepository) {}
    execute(id: string, input: PurchaseSupplierInput) {
        if (!/^\d+$/.test(id) || Number(id) <= 0) throw new Error('شناسه تأمین‌کننده معتبر نیست.');
        validateInput(input);
        return this.repository.update(id, input);
    }
}
