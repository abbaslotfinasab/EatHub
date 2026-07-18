import { useMemo } from "react";

import { useFieldArray } from "react-hook-form";

import type { MenuItem } from "../../../domain/entities/product/menu/MenuItem";

import { useOrderForm } from "./useOrderForm";

export const useOrderItems = () => {

    const {
        control,
        watch,
    } = useOrderForm();

    const {
        fields,
        append,
        remove,
        update,
        replace,
    } = useFieldArray({
        control,
        name: "orderItems",
    });

    const orderItems = watch("orderItems");

    // =========================
    // Exists
    // =========================

    const exists = (
        menuItemId: string,
    ) => {
        return orderItems.some(
            item =>
                item.menuItemId === menuItemId,
        );
    };

    // =========================
    // Add Item
    // =========================

    const addItem = (
        menuItem: MenuItem,
    ) => {

        const index =
            orderItems.findIndex(
                item =>
                    item.menuItemId === menuItem.id,
            );

        if (index >= 0) {

            update(index, {
                ...orderItems[index],
                quantity:
                    orderItems[index].quantity + 1,
            });

            return;
        }

        append({
            menuItemId: menuItem.id,
            quantity: 1,
            notes: null,
        });
    };

    // =========================
    // Remove Item
    // =========================

    const removeItem = (
        menuItemId: string,
    ) => {

        const index =
            orderItems.findIndex(
                item =>
                    item.menuItemId === menuItemId,
            );

        if (index >= 0) {
            remove(index);
        }

    };

    // =========================
    // Increase Quantity
    // =========================

    const increaseQuantity = (
        menuItemId: string,
    ) => {

        const index =
            orderItems.findIndex(
                item =>
                    item.menuItemId === menuItemId,
            );

        if (index < 0) return;

        update(index, {
            ...orderItems[index],
            quantity:
                orderItems[index].quantity + 1,
        });

    };

    // =========================
    // Decrease Quantity
    // =========================

    const decreaseQuantity = (
        menuItemId: string,
    ) => {

        const index =
            orderItems.findIndex(
                item =>
                    item.menuItemId === menuItemId,
            );

        if (index < 0) return;

        const quantity =
            orderItems[index].quantity - 1;

        if (quantity <= 0) {
            remove(index);
            return;
        }

        update(index, {
            ...orderItems[index],
            quantity,
        });

    };

    // =========================
    // Clear
    // =========================

    const clear = () => {
        replace([]);
    };

    // =========================
    // Helpers
    // =========================

    const totalItems = useMemo(() => {

        return orderItems.reduce(
            (sum, item) =>
                sum + item.quantity,
            0,
        );

    }, [orderItems]);

    return {

        fields,

        orderItems,

        totalItems,

        exists,

        addItem,

        removeItem,

        increaseQuantity,

        decreaseQuantity,

        clear,

    };

};