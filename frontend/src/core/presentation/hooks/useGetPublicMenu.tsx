import {container} from "../../data/di/container.ts";
import {useQuery} from "@tanstack/react-query";

export const useGetPublicMenus = (
    slug?: string
) => {
    const {
        getPublicMenusUseCase,
    } = container.menuContainer;


    return useQuery({
        queryKey: [
            "public-menu",
            slug,
        ],

        enabled: !!slug,

        queryFn: () =>
            getPublicMenusUseCase.execute(
                slug!
            ),
    });
};