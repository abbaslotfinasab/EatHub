// src/core/presentation/providers/SidebarProvider.tsx

import {
    useState,
    type ReactNode,
} from "react";

import { SidebarContext } from "../contexts/SidebarContext";

export const SidebarProvider = ({
                                    children,
                                }: {
    children: ReactNode;
}) => {
    const [isCollapsed, setIsCollapsed] =
        useState(false);

    const [mobileOpen, setMobileOpen] =
        useState(false);

    // Desktop

    const toggleCollapse = () => {
        setIsCollapsed((prev) => !prev);
    };

    const collapse = () => {
        setIsCollapsed(true);
    };

    const expand = () => {
        setIsCollapsed(false);
    };

    // Mobile

    const openMobile = () => {
        setMobileOpen(true);
    };

    const closeMobile = () => {
        setMobileOpen(false);
    };

    const toggleMobile = () => {
        setMobileOpen((prev) => !prev);
    };

    return (
        <SidebarContext.Provider
            value={{
                isCollapsed,

                toggleCollapse,
                collapse,
                expand,

                mobileOpen,

                openMobile,
                closeMobile,
                toggleMobile,
            }}
        >
            {children}
        </SidebarContext.Provider>
    );
};