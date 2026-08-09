// components/order/details/ReceiptCard.tsx

import {
    Divider,
    IconButton,
    Paper,
    Stack,
} from "@mui/material";

import CloseRoundedIcon from "@mui/icons-material/CloseRounded";

import type {OrderWithItems} from "../../../../domain/entities/product/order/OrderWithItems";

import {ReceiptHeader} from "./ReceiptHeader";
import {ReceiptCustomer} from "./ReceiptCustomer";
import {ReceiptOrderInfo} from "./ReceiptOrderInfo";
import {ReceiptItems} from "./ReceiptItems";
import {ReceiptSummary} from "./ReceiptSummary";
import {ReceiptPayment} from "./ReceiptPayment";
import {ReceiptNotes} from "./ReceiptNotes";
import {ReceiptActions} from "./ReceiptActions";


interface ReceiptCardProps {

    order: OrderWithItems;

    onClose?(): void;

    onPrint58?(): void;

    onPrint80?(): void;

    onDownloadPdf?(): void;

    onEdit?(): void;

    onChangeStatus?(): void;

    /**
     * نمایش بخش اکشن‌های پایین رسید
     *
     * برای Preview صفحه true
     * برای Print / PDF false
     */
    showActions?: boolean;

    /**
     * نمایش دکمه بستن روی Header
     *
     * برای Preview صفحه true
     * برای Print / PDF false
     */
    showCloseButton?: boolean;

    /**
     * شناسه HTML element
     */
    id?: string;
}


export function ReceiptCard({

    order,

    onClose,

    onPrint58,

    onPrint80,

    onDownloadPdf,

    onEdit,

    onChangeStatus,

    showActions = true,

    showCloseButton = true,

    id = "receipt-card",

}: ReceiptCardProps) {

    const data = order.order;


    return (

        <Paper
            id={id}
            elevation={0}

            sx={{
                overflow: "hidden",

                borderRadius: 1,

                bgcolor: "background.paper",

                color: "text.primary",

                /**
                 * مهم:
                 * در Print/PDF هیچ shadow یا radius اضافه‌ای
                 * وارد خروجی نشود.
                 */
                "@media print": {

                    borderRadius: 0,

                    boxShadow: "none",

                },
            }}
        >

            <Stack>

                {/* =====================================================
                    Header
                ===================================================== */}

                <Stack
                    sx={{
                        position: "relative",
                    }}
                >

                    {showCloseButton && onClose && (

                        <IconButton
                            onClick={onClose}

                            sx={{
                                position: "absolute",

                                top: 16,

                                left: 16,

                                zIndex: 20,

                                bgcolor: "background.paper",

                                boxShadow: 2,

                                "&:hover": {
                                    bgcolor: "background.paper",
                                },

                                "@media print": {
                                    display: "none",
                                },
                            }}
                        >

                            <CloseRoundedIcon/>

                        </IconButton>

                    )}


                    <ReceiptHeader
                        order={data}
                    />

                </Stack>


                {/* =====================================================
                    Body
                ===================================================== */}

                <Stack
                    spacing={3}

                    sx={{
                        p: 3,

                        /**
                         * در خروجی چاپ فاصله‌ها کمی جمع‌تر
                         * می‌شوند تا رسید تمیزتر باشد.
                         */
                        "@media print": {

                            p: 0,

                        },
                    }}
                >

                    {/* Customer */}

                    <ReceiptCustomer
                        order={data}
                    />


                    <Divider/>


                    {/* Order Info */}

                    <ReceiptOrderInfo
                        order={data}
                    />


                    <Divider/>


                    {/* Items */}

                    <ReceiptItems
                        items={order.orderItems}
                    />


                    <Divider/>


                    {/* Summary */}

                    <ReceiptSummary
                        order={data}
                    />


                    <Divider/>


                    {/* Payment */}

                    <ReceiptPayment
                        order={data}
                    />


                    {/* Notes */}

                    {data.notes && (

                        <>

                            <Divider/>

                            <ReceiptNotes
                                notes={data.notes}
                            />

                        </>

                    )}

                </Stack>


                {/* =====================================================
                    Footer / Actions
                ===================================================== */}

                {showActions && (

                    <>

                        <Divider/>

                        <ReceiptActions

                            onPrint58={
                                onPrint58
                            }

                            onPrint80={
                                onPrint80
                            }

                            onDownloadPdf={
                                onDownloadPdf
                            }

                            onEdit={
                                onEdit
                            }

                            onChangeStatus={
                                onChangeStatus
                            }


                        />

                    </>

                )}

            </Stack>

        </Paper>

    );

}