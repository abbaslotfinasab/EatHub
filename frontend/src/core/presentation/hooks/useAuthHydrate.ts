import { useEffect } from "react";
import { container } from "../../data/di/container";
import { useAuthStore } from "../store/auth.store.ts";
import type {AxiosError} from "axios";

export const useAuthHydrate = () => {
    const { getMeUseCase } = container.authContainer;

    const setMe = useAuthStore((s) => s.setMe);
    const setHydrating = useAuthStore((s) => s.setHydrating);
    const clear = useAuthStore((s) => s.clear);

    useEffect(() => {
        const hydrate = async () => {
            setHydrating(true);

            const token = localStorage.getItem("accessToken");

            if (!token) {
                clear();
                setHydrating(false);
                return;
            }

            try {
                const me = await getMeUseCase.execute();
                setMe(me);

            }  catch (err) {
            const error = err as AxiosError;

            console.error("ME FAILED:", error);

            if (error.response?.status === 401) {
                clear();
            }
            } finally {
                setHydrating(false);
            }
        };

        void hydrate();
    }, [getMeUseCase, setMe, setHydrating, clear]);};