import { container } from "../../data/di/container";
import { useAuthStore } from "../store/auth.store";

export const useLogin = () => {
    const { loginUseCase} =
        container.authContainer;

    const { getMeUseCase } = container.authContainer;

    const setMe = useAuthStore((s) => s.setMe);

    const setTokens = useAuthStore((s) => s.setTokens);

    return async (identifier: string, password: string) => {
        try {
            const auth = await loginUseCase.execute(
                identifier,
                password
            );

            // ✅ single source of truth
            setTokens(auth.accessToken, auth.refreshToken);

            const me = await getMeUseCase.execute();

            setMe(me);


        } catch (err) {
            console.error("LOGIN FAILED:", err);
            throw err;
        }
    };
};