import assert from "node:assert/strict";
import test from "node:test";
import {orderMapper} from "./orderMapper.ts";

test("create-order mapper includes the caller's idempotency key", () => {
    const domain = {
        order: {
            customerId: 42,
            tableId: null,
            orderType: "takeaway",
            notes: "No onions",
        },
        orderItems: [
            {
                menuItemId: 7,
                quantity: 2,
                notes: "",
            },
        ],
    };

    const dto = orderMapper.toCreateDTO(domain, "d4ad13d4-45c4-4b3f-9a7e-3fbefb7b04f1");

    assert.equal(dto.idempotency_key, "d4ad13d4-45c4-4b3f-9a7e-3fbefb7b04f1");
    assert.equal(dto.items.length, 1);
    assert.equal(dto.items[0].menu_item_id, 7);
});
