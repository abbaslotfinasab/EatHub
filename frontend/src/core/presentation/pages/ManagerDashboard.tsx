import {Container, Grid, Stack} from "@mui/material";

import {DashboardStats} from "../components/dashboard/DashboardStats";
import {SalesChart} from "../components/dashboard/SalesChart";
import {OrdersTable} from "../components/dashboard/OrdersTable";
import {InventoryAlerts} from "../components/dashboard/InventoryAlerts";
import {TopProducts} from "../components/dashboard/TopProducts";
import {ActivityFeed} from "../components/dashboard/ActivityFeed";

import {useDashboard} from "../hooks/useDashboard";

export const ManagerDashboard = () => {
    const {
        data: dashboard,
        isLoading,
    } = useDashboard();

    if (isLoading) {
        return <div>Loading...</div>;
    }

    return (
                <Container maxWidth="xl">

            <Stack spacing={3}>

                <DashboardStats
                    todaySales={dashboard?.stats.todaySales ?? 0}
                    todayOrders={dashboard?.stats.todayOrders ?? 0}
                    activeOrders={dashboard?.stats.activeOrders ?? 0}
                    todayReservations={dashboard?.stats.todayReservations ?? 0}
                    inventoryAlerts={dashboard?.stats.inventoryAlerts ?? 0}
                />

                <SalesChart
                    data={dashboard?.salesChart ?? []}
                />

                <Grid container spacing={3}>
                    <Grid size={{xs: 12, lg: 8}}>
                        <OrdersTable
                            orders={dashboard?.recentOrders ?? []}
                        />
                    </Grid>

                    <Grid size={{xs: 12, lg: 4}}>
                        <InventoryAlerts
                        />
                    </Grid>
                </Grid>

                <Grid container spacing={3}>
                    <Grid size={{xs: 12, md: 6}}>
                        <TopProducts
                            products={dashboard?.topProducts ?? []}
                        />
                    </Grid>

                    <Grid size={{xs: 12, md: 6}}>
                        <ActivityFeed
                            activities={dashboard?.activities ?? []}
                        />
                    </Grid>
                </Grid>
            </Stack>
                </Container>
    );
};