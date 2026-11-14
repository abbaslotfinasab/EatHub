import assert from "node:assert/strict";
import test from "node:test";

Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
        getItem: () => null,
        setItem: () => {},
        removeItem: () => {},
    },
});

const React = await import("react");
const {renderToString} = await import("react-dom/server");
const {QueryClient, QueryClientProvider} = await import("@tanstack/react-query");
const {container} = await import("../../../data/di/container.ts");
const {useAuthStore} = await import("../../store/auth.store.ts");
const {useUpdateOrderStatus} = await import("./useUpdateOrderStatus.ts");
const {useRecordOrderConsumption} = await import("./useRecordOrderConsumption.ts");
const {orderQueryKeys} = await import("./orderQueryKeys.ts");

const originalOrderContainerDescriptor = Object.getOwnPropertyDescriptor(container, "orderContainer");

function setBusiness(userId, businessId) {
    useAuthStore.setState({
        me: userId === null ? null : {
            id: userId,
            active_business: businessId === null ? null : {id: businessId},
        },
    });
}

function renderMutationHook(hook, execute) {
    const queryClient = new QueryClient({
        defaultOptions: {mutations: {retry: false}, queries: {retry: false}},
    });
    const invalidations = [];
    const invalidateQueries = queryClient.invalidateQueries.bind(queryClient);
    queryClient.invalidateQueries = async (filters) => {
        invalidations.push(filters);
        return invalidateQueries(filters);
    };

    Object.defineProperty(container, "orderContainer", {
        configurable: true,
        value: {
            updateOrderStatusUseCase: {execute},
            recordOrderConsumptionUseCase: {execute},
        },
    });

    let mutation;
    function Probe() {
        mutation = hook();
        return null;
    }

    renderToString(
        React.createElement(
            QueryClientProvider,
            {client: queryClient},
            React.createElement(Probe),
        ),
    );

    return {mutation, queryClient, invalidations};
}

function restoreContainer() {
    if (originalOrderContainerDescriptor) {
        Object.defineProperty(container, "orderContainer", originalOrderContainerDescriptor);
    } else {
        delete container.orderContainer;
    }
}

test("status hook retains the original tenant scope when business changes during mutation", async () => {
    setBusiness(17, 42);
    let resolveMutation;
    const execute = () => new Promise((resolve) => {
        resolveMutation = resolve;
    });
    const {mutation, queryClient, invalidations} = renderMutationHook(useUpdateOrderStatus, execute);

    try {
        const pending = mutation.mutateAsync({orderId: "order-9", status: "confirmed"});
        await new Promise((resolve) => setImmediate(resolve));
        setBusiness(17, 99);
        resolveMutation({ok: true});
        await pending;

        assert.deepEqual(invalidations, [
            {queryKey: orderQueryKeys.listPrefix(17, 42)},
            {queryKey: orderQueryKeys.detail(17, 42, "order-9"), exact: true},
            {queryKey: orderQueryKeys.statusHistory(17, 42, "order-9"), exact: true},
            {queryKey: orderQueryKeys.consumption(17, 42, "order-9"), exact: true},
            {queryKey: orderQueryKeys.refund(17, 42, "order-9"), exact: true},
        ]);
        assert.ok(invalidations.every(({queryKey}) => queryKey[2] === 42));
        assert.ok(!invalidations.some(({queryKey}) => queryKey[2] === 99));
    } finally {
        queryClient.clear();
        restoreContainer();
        setBusiness(null, null);
    }
});

test("consumption hook invalidates only the scoped order detail and consumption queries", async () => {
    setBusiness(17, 42);
    const {mutation, queryClient, invalidations} = renderMutationHook(
        useRecordOrderConsumption,
        async (input) => ({...input, accepted: true}),
    );

    try {
        await mutation.mutateAsync({orderId: "order-9", idempotencyKey: "key-1", items: []});
        assert.deepEqual(invalidations, [
            {queryKey: orderQueryKeys.detail(17, 42, "order-9"), exact: true},
            {queryKey: orderQueryKeys.consumption(17, 42, "order-9"), exact: true},
        ]);
    } finally {
        queryClient.clear();
        restoreContainer();
        setBusiness(null, null);
    }
});

test("status hook performs no invalidation without a business scope", async () => {
    setBusiness(17, null);
    const {mutation, queryClient, invalidations} = renderMutationHook(
        useUpdateOrderStatus,
        async (input) => input,
    );

    try {
        await mutation.mutateAsync({orderId: "order-9", status: "confirmed"});
        assert.deepEqual(invalidations, []);
    } finally {
        queryClient.clear();
        restoreContainer();
        setBusiness(null, null);
    }
});

test("failed consumption mutation does not invalidate order queries", async () => {
    setBusiness(17, 42);
    const {mutation, queryClient, invalidations} = renderMutationHook(
        useRecordOrderConsumption,
        async () => {
            throw new Error("request failed");
        },
    );

    try {
        await assert.rejects(mutation.mutateAsync({
            orderId: "order-9",
            idempotencyKey: "key-2",
            items: [],
        }), /request failed/);
        assert.deepEqual(invalidations, []);
    } finally {
        queryClient.clear();
        restoreContainer();
        setBusiness(null, null);
    }
});
