import type { CreateSupplierPaymentInput } from '../../domain/entities/inventory/SupplierPayment.ts';

export interface PendingSupplierPaymentRequest {
    businessId: string;
    fingerprint: string;
    key: string;
    input: CreateSupplierPaymentInput;
}

export interface SupplierPaymentIdentityStorage {
    getItem(key: string): string | null;
    setItem(key: string, value: string): void;
    removeItem(key: string): void;
}

const storageKey = (businessId: string) => `eathub.purchase.supplier-payment.pending.v1.${businessId}`;

const canonicalAmount = (value: string): string => {
    const match = /^(0|[1-9]\\d*)(?:\\.(\\d{1,2}))?$/.exec(value.trim());
    return match ? match[1] + "." + (match[2] ?? "").padEnd(2, "0") : value.trim();
};

export const supplierPaymentFingerprint = (businessId: string, input: CreateSupplierPaymentInput): string =>
    JSON.stringify({
        businessId,
        supplierId: input.supplierId,
        amount: canonicalAmount(input.amount),
        paymentDate: input.paymentDate,
        method: input.method,
    });

export const readPendingSupplierPayment = (
    businessId: string,
    storage: SupplierPaymentIdentityStorage,
): PendingSupplierPaymentRequest | null => {
    const raw = storage.getItem(storageKey(businessId));
    if (!raw) return null;
    try {
        const parsed = JSON.parse(raw) as PendingSupplierPaymentRequest;
        if (
            parsed.businessId !== businessId
            || typeof parsed.key !== 'string'
            || !parsed.key
            || !parsed.input
            || parsed.fingerprint !== supplierPaymentFingerprint(businessId, parsed.input)
        ) {
            storage.removeItem(storageKey(businessId));
            return null;
        }
        return parsed;
    } catch {
        storage.removeItem(storageKey(businessId));
        return null;
    }
};

export const savePendingSupplierPayment = (
    request: PendingSupplierPaymentRequest,
    storage: SupplierPaymentIdentityStorage,
): void => {
    if (request.fingerprint !== supplierPaymentFingerprint(request.businessId, request.input)) {
        throw new Error('محتوای درخواست پرداخت با شناسه آن مطابقت ندارد.');
    }
    storage.setItem(storageKey(request.businessId), JSON.stringify(request));
};

export const clearPendingSupplierPayment = (
    businessId: string,
    storage: SupplierPaymentIdentityStorage,
): void => {
    storage.removeItem(storageKey(businessId));
};
