// src/presentation/hooks/useCreatePurchaseOrder.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {createPurchaseOrderUseCase} from "../../data/di/purchaseOrder.ts";
import type {PurchaseOrderWithItems} from "../../domain/entities/inventory/facture/PurchaseOrderWithItems.ts";

export const useCreatePurchaseOrder = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (input: PurchaseOrderWithItems) =>
            createPurchaseOrderUseCase.execute(input),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] });
        },
    });
};