import { useAuthHydrate } from "../hooks/useAuthHydrate";

export const AppHydrate = ({
                               children,
                           }: {
    children: React.ReactNode;
}) => {
    useAuthHydrate();

    return <>{children}</>;
};