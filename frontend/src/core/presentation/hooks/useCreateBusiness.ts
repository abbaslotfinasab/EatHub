// presentation/hooks/useCreateBusiness.ts

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createBusinessUseCase } from "../../data/di/business";
import type {Business} from "../../domain/entities/account/Business.ts";
import { useAuthStore } from "../store/auth.store.ts";
import {container} from "../../data/di/container.ts";

export const useCreateBusiness = () => {
  const queryClient = useQueryClient();
  const {getMeUseCase } = container.authContainer;
  const setMe = useAuthStore((s) => s.setMe);


  return useMutation({
    mutationFn: (input: Business) =>
      createBusinessUseCase.execute(input),

    onSuccess: async () => {
      // بعد از ساخت بیزینس، لیست بیزینس‌ها آپدیت بشه
      await queryClient.invalidateQueries({queryKey: ["businesses"]});
      const me = await getMeUseCase.execute();
      setMe(me);
    },
  });
};