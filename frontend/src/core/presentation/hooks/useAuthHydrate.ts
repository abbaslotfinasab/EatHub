import { useEffect } from "react";
import { container } from "../../data/di/container";
import { useAuthStore } from "../store/auth.store.ts";
import { useBusinessContextStore } from "../store/business-context.store.ts";
import type {AxiosError} from "axios";

export const useAuthHydrate = () => {
    const { getMeUseCase } = container.authContainer;

    const setMe = useAuthStore((s) => s.setMe);
    const setHydrating = useAuthStore((s) => s.setHydrating);
    const clear = useAuthStore((s) => s.clear);
    const selectedBusinessId = useBusinessContextStore((s) => s.selectedBusinessId);

    useEffect(() => {
        const hydrate = async () => {
            setHydrating(true);

            // Do not keep showing the previous tenant's permissions while the
            // selected business context is being refreshed.
            const currentMe = useAuthStore.getState().me;
            if (currentMe?.active_business) {
                setMe({...currentMe, active_business: null});
            }

            const token = localStorage.getItem("accessToken");

            if (!token) {
                clear();
                setHydrating(false);
                return;
            }

            try {
                const me = await getMeUseCase.execute();
                setMe(me);

            } catch (err) {
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
    }, [getMeUseCase, setMe, setHydrating, clear, selectedBusinessId]);
};
