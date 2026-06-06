// src/core/presentation/components/layout/Layout.tsx
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import {NavbarProvider} from "../../providers/NavbarProvider.tsx";

export const Layout = () => {
    return (
        <NavbarProvider>
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <main className="container mx-auto px-4 py-8">
                    <Outlet /> {/* صفحات فرزند در اینجا رندر می‌شوند */}
                </main>
            </div>
        </NavbarProvider>
    );
};