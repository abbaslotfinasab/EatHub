// src/features/auth/presentation/pages/LoginPage.tsx

import { AuthLayout } from "../components/layout/AuthLayout";
import { AuthCard } from "../components/auth/AuthCard.tsx";
import { LoginForm } from "../components/auth/LoginForm";

export const LoginPage = () => {
    return (
        <AuthLayout>
            <AuthCard
                title="خوش آمدید 👋"
                subtitle="برای ادامه وارد حساب کاربری خود شوید"
            >
                <LoginForm />
            </AuthCard>
        </AuthLayout>
    );
};