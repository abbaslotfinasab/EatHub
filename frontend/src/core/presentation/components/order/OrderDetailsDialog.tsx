// presentation/components/order/OrderDetailsDialog.tsx

import {
    Dialog,
    DialogContent,
} from "@mui/material";


import type {OrderStatusType} from "../../../domain/entities/product/order/Order";
import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems";
import {ReceiptCard} from "./details/ReceiptCard.tsx";
import {usePrintReceipt} from "../../hooks/usePrintReceipt.ts";


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
                                   }: OrderDetailsDialogProps) => {

    const {
        printReceipt80,
        exportPdf,
    } = usePrintReceipt();


    if (!order) {
        return null;
    }


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
                    },
                },
            }}
        >

            <DialogContent
                sx={{
                    p: 0,
                    bgcolor: "#f5f5f5",
                }}
            >

                <ReceiptCard
                    order={order}
                    onClose={onClose}
                    onPrint={printReceipt80}
                    onDownloadPdf={exportPdf}

                />


            </DialogContent>

        </Dialog>

    );

};