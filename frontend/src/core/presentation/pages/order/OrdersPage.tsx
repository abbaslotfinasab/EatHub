import {useMemo, useState} from "react";

import {Box, Fab} from "@mui/material";

import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems.ts";
import {
    OrderStatus,
    type OrderStatusType,
} from "../../../domain/entities/product/order/Order.ts";
import {useGetOrders} from "../../hooks/order/useGetOrders.ts";
import {OrdersLoading} from "../../components/order/OrdersLoading.tsx";
import {OrderActionsMenu} from "../../components/order/OrderActionsMenu.tsx";
import {OrdersTable} from "../../components/order/OrdersTable.tsx";
import {OrdersToolbar} from "../../components/order/OrdersToolbar.tsx";
import {OrdersStats} from "../../components/order/OrderStats.tsx";
import {OrdersEmpty} from "../../components/order/OrdersEmpty.tsx";
import {OrderDetailsDialog} from "../../components/order/OrderDetailsDialog.tsx";
import AddIcon from "@mui/icons-material/Add";
import {useNavigate} from "react-router-dom";


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
        refetch,
    } = useGetOrders();

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

    const [menuAnchor, setMenuAnchor] =
        useState<HTMLElement | null>(null);

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

        return orders.filter((item) => {

            const order = item.order;

            const matchesStatus =
                statusFilter === "ALL"
                    ? true
                    : order.status === statusFilter;

            const keyword = search.trim().toLowerCase();

            const matchesSearch =
                keyword.length === 0
                    ? true
                    : order.customerName
                        .toLowerCase()
                        .includes(keyword) ||

                    order.customerPhone
                        ?.includes(keyword) ||

                    order.id
                        .toLowerCase()
                        .includes(keyword);

            return (
                matchesStatus &&
                matchesSearch
            );

        });

    }, [
        orders,
        search,
        statusFilter,
    ]);

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
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 3,
            }}
        >
            {/* Statistics */}

            <OrdersStats
                totalOrders={stats.totalOrders.toString()}
                pendingOrders={stats.pendingOrders.toString()}
                preparingOrders={stats.preparingOrders.toString()}
                readyOrders={stats.readyOrders.toString()}
            />

            {/* Toolbar */}

            <OrdersToolbar
                search={search}
                status={statusFilter}
                onSearchChange={setSearch}
                onStatusChange={setStatusFilter}
                onRefresh={() => refetch()}
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

                    if (
                        selectedOrder
                    ) {
                        setDialogOpen(
                            true,
                        );
                    }
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

        </Box>
    );
};