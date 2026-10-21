import assert from "node:assert/strict";
import test from "node:test";
import {meMapper} from "./meMapper.ts";

const response = (permissionsMarker) => {
    const activeBusiness = {
        id: 1,
        name: "Test business",
        role: "ACCOUNTANT",
        slug: "test-business",
    };
    if (permissionsMarker !== "missing") {
        activeBusiness.permissions = permissionsMarker;
    }
    return {
        id: 1,
        email: "accountant@example.com",
        name: "Test Accountant",
        number: "1",
        has_business: true,
        memberships: [],
        active_business: activeBusiness,
        meta: {needs_onboarding: false, business_count: 1},
    };
};

test("missing permissions normalize to an empty array", () => {
    assert.deepEqual(meMapper(response("missing")).active_business.permissions, []);
});

test("null permissions normalize to an empty array", () => {
    assert.deepEqual(meMapper(response(null)).active_business.permissions, []);
});

test("valid permissions are preserved", () => {
    assert.deepEqual(
        meMapper(response(["payments.manage"])).active_business.permissions,
        ["payments.manage"],
    );
});
