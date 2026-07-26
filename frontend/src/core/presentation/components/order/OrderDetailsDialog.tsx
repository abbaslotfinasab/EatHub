// presentation/components/order/OrderDetailsDialog.tsx

import {
    Dialog,
    DialogContent,
    IconButton,
    Stack,
} from "@mui/material";

import CloseRoundedIcon from "@mui/icons-material/CloseRounded";

import type {OrderStatusType} from "../../../domain/entities/product/order/Order";
import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems";
import {ReceiptHeader} from "./details/ReceiptHeader";
import {ReceiptOrderInfo} from "./details/ReceiptOrderInfo";
import {ReceiptItems} from "./details/ReceiptItems";
import {ReceiptSummary} from "./details/ReceiptSummary";
import {ReceiptPayment} from "./details/ReceiptPayment";
import {ReceiptActions} from "./details/ReceiptActions";
import {ReceiptNotes} from "./details/ReceiptNotes.tsx";
import {ReceiptCustomer} from "./details/ReceiptCustomer.tsx";


interface OrderDetailsDialogProps {
    open: boolean;

    order?: OrderWithItems;

    loading?: boolean;

    onClose(): void;

    onPrint?(): void;

    onStatusChange?(
        status: OrderStatusType,
    ): void;
}

export const OrderDetailsDialog = ({
                                       open,
                                       order,
                                       onClose,
                                       onPrint,
                                   }: OrderDetailsDialogProps) => {

    if (!order) {
        return null;
    }

    const data = order.order;

    return (

        <Dialog
            open={open}
            onClose={onClose}
            fullWidth
            maxWidth="sm"
            slotProps={{
                paper: {
                    sx: {
                        borderRadius: 4,
                        overflow: "hidden",
                    },
                },
            }}
        >

            <DialogContent
                sx={{
                    p: 0,
                    bgcolor: "#fafafa",
                }}
            >

                <Stack>

                    <Stack
                        sx={{
                            position: "relative",
                        }}
                    >

                        <IconButton
                            onClick={onClose}
                            sx={{
                                position: "absolute",
                                top: 12,
                                left: 12,
                                zIndex: 10,
                                bgcolor: "background.paper",
                                boxShadow: 1,

                                "&:hover": {
                                    bgcolor: "background.paper",
                                },
                            }}
                        >
                            <CloseRoundedIcon/>
                        </IconButton>

                        <ReceiptHeader
                            order={data}
                        />

                    </Stack>

                    <Stack
                        spacing={2}
                        sx={{
                            p: 3,
                        }}
                    >

                        <ReceiptCustomer
                            order={data}
                        />

                        <ReceiptOrderInfo
                            order={data}
                        />

                        <ReceiptItems
                            items={
                                order.orderItems
                            }
                        />

                        <ReceiptSummary
                            order={data}
                        />

                        <ReceiptPayment
                            order={data}
                        />

                        <ReceiptNotes
                            notes={data.notes}
                        />

                    </Stack>

                    <ReceiptActions
                        onPrint={onPrint}
                        onClose={onClose}
                    />

                </Stack>

            </DialogContent>

        </Dialog>

    );

};