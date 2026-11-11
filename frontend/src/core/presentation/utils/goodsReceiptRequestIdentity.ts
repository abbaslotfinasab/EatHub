export type GoodsReceiptRequestIdentity = { fingerprint: string; key: string; receivedDate: string };
export interface GoodsReceiptIdentityStorage { getItem(key: string): string | null; setItem(key: string, value: string): void; }
const STORAGE_KEY = 'eathub:goods-receipt-request-identities:v1';
const readIdentities = (storage: GoodsReceiptIdentityStorage): Record<string, GoodsReceiptRequestIdentity> => {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return {};
    try {
        const parsed: unknown = JSON.parse(raw);
        if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {};
        return parsed as Record<string, GoodsReceiptRequestIdentity>;
    } catch { return {}; }
};
export const getOrCreateGoodsReceiptRequestIdentity = (fingerprint: string, storage: GoodsReceiptIdentityStorage, createKey: () => string, now: () => Date = () => new Date()): GoodsReceiptRequestIdentity => {
    if (!fingerprint) throw new Error('شناسه محتوای درخواست دریافت خالی است.');
    const identities = readIdentities(storage);
    const existing = identities[fingerprint];
    if (existing && existing.fingerprint === fingerprint && typeof existing.key === 'string' && existing.key.length > 0 && typeof existing.receivedDate === 'string' && !Number.isNaN(Date.parse(existing.receivedDate))) return existing;
    const identity = { fingerprint, key: createKey(), receivedDate: now().toISOString() };
    if (!identity.key) throw new Error('ساخت شناسه امن برای درخواست ممکن نیست.');
    identities[fingerprint] = identity;
    storage.setItem(STORAGE_KEY, JSON.stringify(identities));
    return identity;
};
export const clearGoodsReceiptRequestIdentity = (fingerprint: string, storage: GoodsReceiptIdentityStorage): void => {
    const identities = readIdentities(storage);
    if (!(fingerprint in identities)) return;
    delete identities[fingerprint];
    storage.setItem(STORAGE_KEY, JSON.stringify(identities));
};

export const listGoodsReceiptRequestIdentities = (storage: GoodsReceiptIdentityStorage): GoodsReceiptRequestIdentity[] =>
    Object.values(readIdentities(storage)).filter((identity) =>
        Boolean(identity)
        && typeof identity.fingerprint === 'string'
        && typeof identity.key === 'string'
        && typeof identity.receivedDate === 'string'
    );
