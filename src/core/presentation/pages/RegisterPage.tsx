// src/features/auth/presentation/pages/RegisterPage.tsx

import { AuthLayout } from "../components/layout/AuthLayout";
import { AuthCard } from "../components/auth/AuthCard";
import { RegisterForm } from "../components/auth/RegisterForm";

export const RegisterPage = () => {
    return (
        <AuthLayout>
            <AuthCard
                title="ایجاد حساب 🚀"
                subtitle="حساب EatHub خود را ایجاد کنید"
            >
                <RegisterForm />
            </AuthCard>
        </AuthLayout>
    );
};