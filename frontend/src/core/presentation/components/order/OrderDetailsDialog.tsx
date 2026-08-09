// presentation/components/order/OrderDetailsDialog.tsx

import {
    Box,
    Dialog,
    DialogContent,
} from "@mui/material";

import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems";

import {ReceiptCard} from "./details/ReceiptCard.tsx";
import {ReceiptThermal} from "./thermal/ReceiptThermal.tsx";

import {usePrintReceipt} from "../../hooks/usePrintReceipt.ts";


interface OrderDetailsDialogProps {

    open: boolean;

    order?: OrderWithItems;

    loading?: boolean;

    onClose(): void;

    onEdit?(): void;

    onStatusChange?(): void;

}


export const OrderDetailsDialog = ({
                                       open,
                                       order,
                                       onClose,
                                       onEdit,
                                       onStatusChange,
                                   }: OrderDetailsDialogProps) => {

    const {
        printReceipt58,
        printReceipt80,
        saveReceiptPdf,
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
                        borderRadius: 1,
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

                {/* =====================================================
                    Receipt Preview
                ===================================================== */}

                <ReceiptCard
                    order={order}
                    onClose={onClose}

                    onPrint58={printReceipt58}
                    onPrint80={printReceipt80}
                    onDownloadPdf={saveReceiptPdf}

                    onEdit={onEdit}
                    onChangeStatus={onStatusChange}
                />

                <Box
                    sx={{
                        position: "fixed",
                        left: "-10000px",
                        top: 0,
                        width: "794px",
                        visibility: "hidden",
                        pointerEvents: "none",
                    }}
                >
                    <ReceiptCard
                        id="receipt-pdf"
                        order={order}
                        showActions={false}
                        showCloseButton={false}
                    />
                </Box>


                {/* =====================================================
                    Thermal Print Templates
                    ===================================================== */}

                <Box
                    sx={{
                        position: "fixed",
                        left: "-10000px",
                        top: 0,
                        visibility: "hidden",
                    }}
                >

                    <ReceiptThermal
                        id="receipt-58"
                        order={order}
                        paper={58}
                    />

                    <ReceiptThermal
                        id="receipt-80"
                        order={order}
                        paper={80}
                    />

                </Box>

            </DialogContent>

        </Dialog>

    );

};