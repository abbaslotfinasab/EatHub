import { container } from "../../data/di/container";
import { useAuthStore } from "../../store/auth.store";

export const useLogin = () => {
    const { loginUseCase} =
        container.authContainer;

    const setTokens = useAuthStore((s) => s.setTokens);

    return async (email: string, password: string) => {
        try {
            const auth = await loginUseCase.execute(
                email,
                password
            );

            // ✅ single source of truth
            setTokens(auth.accessToken, auth.refreshToken);

        } catch (err) {
            console.error("LOGIN FAILED:", err);
            throw err;
        }
    };
};