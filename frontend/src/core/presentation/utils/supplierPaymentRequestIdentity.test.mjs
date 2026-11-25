import assert from "node:assert/strict";
import test from "node:test";
import {
    clearPendingSupplierPayment,
    readPendingSupplierPayment,
    savePendingSupplierPayment,
    supplierPaymentFingerprint,
} from "./supplierPaymentRequestIdentity.ts";

class MemoryStorage {
    values = new Map();
    getItem(key) { return this.values.get(key) ?? null; }
    setItem(key, value) { this.values.set(key, value); }
    removeItem(key) { this.values.delete(key); }
}

const input = {
    supplierId: "supplier-17",
    amount: "125.5",
    paymentDate: "2026-11-25",
    method: "bank_transfer",
};
const businessId = "business-9";
const key = "b63d44c4-c6ab-4b53-b8b4-2e6f8c4e81b1";
const storageKey = `eathub.purchase.supplier-payment.pending.v1.${businessId}`;

function request(overrides = {}) {
    const value = {...input, ...overrides};
    return {
        businessId,
        fingerprint: supplierPaymentFingerprint(businessId, value),
        key,
        input: value,
    };
}

test("pending payment identity survives reload with the same key and exact payload", () => {
    const storage = new MemoryStorage();
    const pending = request();
    savePendingSupplierPayment(pending, storage);

    const restored = readPendingSupplierPayment(businessId, storage);

    assert.deepEqual(restored, pending);
    assert.equal(restored.key, key);
    assert.deepEqual(restored.input, input);
});

test("retry uses a stable fingerprint for equivalent decimal representations", () => {
    assert.equal(
        supplierPaymentFingerprint(businessId, {...input, amount: "125.5"}),
        supplierPaymentFingerprint(businessId, {...input, amount: "125.50"}),
    );
    assert.equal(
        supplierPaymentFingerprint(businessId, {...input, amount: "125"}),
        supplierPaymentFingerprint(businessId, {...input, amount: "125.00"}),
    );
});

test("fingerprint changes when business, supplier, amount, date, or method changes", () => {
    const baseline = supplierPaymentFingerprint(businessId, input);
    assert.notEqual(supplierPaymentFingerprint("business-10", input), baseline);
    assert.notEqual(supplierPaymentFingerprint(businessId, {...input, supplierId: "supplier-18"}), baseline);
    assert.notEqual(supplierPaymentFingerprint(businessId, {...input, amount: "125.51"}), baseline);
    assert.notEqual(supplierPaymentFingerprint(businessId, {...input, paymentDate: "2026-11-26"}), baseline);
    assert.notEqual(supplierPaymentFingerprint(businessId, {...input, method: "cash"}), baseline);
});

test("tampered persisted payload is rejected and removed instead of reusing its key", () => {
    const storage = new MemoryStorage();
    savePendingSupplierPayment(request(), storage);
    storage.setItem(storageKey, JSON.stringify({
        ...request(),
        input: {...input, amount: "999.00"},
    }));

    assert.equal(readPendingSupplierPayment(businessId, storage), null);
    assert.equal(storage.getItem(storageKey), null);
});

test("malformed persisted JSON is cleared safely", () => {
    const storage = new MemoryStorage();
    storage.setItem(storageKey, "{broken-json");

    assert.equal(readPendingSupplierPayment(businessId, storage), null);
    assert.equal(storage.getItem(storageKey), null);
});

test("saving a request with a mismatched fingerprint is rejected", () => {
    const storage = new MemoryStorage();
    const pending = request();
    pending.input = {...pending.input, amount: "126.00"};

    assert.throws(
        () => savePendingSupplierPayment(pending, storage),
        /محتوای درخواست پرداخت/,
    );
    assert.equal(storage.getItem(storageKey), null);
});

test("clearing a completed payment removes only that business identity", () => {
    const storage = new MemoryStorage();
    const first = request();
    const secondBusinessId = "business-10";
    const secondInput = {...input, supplierId: "supplier-99"};
    const second = {
        businessId: secondBusinessId,
        fingerprint: supplierPaymentFingerprint(secondBusinessId, secondInput),
        key: "second-key",
        input: secondInput,
    };
    savePendingSupplierPayment(first, storage);
    savePendingSupplierPayment(second, storage);

    clearPendingSupplierPayment(businessId, storage);

    assert.equal(readPendingSupplierPayment(businessId, storage), null);
    assert.deepEqual(readPendingSupplierPayment(secondBusinessId, storage), second);
});
