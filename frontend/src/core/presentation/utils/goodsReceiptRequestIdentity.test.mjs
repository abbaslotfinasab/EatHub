import assert from "node:assert/strict";
import test from "node:test";
import { clearGoodsReceiptRequestIdentity, getOrCreateGoodsReceiptRequestIdentity, listGoodsReceiptRequestIdentities } from "./goodsReceiptRequestIdentity.ts";
class MemoryStorage {
    values = new Map();
    getItem(key) { return this.values.get(key) ?? null; }
    setItem(key, value) { this.values.set(key, value); }
}
test("reuses the same identity after a page reload", () => {
    const storage = new MemoryStorage();
    let generated = 0;
    const createKey = () => "key-" + (++generated);
    const first = getOrCreateGoodsReceiptRequestIdentity("payload-a", storage, createKey, () => new Date("2026-11-11T10:00:00.000Z"));
    const reloaded = getOrCreateGoodsReceiptRequestIdentity("payload-a", storage, createKey, () => new Date("2026-11-11T10:05:00.000Z"));
    assert.deepEqual(reloaded, first);
    assert.equal(generated, 1);
});
test("creates a different identity for a changed payload", () => {
    const storage = new MemoryStorage();
    let generated = 0;
    const createKey = () => "key-" + (++generated);
    const first = getOrCreateGoodsReceiptRequestIdentity("payload-a", storage, createKey);
    const second = getOrCreateGoodsReceiptRequestIdentity("payload-b", storage, createKey);
    assert.notEqual(first.key, second.key);
    assert.equal(generated, 2);
});
test("clears only the completed identity", () => {
    const storage = new MemoryStorage();
    let generated = 0;
    const createKey = () => "key-" + (++generated);
    const first = getOrCreateGoodsReceiptRequestIdentity("payload-a", storage, createKey);
    const second = getOrCreateGoodsReceiptRequestIdentity("payload-b", storage, createKey);
    clearGoodsReceiptRequestIdentity("payload-a", storage);
    assert.equal(getOrCreateGoodsReceiptRequestIdentity("payload-b", storage, createKey).key, second.key);
    assert.notEqual(getOrCreateGoodsReceiptRequestIdentity("payload-a", storage, createKey).key, first.key);
});
test("replaces malformed persisted state", () => {
    const storage = new MemoryStorage();
    storage.setItem("eathub:goods-receipt-request-identities:v1", "{broken");
    assert.equal(getOrCreateGoodsReceiptRequestIdentity("payload", storage, () => "fresh-key").key, "fresh-key");
});

test("lists pending identities so a page can recover an uncertain request", () => {
    const storage = new MemoryStorage();
    const identity = getOrCreateGoodsReceiptRequestIdentity("payload-a", storage, () => "pending-key");
    assert.deepEqual(listGoodsReceiptRequestIdentities(storage), [identity]);
});
