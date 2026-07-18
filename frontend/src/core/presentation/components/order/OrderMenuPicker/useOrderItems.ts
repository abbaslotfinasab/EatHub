// presentation/components/order/OrderMenuPicker/useOrderItems.ts

import { useCallback } from "react";

import type { MenuItem } from "../../../../domain/entities/product/menu/MenuItem";

import { useOrderForm } from "../../../forms/order/useOrderForm";

export const useOrderItems = () => {

    const {
        watch,
        setValue,
    } = useOrderForm();

    const orderItems =
        watch("orderItems");

    // ===========================
    // Add
    // ===========================

    const addItem = useCallback(
        (item: MenuItem) => {

            const exists =
                orderItems.find(
                    x =>
                        x.menuItemId ===
                        item.id,
                );

            if (exists) {
                return;
            }

            setValue(
                "orderItems",
                [
                    ...orderItems,
                    {
                        menuItemId:
                            item.id,
                        quantity: 1,
                        notes: "",
                    },
                ],
                {
                    shouldDirty: true,
                    shouldValidate: true,
                },
            );

        },
        [
            orderItems,
            setValue,
        ],
    );

    // ===========================
    // Increase
    // ===========================

    const increaseQuantity =
        useCallback(
            (
                menuItemId: string,
            ) => {

                setValue(
                    "orderItems",
                    orderItems.map(
                        item =>
                            item.menuItemId ===
                            menuItemId
                                ? {
                                      ...item,
                                      quantity:
                                          item.quantity +
                                          1,
                                  }
                                : item,
                    ),
                    {
                        shouldDirty: true,
                    },
                );

            },
            [
                orderItems,
                setValue,
            ],
        );

    // ===========================
    // Decrease
    // ===========================

    const decreaseQuantity =
        useCallback(
            (
                menuItemId: string,
            ) => {

                const updated =
                    orderItems
                        .map(
                            item =>
                                item.menuItemId ===
                                menuItemId
                                    ? {
                                          ...item,
                                          quantity:
                                              item.quantity -
                                              1,
                                      }
                                    : item,
                        )
                        .filter(
                            item =>
                                item.quantity >
                                0,
                        );

                setValue(
                    "orderItems",
                    updated,
                    {
                        shouldDirty: true,
                    },
                );

            },
            [
                orderItems,
                setValue,
            ],
        );

    // ===========================
    // Remove
    // ===========================

    const removeItem =
        useCallback(
            (
                menuItemId: string,
            ) => {

                setValue(
                    "orderItems",
                    orderItems.filter(
                        item =>
                            item.menuItemId !==
                            menuItemId,
                    ),
                    {
                        shouldDirty: true,
                    },
                );

            },
            [
                orderItems,
                setValue,
            ],
        );

    // ===========================
    // Update Notes
    // ===========================

    const updateNotes =
        useCallback(
            (
                menuItemId: string,
                notes: string,
            ) => {

                setValue(
                    "orderItems",
                    orderItems.map(
                        item =>
                            item.menuItemId ===
                            menuItemId
                                ? {
                                      ...item,
                                      notes,
                                  }
                                : item,
                    ),
                    {
                        shouldDirty: true,
                    },
                );

            },
            [
                orderItems,
                setValue,
            ],
        );

    // ===========================
    // Clear
    // ===========================

    const clearItems =
        useCallback(() => {

            setValue(
                "orderItems",
                [],
                {
                    shouldDirty: true,
                },
            );

        }, [setValue]);

    return {
        orderItems,

        addItem,

        removeItem,

        increaseQuantity,

        decreaseQuantity,

        updateNotes,

        clearItems,
    };

};