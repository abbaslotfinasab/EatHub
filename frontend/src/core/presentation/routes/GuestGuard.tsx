import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/auth.store";

export const GuestGuard = () => {
    const me = useAuthStore((s) => s.me);
    const isHydrating = useAuthStore((s) => s.isHydrating);

    if (isHydrating) return null;

    if (me) {
        return <Navigate to="/dashboard" replace />;
    }

    return <Outlet />;
};