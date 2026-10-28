import {useMutation, useQueryClient} from "@tanstack/react-query";
import {container} from "../../../data/di/container.ts";
import type {RecordOrderConsumptionInput} from "../../../domain/entities/product/order/OrderInventoryConsumption.ts";

export const useRecordOrderConsumption = () => {
    const queryClient = useQueryClient();
    const useCase = container.orderContainer.recordOrderConsumptionUseCase;

    return useMutation({
        mutationFn: (input: RecordOrderConsumptionInput) => useCase.execute(input),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["orders"]});
        },
    });
};
