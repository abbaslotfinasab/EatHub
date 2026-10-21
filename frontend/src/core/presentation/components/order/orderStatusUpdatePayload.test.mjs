import assert from "node:assert/strict";
import test from "node:test";
import {
    buildOrderStatusUpdatePayload,
    getOrderStatusControlState,
    hasPermission,
} from "./orderStatusUpdatePayload.ts";

test("orders.update renders the status control enabled", () => {
    assert.deepEqual(
        getOrderStatusControlState(["orders.update"]),
        {visible: true, disabled: false},
    );
});

test("missing and null permissions keep the status control visible but disabled", () => {
    assert.deepEqual(getOrderStatusControlState(undefined), {
        visible: true,
        disabled: true,
        helperText: "برای تغییر وضعیت سفارش، مجوز orders.update لازم است.",
    });
    assert.equal(getOrderStatusControlState(null).visible, true);
    assert.equal(getOrderStatusControlState(null).disabled, true);
});

test("unrecognized permission data does not grant order updates", () => {
    assert.equal(getOrderStatusControlState("orders.update").disabled, true);
    assert.equal(getOrderStatusControlState({permissions: ["orders.update"]}).disabled, true);
    assert.equal(hasPermission(["orders.update-extra"], "orders.update"), false);
});

test("order viewing and permitted payment edits remain available without status permission", () => {
    const permissions = ["orders.view", "payments.manage"];
    assert.equal(getOrderStatusControlState(permissions).visible, true);
    assert.equal(getOrderStatusControlState(permissions).disabled, true);
    assert.equal(hasPermission(permissions, "orders.view"), true);
    assert.deepEqual(
        buildOrderStatusUpdatePayload(
            {status: "ready", paymentStatus: "paid"},
            {status: true, paymentStatus: true},
            {canUpdateOrders: false, canManagePayments: true},
        ),
        {paymentStatus: "paid"},
    );
});

test("accountant payload includes payment edits and excludes unauthorized status", () => {
    assert.deepEqual(
        buildOrderStatusUpdatePayload(
            {status: "ready", paymentStatus: "paid", paymentMethod: "cash"},
            {status: true, paymentStatus: true, paymentMethod: true},
            {canUpdateOrders: false, canManagePayments: true},
        ),
        {paymentStatus: "paid", paymentMethod: "cash"},
    );
});

test("status permission does not include untouched payment fields", () => {
    assert.deepEqual(
        buildOrderStatusUpdatePayload(
            {status: "ready", paymentStatus: "pending", paymentMethod: "cash"},
            {status: true},
            {canUpdateOrders: true, canManagePayments: false},
        ),
        {status: "ready"},
    );
});

test("payment fields are omitted when payment permission is absent, even when dirty", () => {
    assert.deepEqual(
        buildOrderStatusUpdatePayload(
            {status: "ready", paymentStatus: "paid", paymentMethod: "cash"},
            {status: true, paymentStatus: true, paymentMethod: true},
            {canUpdateOrders: true, canManagePayments: false},
        ),
        {status: "ready"},
    );
});

test("combined changes omit status when order permission is absent", () => {
    assert.deepEqual(
        buildOrderStatusUpdatePayload(
            {status: "ready", paymentStatus: "paid", paymentMethod: "cash"},
            {status: true, paymentStatus: true, paymentMethod: true},
            {canUpdateOrders: false, canManagePayments: true},
        ),
        {paymentStatus: "paid", paymentMethod: "cash"},
    );
});
