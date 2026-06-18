// src/features/auth/presentation/pages/ResetPasswordPage.tsx

import { AuthLayout } from "../components/layout/AuthLayout";
import { AuthCard } from "../components/auth/AuthCard";
import { ResetPasswordForm } from "../components/auth/ResetPasswordForm";

export const ResetPasswordPage = () => {
    return (
        <AuthLayout>
            <AuthCard
                title="رمز عبور جدید"
                subtitle="یک رمز عبور جدید برای حساب خود انتخاب کنید."
            >
                <ResetPasswordForm />
            </AuthCard>
        </AuthLayout>
    );
};