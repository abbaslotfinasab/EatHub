import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/auth.store";
import {FullPageLoader} from "../pages/FullPageLoader.tsx";

export const AuthGuard = () => {
    const me = useAuthStore((s) => s.me);
    const isHydrating = useAuthStore((s) => s.isHydrating);

    if (isHydrating) return <FullPageLoader />;

    if (!me) {
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
};