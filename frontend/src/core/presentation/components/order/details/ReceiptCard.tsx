// components/order/details/ReceiptCard.tsx

import {Divider, IconButton, Paper, Stack} from "@mui/material";

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

    onClose: () => void;

    onPrint?: () => void;

    onDownloadPdf?: () => void;

    showActions?: boolean;

    showCloseButton?: boolean;
}

export function ReceiptCard({
                                order,

                                onClose,

                                onPrint,

                                onDownloadPdf,

                                showActions = true,

                                showCloseButton = true,

                            }: ReceiptCardProps) {

    const data = order.order;

    return (

        <Paper
            id="receipt-card"
            elevation={0}
            sx={{
                overflow: "hidden",
                borderRadius: 4,
                bgcolor: "background.paper",
            }}
        >

            <Stack>

                {/* =========================
                    Header
                ========================= */}

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
                            }}
                        >
                            <CloseRoundedIcon/>
                        </IconButton>

                    )}

                    <ReceiptHeader
                        order={data}
                    />

                </Stack>

                {/* =========================
                    Body
                ========================= */}

                <Stack
                    spacing={3}
                    sx={{
                        p: 3,
                    }}
                >

                    <ReceiptCustomer
                        order={data}
                    />

                    <Divider/>

                    <ReceiptOrderInfo
                        order={data}
                    />

                    <Divider/>

                    <ReceiptItems
                        items={order.orderItems}
                    />

                    <Divider/>

                    <ReceiptSummary
                        order={data}
                    />

                    <Divider/>

                    <ReceiptPayment
                        order={data}
                    />

                    {data.notes && (
                        <>
                            <Divider/>

                            <ReceiptNotes
                                notes={data.notes}
                            />
                        </>
                    )}

                </Stack>

                {/* =========================
                    Footer
                ========================= */}

                {showActions && (

                    <>

                        <Divider/>

                        <ReceiptActions
                            onPrint={onPrint}
                            onDownloadPdf={onDownloadPdf}
                            onClose={onClose}
                        />

                    </>

                )}

            </Stack>

        </Paper>

    );

}