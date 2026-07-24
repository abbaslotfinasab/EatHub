import {useMemo, useState} from "react";

import {
    Container,
    Fab,
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



    const debouncedSearch =
        useDebounce(
            search,
            500
        );



    const orderFilters = useMemo(() => ({


        ...filters,


        search:
            debouncedSearch || undefined,


    }), [

        filters,

        debouncedSearch

    ]);





    /*
    |--------------------------------------------------------------------------
    | Query
    |--------------------------------------------------------------------------
    */


    const {

        data: orders = [],

        isLoading,

    } = useGetAllOrders(
        orderFilters
    );





    /*
    |--------------------------------------------------------------------------
    | UI State
    |--------------------------------------------------------------------------
    */


    const [
        selectedOrder,
        setSelectedOrder
    ] = useState<OrderWithItems | null>(
        null
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

        setFilters({

            ordering:
                "-created_at",

        });

    };



    const handleOrderClick = (
        order: OrderWithItems
    ) => {

        setSelectedOrder(order);

        setDialogOpen(true);

    };



    const handleMenuOpen = (
        event: React.MouseEvent<HTMLElement>,

        order: OrderWithItems,

    ) => {

        setSelectedOrder(order);

        setMenuAnchor(
            event.currentTarget
        );

    };



    const handleMenuClose = () => {

        setMenuAnchor(null);

    };



    const handleOpenStatusDialog = () => {


        if (!selectedOrder) {

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
                orders.length,



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


    },[orders]);





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

                    onSearchChange={
                        setSearch
                    }

                    onFiltersChange={
                        setFilters
                    }

                />




                {
                    orders.length === 0 ? (


                        <OrdersEmpty

                            hasFilters={

                                Boolean(

                                    search ||

                                    Object.keys(
                                        filters
                                    ).length > 1

                                )

                            }


                            onResetFilters={
                                handleResetFilters
                            }

                        />


                    ) : (


                        <OrdersTable

                            orders={orders}


                            onOrderClick={
                                handleOrderClick
                            }


                            onOrderMenuClick={
                                handleMenuOpen
                            }

                        />


                    )
                }


            </Stack>





            <OrderDetailsDialog

                open={dialogOpen}


                order={
                    selectedOrder ?? undefined
                }


                onClose={() =>
                    setDialogOpen(false)
                }


                onPrint={() => {

                    console.log(
                        "Print",
                        selectedOrder
                    );

                }}


                onStatusChange={() => {}}

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



                onSubmit={(data)=>{


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






            <OrderActionsMenu


                anchorEl={menuAnchor}


                open={
                    Boolean(menuAnchor)
                }


                onClose={
                    handleMenuClose
                }



                onView={()=>{


                    handleMenuClose();


                    setDialogOpen(true);


                }}




                onChangeStatus={()=>{


                    handleMenuClose();


                    handleOpenStatusDialog();


                }}




                onPrint={()=>{


                    handleMenuClose();


                    console.log(
                        "Print",
                        selectedOrder
                    );


                }}



                onEdit={()=>{


                    handleMenuClose();



                    if (!selectedOrder) {

                        return;

                    }



                    navigate(

                        `/orders/${selectedOrder.order.id}/edit`

                    );


                }}



                onDelete={()=>{


                    handleMenuClose();


                    console.log(
                        "Delete",
                        selectedOrder
                    );


                }}


            />







            <Fab

                variant="extended"


                onClick={()=>


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



                    "&:hover":{

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