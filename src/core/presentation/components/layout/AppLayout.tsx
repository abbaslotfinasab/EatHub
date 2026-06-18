// layouts/AppLayout.tsx

import { Outlet } from "react-router-dom";

export const AppLayout = () => {
    return (
            <div className="min-h-screen bg-gray-50">
                <Outlet />
            </div>
    );
};