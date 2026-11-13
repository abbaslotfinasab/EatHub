export interface OrderConsumptionLineIdentity {
    requirementId: number;
    quantity: string;
    unit: string;
}

export interface PendingOrderConsumptionRequest {
    businessId: string;
    orderId: string;
    fingerprint: string;
    key: string;
    lines: OrderConsumptionLineIdentity[];
}

export interface SessionStorageLike {
    getItem(key: string): string | null;
    setItem(key: string, value: string): void;
    removeItem(key: string): void;
}

const storageKey = (businessId: string, orderId: string) =>
    `eathub:pending-order-consumption:${businessId}:${orderId}`;

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function orderConsumptionFingerprint(
    businessId: string,
    orderId: string,
    lines: OrderConsumptionLineIdentity[],
): string {
    const canonicalLines = [...lines]
        .map((line) => ({
            requirementId: line.requirementId,
            quantity: line.quantity.trim(),
            unit: line.unit,
        }))
        .sort((left, right) => left.requirementId - right.requirementId);
    return JSON.stringify([businessId, orderId, canonicalLines]);
}

export function createPendingOrderConsumptionRequest(
    businessId: string,
    orderId: string,
    lines: OrderConsumptionLineIdentity[],
    key: string,
): PendingOrderConsumptionRequest {
    if (!businessId || !orderId || !uuidPattern.test(key)) {
        throw new Error("Invalid order-consumption request identity.");
    }
    const normalizedLines = [...lines]
        .map((line) => ({
            requirementId: line.requirementId,
            quantity: line.quantity.trim(),
            unit: line.unit,
        }))
        .sort((left, right) => left.requirementId - right.requirementId);
    if (
        normalizedLines.length === 0
        || normalizedLines.some((line) =>
            !Number.isSafeInteger(line.requirementId)
            || line.requirementId <= 0
            || !line.quantity
            || !line.unit
        )
    ) {
        throw new Error("Invalid order-consumption request lines.");
    }
    return {
        businessId,
        orderId,
        fingerprint: orderConsumptionFingerprint(businessId, orderId, normalizedLines),
        key,
        lines: normalizedLines,
    };
}

export function savePendingOrderConsumption(
    request: PendingOrderConsumptionRequest,
    storage: SessionStorageLike,
): void {
    storage.setItem(storageKey(request.businessId, request.orderId), JSON.stringify(request));
}

export function readPendingOrderConsumption(
    businessId: string,
    orderId: string,
    storage: SessionStorageLike,
): PendingOrderConsumptionRequest | null {
    const raw = storage.getItem(storageKey(businessId, orderId));
    if (!raw) return null;
    const value = JSON.parse(raw) as PendingOrderConsumptionRequest;
    if (
        value.businessId !== businessId
        || value.orderId !== orderId
        || !uuidPattern.test(value.key)
        || !Array.isArray(value.lines)
        || value.lines.length === 0
        || value.fingerprint !== orderConsumptionFingerprint(businessId, orderId, value.lines)
    ) {
        throw new Error("Stored order-consumption request identity is invalid.");
    }
    return value;
}

export function clearPendingOrderConsumption(
    businessId: string,
    orderId: string,
    storage: SessionStorageLike,
): void {
    storage.removeItem(storageKey(businessId, orderId));
}
