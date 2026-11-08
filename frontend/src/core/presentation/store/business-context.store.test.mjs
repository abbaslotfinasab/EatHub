import test from "node:test";
import assert from "node:assert/strict";

const values = new Map();
globalThis.sessionStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
};

const { useBusinessContextStore, getBusinessRequestSignal } = await import(
    "../../store/business-context.store.ts"
);

test("business selection is persisted in this tab's session storage", () => {
    useBusinessContextStore.getState().selectBusiness(42);
    assert.equal(useBusinessContextStore.getState().selectedBusinessId, 42);
    assert.equal(values.get("eathub.selectedBusinessId"), "42");
});

test("switching business aborts requests from the previous context", () => {
    const previousSignal = getBusinessRequestSignal();
    useBusinessContextStore.getState().selectBusiness(84);
    assert.equal(previousSignal.aborted, true);
    assert.equal(getBusinessRequestSignal().aborted, false);
    assert.equal(useBusinessContextStore.getState().selectedBusinessId, 84);
});

test("clearing business removes the tab selection", () => {
    useBusinessContextStore.getState().clearBusiness();
    assert.equal(useBusinessContextStore.getState().selectedBusinessId, null);
    assert.equal(values.has("eathub.selectedBusinessId"), false);
});

test("invalid business identifiers are rejected", () => {
    assert.throws(
        () => useBusinessContextStore.getState().selectBusiness(0),
        /Invalid business id/,
    );
});
