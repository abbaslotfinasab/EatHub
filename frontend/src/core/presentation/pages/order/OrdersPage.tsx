import {useEffect, useMemo, useState} from "react";
import {isAxiosError} from "axios";

import {
    Container,
    Fab,
    FormControl,
    InputLabel,
    MenuItem,
    Pagination,
    Paper,
    Select,
    type SelectChangeEvent,
    Stack,
} from "@mui/material";

import AddIcon from "@mui/icons-material/Add";

import {useNavigate} from "react-router-dom";

import {
    OrderStatus,
} from "../../../domain/entities/product/order/Order.ts";

import type {
    OrderWithItems,
} from "../../../domain/entities/product/order/OrderWithItems.ts";

import type {
    OrderFilters,
} from "../../../domain/objects/filters/OrderFilters.ts";


import {useDebounce} from "../../hooks/useDebounce.ts";

import {useGetAllOrders} from "../../hooks/order/useGetAllOrders.ts";
import {useUpdateOrderStatus} from "../../hooks/order/useUpdateOrderStatus.ts";


import {OrdersLoading} from "../../components/order/OrdersLoading.tsx";
import {OrdersToolbar} from "../../components/order/OrdersToolbar.tsx";
import {OrdersTable} from "../../components/order/OrdersTable.tsx";
import {OrdersStats} from "../../components/order/OrderStats.tsx";
import {OrdersEmpty} from "../../components/order/OrdersEmpty.tsx";

import {OrderActionsMenu} from "../../components/order/OrderActionsMenu.tsx";
import {OrderDetailsDialog} from "../../components/order/OrderDetailsDialog.tsx";
import {OrderStatusDialog} from "../../components/order/OrderStatusDialog.tsx";
import {useDeleteOrder} from "../../hooks/order/useDeleteOrder.ts";
import {useGetOrderById} from "../../hooks/order/useGetOrderById.ts";


const getDeleteOrderErrorMessage = (error: unknown): string => {
    if (isAxiosError(error)) {
        const data: unknown = error.response?.data;
        if (typeof data === "string") {
            return data;
        }
        if (data && typeof data === "object" && "detail" in data) {
            const detail = (data as {detail?: unknown}).detail;
            if (typeof detail === "string") {
                return detail;
            }
            if (Array.isArray(detail)) {
                return detail.map(String).join(" ");
            }
        }
    }

    return "حذف سفارش انجام نشد. سفارش‌های پرداخت‌شده یا دارای سابقه تراکنش قابل حذف نیستند.";
};


export const OrdersPage = () => {


    const navigate = useNavigate();


    /*
    |--------------------------------------------------------------------------
    | Filters
    |--------------------------------------------------------------------------
    */


    const [
        search,
        setSearch
    ] = useState("");


    const [
        filters,
        setFilters
    ] = useState<OrderFilters>({

        ordering:
            "-created_at",

    });

    const [page, setPage] = useState(0);

    const [rowsPerPage, setRowsPerPage] = useState(20);


    const debouncedSearch =
        useDebounce(
            search,
            500
        );


    const orderFilters = useMemo(() => ({


        ...filters,


        search:
            debouncedSearch || undefined,

        page: page + 1,

        pageSize: rowsPerPage,


    }), [

        filters,

        debouncedSearch,
        page,
        rowsPerPage,

    ]);


    /*
    |--------------------------------------------------------------------------
    | Query
    |--------------------------------------------------------------------------
    */

    const deleteOrder =
        useDeleteOrder();

    const {
        data,
        isLoading,
    } = useGetAllOrders(
        orderFilters
    );

    const orders = data?.results ?? [];
    const totalOrderCount = data?.count ?? 0;
    const lastPage = Math.max(
        0,
        Math.ceil(totalOrderCount / rowsPerPage) - 1,
    );
    const safePage = Math.min(page, lastPage);

    useEffect(() => {
        if (page !== safePage) {
            setPage(safePage);
        }
    }, [page, safePage]);

    /*
    |--------------------------------------------------------------------------
    | UI State
    |--------------------------------------------------------------------------
    */


    const [selectedOrderId, setSelectedOrderId] =
        useState<string | null>(null);


    const {
        data: orderDetail,
        isLoading: orderDetailLoading,
    } = useGetOrderById(
        selectedOrderId ?? undefined,
    );

    const [
        dialogOpen,
        setDialogOpen
    ] = useState(false);


    const [
        statusDialogOpen,
        setStatusDialogOpen
    ] = useState(false);


    const [
        menuAnchor,
        setMenuAnchor
    ] = useState<HTMLElement | null>(
        null
    );


    const updateStatusMutation =
        useUpdateOrderStatus();


    /*
    |--------------------------------------------------------------------------
    | Handlers
    |--------------------------------------------------------------------------
    */


    const handleResetFilters = () => {

        setSearch("");
        setPage(0);

        setFilters({

            ordering:
                "-created_at",

        });

    };

    const handleSearchChange = (value: string) => {
        setPage(0);
        setSearch(value);
    };

    const handleFiltersChange = (nextFilters: OrderFilters) => {
        setPage(0);
        setFilters(nextFilters);
    };

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


    const handleOrderClick = (
        order: OrderWithItems
    ) => {

        setSelectedOrderId(
            order.order.id,
        );
        setDialogOpen(true);

    };


    const handleMenuOpen = (
        event: React.MouseEvent<HTMLElement>,
        order: OrderWithItems,
    ) => {

        setSelectedOrderId(
            order.order.id,
        );
        setMenuAnchor(
            event.currentTarget
        );

    };


    const handleMenuClose = () => {

        setMenuAnchor(null);

    };


    const handleOpenStatusDialog = () => {


        if (!selectedOrderId) {

            return;

        }


        setStatusDialogOpen(true);

    };


    /*
    |--------------------------------------------------------------------------
    | Statistics
    |--------------------------------------------------------------------------
    */


    const stats = useMemo(() => {


        return {


            totalOrders:
            totalOrderCount,


            pendingOrders:
            orders.filter(
                item =>
                    item.order.status ===
                    OrderStatus.PENDING
            ).length,


            preparingOrders:
            orders.filter(
                item =>
                    item.order.status ===
                    OrderStatus.PREPARING
            ).length,


            readyOrders:
            orders.filter(
                item =>
                    item.order.status ===
                    OrderStatus.READY
            ).length,


        };


    }, [orders, totalOrderCount]);


    const hasActiveFilters = Boolean(
        search ||
        filters.status ||
        filters.orderType ||
        filters.paymentStatus ||
        filters.paymentMethod ||
        filters.fromDate ||
        filters.toDate ||
        filters.minTotal !== undefined ||
        filters.maxTotal !== undefined ||
        (filters.ordering && filters.ordering !== "-created_at")
    );

    if (isLoading) {

        return <OrdersLoading/>;

    }


    return (

        <Container maxWidth="xl">


            <Stack spacing={3}>


                <OrdersStats

                    totalOrders={
                        stats.totalOrders
                    }

                    pendingOrders={
                        stats.pendingOrders
                    }

                    preparingOrders={
                        stats.preparingOrders
                    }

                    readyOrders={
                        stats.readyOrders
                    }

                />


                <OrdersToolbar

                    search={search}

                    filters={filters}

                    onSearchChange={handleSearchChange}

                    onFiltersChange={handleFiltersChange}

                />


                {
                    orders.length === 0 ? (


                        <OrdersEmpty

                            hasFilters={hasActiveFilters}


                            onResetFilters={
                                handleResetFilters
                            }

                        />


                    ) : (


                        <>
                            <OrdersTable

                                orders={orders}


                                onOrderClick={
                                    handleOrderClick
                                }


                                onOrderMenuClick={
                                    handleMenuOpen
                                }

                            />

                            <Paper
                                variant="outlined"
                                sx={{
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
                                                totalOrderCount / rowsPerPage,
                                            ),
                                        )}
                                        page={safePage + 1}
                                        onChange={handlePageChange}
                                        shape="rounded"
                                        color="primary"
                                        siblingCount={1}
                                        boundaryCount={1}
                                        aria-label="صفحه‌بندی سفارشات"
                                    />

                                    <FormControl
                                        size="small"
                                        sx={{minWidth: 150}}
                                    >
                                        <InputLabel id="orders-rows-per-page-label">
                                            تعداد در صفحه
                                        </InputLabel>
                                        <Select
                                            labelId="orders-rows-per-page-label"
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
                                            {[10, 20, 50, 100].map(
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
                        </>


                    )
                }


            </Stack>


            <OrderDetailsDialog
                open={dialogOpen}
                loading={orderDetailLoading}
                order={orderDetail ?? undefined}
                onClose={() => {
                    setDialogOpen(false);
                    setSelectedOrderId(null);
                }}
                onStatusChange={() => {


                    handleMenuClose();


                    handleOpenStatusDialog();


                }}


                onEdit={() => {


                    handleMenuClose();


                    if (!selectedOrderId) {

                        return;

                    }


                    navigate(
                        `/orders/${selectedOrderId}/edit`
                    );


                }}
            />

            <OrderStatusDialog


                open={statusDialogOpen}


                order={orderDetail?.order}


                loading={
                    updateStatusMutation.isPending
                }


                onClose={() => {
                    setStatusDialogOpen(false);
                    setSelectedOrderId(null);
                }}


                onSubmit={(data) => {


                    if (!selectedOrderId) {

                        return;

                    }


                    updateStatusMutation.mutate({


                        orderId:
                            selectedOrderId ?? "",


                        status:
                        data.status,


                        paymentStatus:
                        data.paymentStatus,


                        paymentMethod:
                        data.paymentMethod,


                    });


                    setStatusDialogOpen(false);


                }}


            />


            <OrderActionsMenu


                anchorEl={menuAnchor}


                open={
                    Boolean(menuAnchor)
                }


                onClose={
                    handleMenuClose
                }


                onView={() => {


                    handleMenuClose();


                    setDialogOpen(true);


                }}


                onChangeStatus={() => {


                    handleMenuClose();


                    handleOpenStatusDialog();


                }}


                onPrint={() => {


                    handleMenuClose();


                }}


                onEdit={() => {


                    handleMenuClose();


                    if (!selectedOrderId) {

                        return;

                    }


                    navigate(
                        `/orders/${selectedOrderId}/edit`
                    );


                }}


                onDelete={async () => {

                    handleMenuClose();

                    if (!selectedOrderId) {
                        return;
                    }

                    if (!confirm("سفارش حذف شود؟")) {
                        return;
                    }

                    try {
                        await deleteOrder.mutateAsync(selectedOrderId);
                        setSelectedOrderId(null);
                    } catch (error) {
                        window.alert(getDeleteOrderErrorMessage(error));
                    }

                }}


            />


            <Fab

                variant="extended"


                onClick={() =>


                    navigate(
                        "/orders/create"
                    )


                }


                sx={{


                    position:
                        "fixed",


                    left:
                        24,


                    bottom:
                        24,


                    bgcolor:
                        "#10281A",


                    color:
                        "#fff",


                    "&:hover": {

                        bgcolor:
                            "#173724",

                    },


                }}


            >

                <AddIcon/>

                سفارش جدید


            </Fab>


        </Container>

    );

};
