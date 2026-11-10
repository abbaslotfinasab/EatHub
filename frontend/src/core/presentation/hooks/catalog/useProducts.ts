import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { container } from "../../../data/di/container.ts";
import type { ProductInput } from "../../../domain/entities/catalog/Product.ts";
import { useBusinessContextStore } from "../../store/business-context.store.ts";

export const useProducts = (search: string, page = 1, pageSize = 20) => {
    const businessId = useBusinessContextStore((state) => state.selectedBusinessId);
    const repository = container.catalogContainer.productRepository;

    return useQuery({
        queryKey: ["catalog", "products", businessId, { search, page, pageSize }],
        queryFn: () => repository.findAll({ search, page, pageSize }),
        enabled: businessId !== null,
    });
};

export const useCreateProduct = () => {
    const queryClient = useQueryClient();
    const businessId = useBusinessContextStore((state) => state.selectedBusinessId);
    const repository = container.catalogContainer.productRepository;

    return useMutation({
        mutationFn: (input: ProductInput) => repository.create(input),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["catalog", "products", businessId] }),
    });
};

export const useUpdateProduct = () => {
    const queryClient = useQueryClient();
    const businessId = useBusinessContextStore((state) => state.selectedBusinessId);
    const repository = container.catalogContainer.productRepository;

    return useMutation({
        mutationFn: ({ id, input }: { id: number; input: Partial<ProductInput> }) => repository.update(id, input),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["catalog", "products", businessId] }),
    });
};
