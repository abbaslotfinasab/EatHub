import { useAuthStore } from "../store/auth.store.ts";

export const useAuth = () => {
    const me = useAuthStore((s) => s.me);

    const isAuthenticated = !!me;

    const isGuest = !me;

    return {
        me,
        isAuthenticated,
        isGuest,
    };
};