import assert from "node:assert/strict";
import test from "node:test";

import {invalidateOrderQueries} from "./invalidateOrderQueries.ts";
import {orderQueryKeys} from "./orderQueryKeys.ts";

const scope = {userId: 17, businessId: 42};
const orderId = "order-9";

function queryClientSpy() {
    const calls = [];
    return {
        calls,
        invalidateQueries: async (filters) => {
            calls.push(filters);
        },
    };
}

const cases = [
    {
        mutation: "create",
        expected: [{queryKey: orderQueryKeys.listPrefix(17, 42)}],
    },
    {
        mutation: "update",
        expected: [
            {queryKey: orderQueryKeys.listPrefix(17, 42)},
            {queryKey: orderQueryKeys.detail(17, 42, orderId), exact: true},
        ],
    },
    {
        mutation: "delete",
        expected: [
            {queryKey: orderQueryKeys.listPrefix(17, 42)},
            {queryKey: orderQueryKeys.detail(17, 42, orderId), exact: true},
            {queryKey: orderQueryKeys.statusHistory(17, 42, orderId), exact: true},
            {queryKey: orderQueryKeys.consumption(17, 42, orderId), exact: true},
            {queryKey: orderQueryKeys.refund(17, 42, orderId), exact: true},
        ],
    },
    {
        mutation: "status",
        expected: [
            {queryKey: orderQueryKeys.listPrefix(17, 42)},
            {queryKey: orderQueryKeys.detail(17, 42, orderId), exact: true},
            {queryKey: orderQueryKeys.statusHistory(17, 42, orderId), exact: true},
            {queryKey: orderQueryKeys.consumption(17, 42, orderId), exact: true},
            {queryKey: orderQueryKeys.refund(17, 42, orderId), exact: true},
        ],
    },
    {
        mutation: "refund",
        expected: [
            {queryKey: orderQueryKeys.listPrefix(17, 42)},
            {queryKey: orderQueryKeys.detail(17, 42, orderId), exact: true},
            {queryKey: orderQueryKeys.statusHistory(17, 42, orderId), exact: true},
            {queryKey: orderQueryKeys.refund(17, 42, orderId), exact: true},
        ],
    },
    {
        mutation: "consumption",
        expected: [
            {queryKey: orderQueryKeys.detail(17, 42, orderId), exact: true},
            {queryKey: orderQueryKeys.consumption(17, 42, orderId), exact: true},
        ],
    },
];

for (const {mutation, expected} of cases) {
    test(`${mutation} mutation invalidates only its affected scoped queries`, async () => {
        const queryClient = queryClientSpy();

        await invalidateOrderQueries(queryClient, scope, orderId, mutation);

        assert.deepEqual(queryClient.calls, expected);
        for (const call of queryClient.calls) {
            assert.notDeepEqual(call.queryKey, orderQueryKeys.all);
            assert.equal(call.queryKey[0], "orders");
            assert.equal(call.queryKey[1], scope.userId);
            assert.equal(call.queryKey[2], scope.businessId);
        }
    });
}

test("create does not invalidate detail or subresource queries", async () => {
    const queryClient = queryClientSpy();

    await invalidateOrderQueries(queryClient, scope, undefined, "create");

    assert.deepEqual(queryClient.calls, [
        {queryKey: orderQueryKeys.listPrefix(scope.userId, scope.businessId)},
    ]);
});

test("missing business scope is a no-op", async () => {
    const queryClient = queryClientSpy();

    await invalidateOrderQueries(queryClient, {...scope, businessId: null}, orderId, "status");

    assert.deepEqual(queryClient.calls, []);
});

test("in-flight mutation retains the original business scope after a business switch", async () => {
    const queryClient = queryClientSpy();
    const capturedScope = {...scope};

    const currentScopeAfterSwitch = {userId: 17, businessId: 99};
    await invalidateOrderQueries(queryClient, capturedScope, orderId, "status");

    assert.ok(queryClient.calls.length > 0);
    assert.ok(queryClient.calls.every(({queryKey}) =>
        queryKey[1] === capturedScope.userId
        && queryKey[2] === capturedScope.businessId
        && queryKey[2] !== currentScopeAfterSwitch.businessId
    ));
});
