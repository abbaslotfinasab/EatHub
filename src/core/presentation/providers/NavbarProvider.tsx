// src/core/presentation/contexts/NavbarProvider.tsx
import { useState, type ReactNode } from 'react';
import { NavbarContext } from "../contexts/NavbarContext";

type NavbarRightElement = ReactNode | null;

export interface NavbarContextType {
    rightElement: NavbarRightElement;
    setRightElement: (element: NavbarRightElement) => void;
    isVisible: boolean;
    setVisible: (visible: boolean) => void;
    showMenu: boolean;           // جدید: نمایش منو یا نه
    setShowMenu: (show: boolean) => void;
}

export const NavbarProvider = ({ children }: { children: ReactNode }) => {
    const [rightElement, setRightElement] = useState<NavbarRightElement>(null);
    const [isVisible, setVisible] = useState(true);
    const [showMenu, setShowMenu] = useState(true); // به طور پیش‌فرض منو نمایش داده شود

    return (
        <NavbarContext.Provider
            value={{
                rightElement,
                setRightElement,
                isVisible,
                setVisible,
                showMenu,
                setShowMenu,
            }}
        >
            {children}
        </NavbarContext.Provider>
    );
};