// src/core/presentation/contexts/SidebarContext.ts

import { createContext } from "react";

export interface SidebarContextType {
    // Desktop Sidebar

    isCollapsed: boolean;

    toggleCollapse: () => void;
    collapse: () => void;
    expand: () => void;

    // Mobile Drawer

    mobileOpen: boolean;

    openMobile: () => void;
    closeMobile: () => void;
    toggleMobile: () => void;
}

export const SidebarContext =
    createContext<SidebarContextType | undefined>(
        undefined
    );