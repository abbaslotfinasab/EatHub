import { useAuthStore } from "../../store/auth.store.ts";
import {Outlet} from "react-router-dom";

export const PublicRoute = () => {
    const me = useAuthStore((s) => s.me);
    const isHydrating = useAuthStore((s) => s.isHydrating);

    if (isHydrating) return null;

    if (me) {
        // return <Navigate to="/dashboard" replace />;
    }

    return <Outlet />;
};