import {useEffect, useState} from "react";

import {
    Container,
    FormControl,
    Grid,
    InputLabel,
    MenuItem,
    Pagination,
    Paper,
    Select,
    Stack,
} from "@mui/material";

import type {SelectChangeEvent} from "@mui/material/Select";

import {DashboardStats} from "../components/dashboard/DashboardStats";
import {SalesChart} from "../components/dashboard/SalesChart";
import {OrdersTable} from "../components/dashboard/OrdersTable";
import {InventoryAlerts} from "../components/dashboard/InventoryAlerts";
import {TopProducts} from "../components/dashboard/TopProducts";
import {ActivityFeed} from "../components/dashboard/ActivityFeed";

import {useDashboard} from "../hooks/useDashboard";

export const ManagerDashboard = () => {
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);

    const {
        data: dashboard,
        isLoading,
    } = useDashboard({
        page: page + 1,
        pageSize: rowsPerPage,
    });

    const recentOrders = dashboard?.recentOrders.results ?? [];
    const totalCount = dashboard?.recentOrders.count ?? 0;
    const lastPage = Math.max(
        0,
        Math.ceil(totalCount / rowsPerPage) - 1,
    );
    const safePage = Math.min(page, lastPage);

    useEffect(() => {
        if (page !== safePage) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setPage(safePage);
        }
    }, [page, safePage]);

    const handlePageChange = (
        _event: React.ChangeEvent<unknown>,
        newPage: number,
    ) => {
        const nextPage = newPage - 1;
        setPage(Math.min(Math.max(nextPage, 0), lastPage));
    };

    const handleRowsPerPageChange = (
        event: SelectChangeEvent<number>,
    ) => {
        setRowsPerPage(Number(event.target.value));
        setPage(0);
    };

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
                            orders={recentOrders}
                        />

                        {recentOrders.length > 0 && lastPage > 0 && (
                            <Paper
                                variant="outlined"
                                sx={{
                                    mt: 2,
                                    p: {xs: 1.5, sm: 2},
                                    borderRadius: 2,
                                    direction: "rtl",
                                }}
                            >
                                <Stack
                                    sx={{
                                        flexDirection: {
                                            xs: "column",
                                            sm: "row",
                                        },
                                        gap: 2,
                                        alignItems: "center",
                                        justifyContent: "center",
                                    }}
                                >
                                    <Pagination
                                        count={Math.max(
                                            1,
                                            Math.ceil(
                                                totalCount / rowsPerPage,
                                            ),
                                        )}
                                        page={safePage + 1}
                                        onChange={handlePageChange}
                                        shape="rounded"
                                        color="primary"
                                        siblingCount={1}
                                        boundaryCount={1}
                                        aria-label="صفحه‌بندی سفارشات اخیر"
                                    />

                                    <FormControl
                                        size="small"
                                        sx={{minWidth: 150}}
                                    >
                                        <InputLabel id="dashboard-rows-per-page-label">
                                            تعداد در صفحه
                                        </InputLabel>
                                        <Select
                                            labelId="dashboard-rows-per-page-label"
                                            value={rowsPerPage}
                                            label="تعداد در صفحه"
                                            onChange={
                                                handleRowsPerPageChange
                                            }
                                            inputProps={{
                                                "aria-label":
                                                    "تعداد در صفحه",
                                            }}
                                        >
                                            {[5, 10, 20, 50].map(
                                                (option) => (
                                                    <MenuItem
                                                        key={option}
                                                        value={option}
                                                    >
                                                        {option}
                                                    </MenuItem>
                                                ),
                                            )}
                                        </Select>
                                    </FormControl>
                                </Stack>
                            </Paper>
                        )}
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
