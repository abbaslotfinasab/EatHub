import { useQuery } from "@tanstack/react-query";

import { container } from "../../data/di/container";
import type {DashboardFilters} from "../../domain/objects/filters/DashboardFilters.ts";

export const useDashboard = (filters?: DashboardFilters) => {
    const { getDashboardUseCase } =
        container.dashboardContainer;

    return useQuery({
        queryKey: filters ? ["dashboard", filters] : ["dashboard"],
        queryFn: async () => {
            try {
                return await getDashboardUseCase.execute(filters);
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
