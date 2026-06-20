import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/auth.store.ts";

export const ProtectedRoute = () => {
    const me = useAuthStore((s) => s.me);
    const isHydrating = useAuthStore((s) => s.isHydrating);

    if (isHydrating) {
        return <div>Loading...</div>;
    }

    if (!me) {
        return <Navigate to="/login" replace />;
    }

     if (!me.has_business) {
        return <Navigate to="/business" replace />;
    }

    return <Outlet />;
};