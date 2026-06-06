// src/core/presentation/components/layout/Navbar.tsx
// src/core/presentation/components/layout/Navbar.tsx
import { Menu, X } from 'lucide-react';
import { useState } from 'react';
import {Link, NavLink} from 'react-router-dom';
import {useNavbar} from "../../hooks/useNavbar.ts";

export const Navbar = () => {
    const {rightElement, isVisible, showMenu } = useNavbar();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    if (!isVisible) return null;

    return (
        <nav className="sticky top-0 z-50 bg-white shadow-md">
            <div className="mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex h-16 items-center justify-between">
                    {/* لوگو/برند */}
                    <div className="flex items-center">
                        <Link to="/" className="text-xl font-bold text-red-600">
                            EatHub
                        </Link>
                    </div>

                    {/* منوی دسکتاپ (فقط اگر showMenu === true) */}
                    {showMenu && (
                        <div className="hidden md:flex md:items-center md:space-x-4 md:space-x-reverse">
                            <NavLink to="/dashboard">داشبورد</NavLink>
                            <NavLink to="/recipes">رسپی‌ها</NavLink>
                            <NavLink to="/ingredients">مواد اولیه</NavLink>
                            <NavLink to="/orders">سفارشات</NavLink>
                            <NavLink to="/reports">گزارشات</NavLink>
                        </div>
                    )}

                    {/* بخش راست Navbar (عنوان صفحه و المان‌های سفارشی) */}
                    <div className="flex items-center gap-2">
                        <div className="text-right">
                            {rightElement && <div className="text-sm text-gray-500">{rightElement}</div>}
                        </div>
                        {/* دکمه منوی موبایل (فقط اگر showMenu === true) */}
                        {showMenu && (
                            <button
                                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                                className="rounded-md p-2 text-gray-500 hover:bg-gray-100 focus:outline-none md:hidden"
                            >
                                {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* منوی موبایل (فقط اگر showMenu === true) */}
            {showMenu && isMobileMenuOpen && (
                <div className="border-t border-gray-200 bg-white md:hidden">
                    <div className="space-y-1 px-2 pb-3 pt-2">
                        <MobileNavLink to="/dashboard" onClick={() => setIsMobileMenuOpen(false)}>
                            داشبورد
                        </MobileNavLink>
                        <MobileNavLink to="/recipes" onClick={() => setIsMobileMenuOpen(false)}>
                            رسپی‌ها
                        </MobileNavLink>
                        <MobileNavLink to="/ingredients" onClick={() => setIsMobileMenuOpen(false)}>
                            مواد اولیه
                        </MobileNavLink>
                        <MobileNavLink to="/orders" onClick={() => setIsMobileMenuOpen(false)}>
                            سفارشات
                        </MobileNavLink>
                        <MobileNavLink to="/reports" onClick={() => setIsMobileMenuOpen(false)}>
                            گزارشات
                        </MobileNavLink>
                    </div>
                </div>
            )}
        </nav>
    );
};

// کامپوننت کمکی برای لینک‌های موبایل
const MobileNavLink = ({ to, onClick, children }: { to: string; onClick: () => void; children: React.ReactNode }) => (
    <Link
        to={to}
        onClick={onClick}
        className="block rounded-md px-3 py-2 text-base font-medium text-gray-700 transition hover:bg-gray-100 hover:text-gray-900"
    >
        {children}
    </Link>
);