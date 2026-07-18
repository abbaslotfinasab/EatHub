import { useAuthStore } from "../store/auth.store";
import {Navigate, Outlet} from "react-router-dom";

export const BusinessGuard = () => {
    const me = useAuthStore((s) => s.me);

    if (!me?.has_business) {
        return <Navigate to="/business" replace />;
    }

    return <Outlet />;
};