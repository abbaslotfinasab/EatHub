import { useQuery } from "@tanstack/react-query";

import { container } from "../../data/di/container";

export const useDashboard = () => {
    const { getDashboardUseCase } =
        container.dashboardContainer;

    return useQuery({
        queryKey: ["dashboard"],
        queryFn: async () => {
            try {
                return await getDashboardUseCase.execute();
            } catch (error) {
                console.error(
                    "GET DASHBOARD FAILED:",
                    error,
                );

                throw error;
            }
        },
    });
};