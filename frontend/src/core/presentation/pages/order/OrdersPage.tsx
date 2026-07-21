import {useMemo, useState} from "react";

import {Container, Fab, Stack} from "@mui/material";

import {
    OrderStatus,
    type OrderStatusType,
} from "../../../domain/entities/product/order/Order.ts";
import {useGetAllOrders} from "../../hooks/order/useGetAllOrders.ts";
import {OrdersLoading} from "../../components/order/OrdersLoading.tsx";
import {OrderActionsMenu} from "../../components/order/OrderActionsMenu.tsx";
import {OrdersTable} from "../../components/order/OrdersTable.tsx";
import {OrdersToolbar} from "../../components/order/OrdersToolbar.tsx";
import {OrdersStats} from "../../components/order/OrderStats.tsx";
import {OrdersEmpty} from "../../components/order/OrdersEmpty.tsx";
import {OrderDetailsDialog} from "../../components/order/OrderDetailsDialog.tsx";
import AddIcon from "@mui/icons-material/Add";
import {useNavigate} from "react-router-dom";
import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems.ts";
import {OrderStatusDialog} from "../../components/order/OrderStatusDialog.tsx";
import {useUpdateOrderStatus} from "../../hooks/order/useUpdateOrderStatus.ts";


type StatusFilter =
    | "ALL"
    | OrderStatusType;

export const OrdersPage = () => {

    const navigate = useNavigate();


    // ============================
    // Queries
    // ============================

    const {
        data: orders = [],
        isLoading,
    } = useGetAllOrders();

    // ============================
    // UI State
    // ============================

    const [search, setSearch] = useState("");

    const [statusFilter, setStatusFilter] =
        useState<StatusFilter>("ALL");

    const [selectedOrder, setSelectedOrder] =
        useState<OrderWithItems | null>(null);

    const [dialogOpen, setDialogOpen] =
        useState(false);

    const [statusDialogOpen, setStatusDialogOpen] =
        useState(false);

    const [menuAnchor, setMenuAnchor] =
        useState<HTMLElement | null>(null);

    const updateStatusMutation =
        useUpdateOrderStatus();
    // ============================
    // Handlers
    // ============================

    const handleOrderClick = (
        order: OrderWithItems,
    ) => {
        setSelectedOrder(order);
        setDialogOpen(true);
    };

    const handleDialogClose = () => {
        setDialogOpen(false);
    };

    const handleOpenStatusDialog = () => {

        if (!selectedOrder) {
            return;
        }

        setStatusDialogOpen(true);
    };


    const handleMenuOpen = (
        event: React.MouseEvent<HTMLElement>,
        order: OrderWithItems,
    ) => {
        setSelectedOrder(order);
        setMenuAnchor(event.currentTarget);
    };

    const handleMenuClose = () => {
        setMenuAnchor(null);
    };

    const handleResetFilters = () => {
        setSearch("");
        setStatusFilter("ALL");
    };

    // ============================
    // Filtering
    // ============================

    const filteredOrders = useMemo(() => {

        const keyword = search.trim().toLowerCase();

        return orders.filter(({order}) => {

            const matchesStatus =
                statusFilter === "ALL" ||
                order.status === statusFilter;

            const searchText = [
                order.id,
                order.customerName,
                order.customerPhone,
                order.tableId,
                order.orderType,
                order.status,
            ]
                .filter(Boolean)
                .join(" ")
                .toLowerCase();

            return (
                matchesStatus &&
                searchText.includes(keyword)
            );
        });

    }, [orders, search, statusFilter]);

    // ============================
    // Statistics
    // ============================

    const stats = useMemo(() => {

        const totalOrders =
            orders.length;

        const pendingOrders =
            orders.filter(
                (o) =>
                    o.order.status ===
                    OrderStatus.PENDING,
            ).length;

        const preparingOrders =
            orders.filter(
                (o) =>
                    o.order.status ===
                    OrderStatus.PREPARING,
            ).length;

        const readyOrders =
            orders.filter(
                (o) =>
                    o.order.status ===
                    OrderStatus.READY,
            ).length;

        return {
            totalOrders,
            pendingOrders,
            preparingOrders,
            readyOrders,
        };

    }, [orders]);

    // ============================
    // Loading
    // ============================

    if (isLoading) {
        return <OrdersLoading/>;
    }

    // ============================
    // Render
    // ============================

    return (
        <Container maxWidth="xl">
            <Stack spacing={3}>

                <OrdersStats
                    totalOrders={stats.totalOrders}
                    pendingOrders={stats.pendingOrders}
                    preparingOrders={stats.preparingOrders}
                    readyOrders={stats.readyOrders}
                />

                {/* Toolbar */}

                <OrdersToolbar
                    search={search}
                    status={statusFilter}
                    onSearchChange={setSearch}
                    onStatusChange={setStatusFilter}
                />

                {/* Empty */}

                {filteredOrders.length === 0 ? (
                    <OrdersEmpty
                        hasFilters={
                            search.trim().length > 0 ||
                            statusFilter !== "ALL"
                        }
                        onResetFilters={
                            handleResetFilters
                        }
                    />
                ) : (
                    <OrdersTable
                        orders={filteredOrders}
                        onOrderClick={
                            handleOrderClick
                        }
                        onOrderMenuClick={
                            handleMenuOpen
                        }
                    />
                )}

            </Stack>


            {/* Details Dialog */}

            <OrderDetailsDialog
                open={dialogOpen}
                order={selectedOrder ?? undefined}
                onClose={handleDialogClose}
                onPrint={() => {
                    console.log(
                        "Print Order",
                        selectedOrder,
                    );
                }}
                onStatusChange={(
                    status,
                ) => {
                    console.log(
                        status,
                    );
                }}
            />

            <OrderStatusDialog

                open={statusDialogOpen}

                order={
                    selectedOrder?.order
                }

                loading={
                    updateStatusMutation.isPending
                }

                onClose={() =>
                    setStatusDialogOpen(false)
                }


                onSubmit={(data) => {


                    if (!selectedOrder) {
                        return;
                    }


                    updateStatusMutation.mutate({

                        orderId:
                        selectedOrder.order.id,

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

            {/* Actions Menu */}

            <OrderActionsMenu
                anchorEl={menuAnchor}
                open={Boolean(menuAnchor)}
                onClose={handleMenuClose}
                onView={() => {
                    handleMenuClose();

                    if (
                        selectedOrder
                    ) {
                        setDialogOpen(
                            true,
                        );
                    }
                }}
                onChangeStatus={() => {

                    handleMenuClose();

                    handleOpenStatusDialog();

                }}
                onPrint={() => {
                    handleMenuClose();

                    console.log(
                        "Print",
                        selectedOrder,
                    );
                }}

                onEdit={() => {
                    handleMenuClose();

                    if (!selectedOrder) return;

                    navigate(
                        `/orders/${selectedOrder.order.id}/edit`,
                    );
                }}
                onDelete={() => {
                    handleMenuClose();

                    console.log(
                        "Delete",
                        selectedOrder,
                    );
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

                    left: 24,
                    bottom: 24,

                    bgcolor:
                        "#10281A",

                    color: "#fff",

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