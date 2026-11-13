import assert from "node:assert/strict";
import test from "node:test";
import {
    clearPendingOrderConsumption,
    createPendingOrderConsumptionRequest,
    orderConsumptionFingerprint,
    readPendingOrderConsumption,
    savePendingOrderConsumption,
} from "./orderConsumptionRequestIdentity.ts";

function memoryStorage() {
    const values = new Map();
    return {
        getItem: (key) => values.get(key) ?? null,
        setItem: (key, value) => values.set(key, value),
        removeItem: (key) => values.delete(key),
        values,
    };
}

const lines = [
    {requirementId: 12, quantity: "1.250", unit: "kg"},
    {requirementId: 4, quantity: "0", unit: "pc"},
];
const key = "d4ad13d4-45c4-4b3f-9a7e-3fbefb7b04f1";

test("pending consumption identity survives reload with the exact same key and payload", () => {
    const storage = memoryStorage();
    const request = createPendingOrderConsumptionRequest("9", "42", lines, key);
    savePendingOrderConsumption(request, storage);

    const restored = readPendingOrderConsumption("9", "42", storage);

    assert.deepEqual(restored, request);
    assert.equal(restored.key, key);
    assert.deepEqual(restored.lines, [
        {requirementId: 4, quantity: "0", unit: "pc"},
        {requirementId: 12, quantity: "1.250", unit: "kg"},
    ]);
});

test("pending requests are isolated by both business and order", () => {
    const storage = memoryStorage();
    savePendingOrderConsumption(
        createPendingOrderConsumptionRequest("9", "42", lines, key),
        storage,
    );

    assert.equal(readPendingOrderConsumption("10", "42", storage), null);
    assert.equal(readPendingOrderConsumption("9", "43", storage), null);
});

test("fingerprint is stable when requirement lines arrive in a different order", () => {
    assert.equal(
        orderConsumptionFingerprint("9", "42", lines),
        orderConsumptionFingerprint("9", "42", [...lines].reverse()),
    );
});

test("tampered stored payload is rejected instead of silently generating a new key", () => {
    const storage = memoryStorage();
    const request = createPendingOrderConsumptionRequest("9", "42", lines, key);
    savePendingOrderConsumption(request, storage);
    const storedKey = "eathub:pending-order-consumption:9:42";
    const tampered = {...request, lines: [{requirementId: 4, quantity: "2", unit: "pc"}]};
    storage.setItem(storedKey, JSON.stringify(tampered));

    assert.throws(() => readPendingOrderConsumption("9", "42", storage));
    assert.equal(storage.values.has(storedKey), true);
});

test("clearing a completed request removes only that business/order identity", () => {
    const storage = memoryStorage();
    savePendingOrderConsumption(
        createPendingOrderConsumptionRequest("9", "42", lines, key),
        storage,
    );
    clearPendingOrderConsumption("9", "42", storage);
    assert.equal(readPendingOrderConsumption("9", "42", storage), null);
});
