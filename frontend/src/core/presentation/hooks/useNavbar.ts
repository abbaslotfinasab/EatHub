// src/core/presentation/hooks/useNavbar.ts
import { useContext } from 'react';
import { NavbarContext } from '../contexts/NavbarContext'; // توجه: به فایل جدید

export const useNavbar = () => {
    const context = useContext(NavbarContext);
    if (!context) throw new Error('useNavbar must be used within NavbarProvider');
    return context;
};