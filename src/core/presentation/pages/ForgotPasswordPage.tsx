// src/features/auth/presentation/pages/ForgotPasswordPage.tsx

import { AuthLayout } from "../components/layout/AuthLayout";
import { AuthCard } from "../components/auth/AuthCard";
import { ForgotPasswordForm } from "../components/auth/ForgotPasswordForm";

export const ForgotPasswordPage = () => {
    return (
        <AuthLayout>
            <AuthCard
                title="بازیابی رمز عبور"
                subtitle="شماره موبایل خود را وارد کنید تا کد تأیید برای شما ارسال شود."
            >
                <ForgotPasswordForm />
            </AuthCard>
        </AuthLayout>
    );
};