// src/features/auth/presentation/hooks/useRegister.ts

import { useState } from "react";
import {useAuthStore} from "../../store/auth.store.ts";
import {container} from "../../data/di/container.ts";

export const useRegister = () => {
    const { registerUseCase, getMeUseCase } =
        container.authContainer;

    const setMe = useAuthStore((s) => s.setMe);
    const setHydrating = useAuthStore((s) => s.setHydrating);

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const register = async (
        email: string,
        password: string,
        name: string,
        number: string
    ) => {
        setIsLoading(true);
        setError(null);

        try {
            // 1. register request
            const auth = await registerUseCase.execute(
                email,
                password,
                name,
                number
            );

            // 2. save tokens
            localStorage.setItem(
                "accessToken",
                auth.accessToken
            );

            localStorage.setItem(
                "refreshToken",
                auth.refreshToken
            );

            // 3. hydrate me (important: single source of truth)
            const me = await getMeUseCase.execute();

            setMe(me);

            return me;
        } catch (err: unknown) {
            console.error("REGISTER FAILED:", err);

            const message =
                err instanceof Error
                    ? err.message
                    : "Registration failed";

            setError(message);

            throw err;
        } finally {
            setIsLoading(false);
            setHydrating(false);
        }
    };

    return {
        register,
        isLoading,
        error,
    };
};