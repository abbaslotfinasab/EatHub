import {
    Box,
    Divider,
    Stack,
    Typography,
} from "@mui/material";

import type {OrderWithItems} from "../../../../domain/entities/product/order/OrderWithItems";

import {formatCurrency} from "../../../utils/formatCurrency";
import {formatDateTime} from "../../../utils/formatDateTime";


interface ReceiptThermalProps {

    /**
     * Element ID used by usePrintReceipt.
     */
    id?: string;

    /**
     * Order data.
     */
    order: OrderWithItems;

    /**
     * Thermal printer paper width.
     */
    paper?: 58 | 80;

}


export function ReceiptThermal({

                                   id,

                                   order,

                                   paper = 80,

                               }: ReceiptThermalProps) {

    const data = order.order;

    const width =
        paper === 58
            ? "58mm"
            : "80mm";


    return (

        <Box
            id={id}

            dir="rtl"

            sx={{
                width,

                minWidth: width,

                maxWidth: width,

                bgcolor: "#ffffff",

                color: "#000000",

                mx: "auto",

                px: paper === 58 ? 1 : 1.5,

                py: 1.5,

                overflow: "hidden",

                fontFamily:
                    '"Vazirmatn", "Tahoma", Arial, sans-serif',

                fontSize:
                    paper === 58
                        ? "10px"
                        : "11px",

                lineHeight: 1.5,

                WebkitPrintColorAdjust: "exact",

                printColorAdjust: "exact",

                "@media print": {

                    width,

                    minWidth: width,

                    maxWidth: width,

                    margin: 0,

                    padding:
                        paper === 58
                            ? "4px"
                            : "6px",

                    boxShadow: "none",

                    borderRadius: 0,

                },

            }}
        >

            {/* =====================================================
                Header
            ===================================================== */}

            <Stack
                sx={{
                    alignItems: "center",
                    gap: 0.4,
                    textAlign: "center",
                }}
            >

                <Typography
                    sx={{
                        fontSize:
                            paper === 58
                                ? 16
                                : 18,

                        fontWeight: 800,

                        lineHeight: 1.3,

                        color: "#000",
                    }}
                >
                    {data.businessName ?? "رستوران"}
                </Typography>


                <Typography
                    sx={{
                        fontSize:
                            paper === 58
                                ? 11
                                : 12,

                        fontWeight: 700,
                    }}
                >
                    رسید سفارش
                </Typography>


                <Typography
                    sx={{
                        fontSize:
                            paper === 58
                                ? 9
                                : 10,

                        color: "#000",
                    }}
                >
                    شماره سفارش: #{data.id}
                </Typography>

            </Stack>


            <ThermalDivider/>


            {/* =====================================================
                Order Information
            ===================================================== */}

            <Stack spacing={0.3}>

                <InfoRow
                    label="تاریخ"
                    value={
                        data.createdAt
                            ? formatDateTime(data.createdAt)
                            : "-"
                    }
                />


                <InfoRow
                    label="مشتری"
                    value={
                        data.customerName ??
                        "مشتری عمومی"
                    }
                />


                {data.customerPhone && (

                    <InfoRow
                        label="تلفن"
                        value={data.customerPhone}
                    />

                )}


                <InfoRow
                    label="نوع سفارش"
                    value={
                        getOrderTypeLabel(
                            data.orderType,
                        )
                    }
                />


                {data.tableId && (

                    <InfoRow
                        label="میز"
                        value={String(data.tableId)}
                    />

                )}

            </Stack>


            <ThermalDivider/>


            {/* =====================================================
                Items Header
            ===================================================== */}

            <Box
                sx={{
                    display: "grid",

                    gridTemplateColumns:
                        paper === 58
                            ? "1fr auto"
                            : "1fr 65px 75px",

                    gap: 0.5,

                    fontWeight: 800,

                    fontSize:
                        paper === 58
                            ? 9
                            : 10,

                    mb: 0.5,
                }}
            >

                <Typography
                    sx={{
                        fontSize: "inherit",
                        fontWeight: "inherit",
                    }}
                >
                    کالا / محصول
                </Typography>


                {paper === 80 && (

                    <Typography
                        align="center"
                        sx={{
                            fontSize: "inherit",
                            fontWeight: "inherit",
                        }}
                    >
                        تعداد
                    </Typography>

                )}


                <Typography
                    align="left"
                    sx={{
                        fontSize: "inherit",
                        fontWeight: "inherit",
                    }}
                >
                    مبلغ
                </Typography>

            </Box>


            {/* =====================================================
                Items
            ===================================================== */}

            <Stack spacing={0.8}>

                {order.orderItems.map((item) => (

                    <Box
                        key={item.id}
                        sx={{
                            breakInside: "avoid",
                        }}
                    >

                        {paper === 58 ? (

                            /*
                             * 58mm
                             * Compact layout
                             */

                            <Stack spacing={0.2}>

                                <Typography
                                    sx={{
                                        fontSize: 10,
                                        fontWeight: 700,
                                        lineHeight: 1.3,
                                    }}
                                >
                                    {item.menuItemName}
                                </Typography>


                                <Stack
                                    sx={{
                                        flexDirection: "row",
                                        justifyContent: "space-between",
                                        alignItems: "center",
                                    }}
                                >

                                    <Typography
                                        sx={{
                                            fontSize: 9,
                                        }}
                                    >
                                        {item.quantity}
                                        {" × "}
                                        {formatCurrency(
                                            item.unitPrice,
                                        )}
                                    </Typography>


                                    <Typography
                                        sx={{
                                            fontSize: 10,
                                            fontWeight: 700,
                                        }}
                                    >
                                        {formatCurrency(
                                            item.totalPrice,
                                        )}
                                    </Typography>

                                </Stack>

                            </Stack>

                        ) : (

                            /*
                             * 80mm
                             * More spacious layout
                             */

                            <Box
                                sx={{
                                    display: "grid",

                                    gridTemplateColumns:
                                        "1fr 65px 75px",

                                    gap: 0.5,

                                    alignItems: "start",
                                }}
                            >

                                <Box>

                                    <Typography
                                        sx={{
                                            fontSize: 10,
                                            fontWeight: 700,
                                            lineHeight: 1.35,
                                        }}
                                    >
                                        {item.menuItemName}
                                    </Typography>


                                    {item.notes && (

                                        <Typography
                                            sx={{
                                                fontSize: 8,
                                                mt: 0.2,
                                                color: "#333",
                                            }}
                                        >
                                            {item.notes}
                                        </Typography>

                                    )}

                                </Box>


                                <Typography
                                    align="center"
                                    sx={{
                                        fontSize: 9,
                                    }}
                                >
                                    {item.quantity}
                                </Typography>


                                <Typography
                                    align="left"
                                    sx={{
                                        fontSize: 9,
                                        fontWeight: 700,
                                    }}
                                >
                                    {formatCurrency(
                                        item.totalPrice,
                                    )}
                                </Typography>

                            </Box>

                        )}

                    </Box>

                ))}

            </Stack>


            <ThermalDivider/>


            {/* =====================================================
                Summary
            ===================================================== */}

            <Stack spacing={0.35}>

                <SummaryRow
                    label="جمع سفارش"
                    value={formatCurrency(data.subtotal)}
                />


                {Number(data.discount) > 0 && (

                    <SummaryRow
                        label="تخفیف"
                        value={formatCurrency(data.discount)}
                    />

                )}


                {Number(data.tax) > 0 && (

                    <SummaryRow
                        label="مالیات"
                        value={formatCurrency(data.tax)}
                    />

                )}

            </Stack>


            <ThermalDivider/>


            {/* =====================================================
                Total
            ===================================================== */}

            <Box
                sx={{
                    display: "flex",

                    alignItems: "center",

                    justifyContent: "space-between",

                    gap: 1,

                    py: 0.5,
                }}
            >

                <Typography
                    sx={{
                        fontSize:
                            paper === 58
                                ? 12
                                : 13,

                        fontWeight: 900,
                    }}
                >
                    مبلغ قابل پرداخت
                </Typography>


                <Typography
                    sx={{
                        fontSize:
                            paper === 58
                                ? 12
                                : 13,

                        fontWeight: 900,

                        whiteSpace: "nowrap",
                    }}
                >
                    {formatCurrency(data.totalAmount)}
                </Typography>

            </Box>


            <ThermalDivider/>


            {/* =====================================================
                Payment
            ===================================================== */}

            <Stack spacing={0.3}>

                <InfoRow
                    label="وضعیت پرداخت"
                    value={
                        getPaymentStatusLabel(
                            data.paymentStatus,
                        )
                    }
                />


                {data.paymentMethod && (

                    <InfoRow
                        label="روش پرداخت"
                        value={
                            getPaymentMethodLabel(
                                data.paymentMethod,
                            )
                        }
                    />

                )}

            </Stack>


            {/* =====================================================
                Notes
            ===================================================== */}

            {data.notes && (

                <>

                    <ThermalDivider/>

                    <Box>

                        <Typography
                            sx={{
                                fontSize: 9,
                                fontWeight: 800,
                                mb: 0.2,
                            }}
                        >
                            توضیحات
                        </Typography>


                        <Typography
                            sx={{
                                fontSize: 9,
                                lineHeight: 1.5,
                            }}
                        >
                            {data.notes}
                        </Typography>

                    </Box>

                </>

            )}


            <ThermalDivider/>


            {/* =====================================================
                Footer
            ===================================================== */}

            <Stack
                sx={{
                    alignItems: "center",
                    gap: 0.3,
                    textAlign: "center",
                }}
            >
                <Typography
                    sx={{
                        fontSize:
                            paper === 58
                                ? 9
                                : 10,

                        fontWeight: 700,
                    }}
                >
                    از خرید شما سپاسگزاریم
                </Typography>


                <Typography
                    sx={{
                        fontSize: 8,
                    }}
                >
                    سفارش شما با موفقیت ثبت شد
                </Typography>

            </Stack>

        </Box>

    );

}


/* ================================================================
   Components
================================================================ */


/**
 * Dashed divider optimized for thermal printers.
 */
function ThermalDivider() {

    return (

        <Divider
            sx={{
                my: 0.8,

                borderColor: "#000",

                borderStyle: "dashed",

                opacity: 1,

                "&::before, &::after": {
                    borderColor: "#000",
                },
            }}
        />

    );

}


/**
 * Generic information row.
 */
interface InfoRowProps {

    label: string;

    value: React.ReactNode;

}


function InfoRow({
                     label,
                     value,
                 }: InfoRowProps) {

    return (

        <Box
            sx={{
                display: "flex",

                justifyContent: "space-between",

                alignItems: "baseline",

                gap: 1,

                direction: "rtl",
            }}
        >

            <Typography
                sx={{
                    fontSize: 9,

                    color: "#333",

                    whiteSpace: "nowrap",
                }}
            >
                {label}
            </Typography>


            <Typography
                sx={{
                    fontSize: 9,

                    fontWeight: 600,

                    color: "#000",

                    textAlign: "left",

                    wordBreak: "break-word",
                }}
            >
                {value}
            </Typography>

        </Box>

    );

}


/**
 * Summary row.
 */
interface SummaryRowProps {

    label: string;

    value: React.ReactNode;

}


function SummaryRow({
                        label,
                        value,
                    }: SummaryRowProps) {

    return (

        <Box
            sx={{
                display: "flex",

                justifyContent: "space-between",

                alignItems: "center",

                gap: 1,
            }}
        >

            <Typography
                sx={{
                    fontSize: 9,
                }}
            >
                {label}
            </Typography>


            <Typography
                sx={{
                    fontSize: 9,

                    fontWeight: 600,

                    whiteSpace: "nowrap",
                }}
            >
                {value}
            </Typography>

        </Box>

    );

}


/* ================================================================
   Labels
================================================================ */


/**
 * Order type label.
 */
function getOrderTypeLabel(
    type: string,
): string {

    switch (type) {

        case "dine_in":
            return "حضوری";

        case "takeaway":
            return "بیرون‌بر";

        case "delivery":
            return "ارسال";

        default:
            return type;

    }

}


/**
 * Payment status label.
 */
function getPaymentStatusLabel(
    status?: string,
): string {

    switch (status) {

        case "paid":
            return "پرداخت شده";

        case "unpaid":
            return "پرداخت نشده";

        case "pending":
            return "در انتظار پرداخت";

        case "failed":
            return "پرداخت ناموفق";

        case "refunded":
            return "مسترد شده";

        default:
            return "-";

    }

}


/**
 * Payment method label.
 */
function getPaymentMethodLabel(
    method: string,
): string {

    switch (method) {

        case "cash":
            return "نقدی";

        case "card":
            return "کارت بانکی";

        case "customer_account":
            return "حساب مشتری";

        default:
            return method;

    }

}

