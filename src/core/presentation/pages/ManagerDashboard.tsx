import { Box, Grid, Stack } from "@mui/material";

import { DashboardHeader } from "../components/dashboard/DashboardHeader.tsx";
import { DashboardStats } from "../components/dashboard/DashboardStats";
import { RestaurantHealth } from "../components/dashboard/RestaurantHealth";
import { SalesChart } from "../components/dashboard/SalesChart";
import { OrdersTable } from "../components/dashboard/OrdersTable";
import { InventoryAlerts } from "../components/dashboard/InventoryAlerts";
import { TopProducts } from "../components/dashboard/TopProducts";
import { ActivityFeed } from "../components/dashboard/ActivityFeed";

import { useDashboard } from "../hooks/useDashboard";

export const ManagerDashboard = () => {
    const {
        salesData,
        isLoading,
    } = useDashboard();

    if (isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <Box
            sx={{
                p: 3,
                backgroundColor: "#F8FAFC",
                minHeight: "100vh",
            }}
        >
            <Stack spacing={3}>
                {/* Header */}
                <DashboardHeader />

                {/* KPI Cards */}
                <DashboardStats/>

                {/* Health Overview */}
                <RestaurantHealth/>

                {/* Sales Chart */}
                <SalesChart data={salesData} />

                {/* Orders + Alerts */}
                <Grid container spacing={3}>
                    <Grid size={{ xs: 12, lg: 8 }}>
                        <OrdersTable />
                    </Grid>

                    <Grid size={{ xs: 12, lg: 4 }}>
                        <InventoryAlerts />
                    </Grid>
                </Grid>

                {/* Products + Activity */}
                <Grid container spacing={3}>
                    <Grid size={{ xs: 12, md: 6 }}>
                        <TopProducts />
                    </Grid>

                    <Grid size={{ xs: 12, md: 6 }}>
                        <ActivityFeed />
                    </Grid>
                </Grid>
            </Stack>
        </Box>
    );
};