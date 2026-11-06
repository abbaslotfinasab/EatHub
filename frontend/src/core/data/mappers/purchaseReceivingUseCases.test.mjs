import assert from "node:assert/strict";
import test from "node:test";
import {
    CreatePurchaseOrder,
    UpdatePurchaseOrder,
    SendPurchaseOrder,
    CancelPurchaseOrder,
} from "../../domain/use-cases/inventory/purchase/PurchaseReceivingUseCases.ts";

const makeRepository = () => {
    const calls = [];
    const result = { id: "41", status: "draft", items: [{ id: "1" }] };
    return {
        calls,
        result,
        createOrder: async (input) => { calls.push(["createOrder", input]); return result; },
        updateOrder: async (id, input) => { calls.push(["updateOrder", id, input]); return result; },
        sendOrder: async (id) => { calls.push(["sendOrder", id]); return { ...result, status: "sent" }; },
        cancelOrder: async (id) => { calls.push(["cancelOrder", id]); return { ...result, status: "cancelled" }; },
    };
};

test("create purchase order forwards supplier, dates, totals and every line", async () => {
    const repository = makeRepository();
    const input = {
        supplierId: "8",
        orderDate: "2026-11-06",
        expectedDate: "2026-11-10",
        discount: "2.00",
        tax: "1.50",
        items: [
            { ingredientId: "12", quantity: "2.500", unitPrice: "30.00", purchaseUnit: "kg" },
            { ingredientId: "13", quantity: "4", unitPrice: "5.25", purchaseUnit: "pc" },
        ],
    };

    const result = await new CreatePurchaseOrder(repository).execute(input);

    assert.equal(result.id, "41");
    assert.deepEqual(repository.calls, [["createOrder", input]]);
});

test("create rejects an empty order without calling the repository", () => {
    const repository = makeRepository();
    assert.throws(
        () => new CreatePurchaseOrder(repository).execute({ items: [] }),
        /حداقل یک قلم/,
    );
    assert.deepEqual(repository.calls, []);
});

test("update draft forwards the order id and replacement lines", async () => {
    const repository = makeRepository();
    const input = {
        discount: "3.00",
        tax: "0.00",
        items: [{ ingredientId: "12", quantity: "3", unitPrice: "12.50", purchaseUnit: "kg" }],
    };

    await new UpdatePurchaseOrder(repository).execute("41", input);

    assert.deepEqual(repository.calls, [["updateOrder", "41", input]]);
});

test("update rejects invalid identifiers and empty line collections", () => {
    const repository = makeRepository();
    const useCase = new UpdatePurchaseOrder(repository);

    assert.throws(() => useCase.execute("0", { items: [{}] }), /شناسه سفارش خرید معتبر نیست/);
    assert.throws(() => useCase.execute("invalid", { items: [{}] }), /شناسه سفارش خرید معتبر نیست/);
    assert.throws(() => useCase.execute("41", { items: [] }), /حداقل یک قلم/);
    assert.deepEqual(repository.calls, []);
});

test("send purchase order calls the send transition for the requested order", async () => {
    const repository = makeRepository();

    const result = await new SendPurchaseOrder(repository).execute("41");

    assert.equal(result.status, "sent");
    assert.deepEqual(repository.calls, [["sendOrder", "41"]]);
});

test("cancel purchase order calls the cancel transition for the requested order", async () => {
    const repository = makeRepository();

    const result = await new CancelPurchaseOrder(repository).execute("41");

    assert.equal(result.status, "cancelled");
    assert.deepEqual(repository.calls, [["cancelOrder", "41"]]);
});
