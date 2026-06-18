import { useQuery } from "@tanstack/react-query";

export const useDashboard = () => {
    const { data, isLoading } = useQuery({
        queryKey: ["dashboard"],
        queryFn: async () => {
            return {
                stats: [],
                salesData: [],
                recentOrders: [],
                inventoryAlerts: [],
                topProducts: [],
                activities: [],
                health: {},
            };
        },
    });

    return {
        stats: data?.stats ?? [],
        salesData: data?.salesData ?? [],
        recentOrders: data?.recentOrders ?? [],
        inventoryAlerts: data?.inventoryAlerts ?? [],
        topProducts: data?.topProducts ?? [],
        activities: data?.activities ?? [],
        health: data?.health,
        isLoading,
    };
};