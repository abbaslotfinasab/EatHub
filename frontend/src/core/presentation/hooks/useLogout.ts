// src/features/auth/hooks/useLogout.ts

import { useNavigate } from "react-router-dom";
import {useAuthStore} from "../store/auth.store.ts";

export const useLogout = () => {
    const navigate = useNavigate();

    return () => {
        // پاک کردن token و me
        useAuthStore.getState().clear();

        // برگشت به صفحه لاگین
        navigate("/login", {
            replace: true,
        });
    };
};