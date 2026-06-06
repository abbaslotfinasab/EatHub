// presentation/hooks/useDeleteMaterial.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {deleteMaterialUseCase} from "../../data/di/material.ts";

export const useDeleteMaterial = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => deleteMaterialUseCase.execute(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['materials'] });
        },
    });
};