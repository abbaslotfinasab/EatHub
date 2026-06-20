// presentation/hooks/useCreateBusiness.ts

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createBusinessUseCase } from "../../data/di/business";
import type {Business} from "../../domain/entities/account/Business.ts";

export const useCreateBusiness = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: Business) =>
      createBusinessUseCase.execute(input),

    onSuccess: () => {
      // بعد از ساخت بیزینس، لیست بیزینس‌ها آپدیت بشه
      queryClient.invalidateQueries({ queryKey: ["businesses"] });
    },
  });
};