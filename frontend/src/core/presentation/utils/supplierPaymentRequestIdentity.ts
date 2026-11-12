export type SupplierPaymentRequestIdentity = {
    fingerprint: string;
    key: string;
    createdAt: string;
};

export interface SupplierPaymentIdentityStorage {
    getItem(key: string): string | null;
    setItem(key: string, value: string): void;
}

const STORAGE_KEY = 'eathub:supplier-payment-request-identities:v1';

const readIdentities = (storage: SupplierPaymentIdentityStorage): Record<string, SupplierPaymentRequestIdentity> => {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return {};
    try {
        const parsed: unknown = JSON.parse(raw);
        if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {};
        return parsed as Record<string, SupplierPaymentRequestIdentity>;
    } catch {
        return {};
    }
};

export const getOrCreateSupplierPaymentRequestIdentity = (
    fingerprint: string,
    storage: SupplierPaymentIdentityStorage,
    createKey: () => string,
    now: () => Date = () => new Date(),
): SupplierPaymentRequestIdentity => {
    if (!fingerprint) throw new Error('شناسه محتوای پرداخت خالی است.');
    const identities = readIdentities(storage);
    const existing = identities[fingerprint];
    if (
        existing
        && existing.fingerprint === fingerprint
        && typeof existing.key === 'string'
        && existing.key.length > 0
        && typeof existing.createdAt === 'string'
        && !Number.isNaN(Date.parse(existing.createdAt))
    ) return existing;

    const identity = { fingerprint, key: createKey(), createdAt: now().toISOString() };
    if (!identity.key) throw new Error('ساخت شناسه امن برای پرداخت ممکن نیست.');
    identities[fingerprint] = identity;
    storage.setItem(STORAGE_KEY, JSON.stringify(identities));
    return identity;
};

export const clearSupplierPaymentRequestIdentity = (
    fingerprint: string,
    storage: SupplierPaymentIdentityStorage,
): void => {
    const identities = readIdentities(storage);
    if (!(fingerprint in identities)) return;
    delete identities[fingerprint];
    storage.setItem(STORAGE_KEY, JSON.stringify(identities));
};

export const listSupplierPaymentRequestIdentities = (
    storage: SupplierPaymentIdentityStorage,
): SupplierPaymentRequestIdentity[] => Object.values(readIdentities(storage)).filter((identity) =>
    Boolean(identity)
    && typeof identity.fingerprint === 'string'
    && typeof identity.key === 'string'
    && typeof identity.createdAt === 'string'
);
