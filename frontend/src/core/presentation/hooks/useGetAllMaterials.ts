// presentation/hooks/useGetAllMaterials.ts
import { useQuery } from '@tanstack/react-query';
import type {MaterialFilters} from "../../domain/objects/filters/MaterialFilters.ts";
import {getAllMaterialsUseCase} from "../../data/di/material.ts";

export const useGetAllMaterials = (filters?: MaterialFilters) => {
    return useQuery({
        queryKey: ['materials', filters],
        queryFn: () => getAllMaterialsUseCase.execute(filters),
    });
};