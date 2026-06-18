// src/features/auth/presentation/pages/VerifyOtpPage.tsx

import { AuthLayout } from "../components/layout/AuthLayout";
import { AuthCard } from "../components/auth/AuthCard";
import { VerifyOtpForm } from "../components/auth/VerifyOtpForm";

export const VerifyOtpPage = () => {
    return (
        <AuthLayout>
            <AuthCard
                title="تأیید شماره موبایل"
                subtitle="کد ارسال شده به شماره 0912******89 را وارد کنید."
            >
                <VerifyOtpForm />
            </AuthCard>
        </AuthLayout>
    );
};