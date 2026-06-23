// import { Navigate, Outlet } from "react-router-dom";
// import { useAuthStore } from "../../store/auth.store";
//
// export const RoleGuard = ({ allowedRoles }: { allowedRoles: string[] }) => {
//     const me = useAuthStore((s) => s.me);
//     const isHydrating = useAuthStore((s) => s.isHydrating);
//
//     if (isHydrating) return null;
//
//     if (!me) return <Navigate to="/login" replace />;
//
//     if (!allowedRoles.includes(me.active_business.role)) {
//         return <Navigate to="/dashboard" replace />;
//     }
//
//     return <Outlet />;
// };