// src/features/auth/hooks/useLogout.ts

import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/auth.store.ts";
import { useBusinessContextStore } from "../store/business-context.store.ts";

export const useLogout = () => {
    const navigate = useNavigate();

    return () => {
        useBusinessContextStore.getState().clearBusiness();
        useAuthStore.getState().clear();
        navigate("/login", { replace: true });
    };
};
