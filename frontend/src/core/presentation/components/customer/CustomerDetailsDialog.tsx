import {
    AccountBalanceWalletOutlined,
    Close as CloseIcon,
    EditOutlined,
} from "@mui/icons-material";

import {
    Avatar,
    Box,
    Button,
    Dialog,
    DialogContent,
    DialogTitle,
    Divider,
    IconButton,
    Stack,
    Typography,
} from "@mui/material";

import Grid from "@mui/material/Grid";

import type {CustomerDetail} from "../../../domain/entities/product/customer/CustomerDetail";

import {formatCurrency} from "../../utils/formatCurrency";
import {formatDate} from "../../utils/formatDate";

import {CustomerTransactionTimeline} from "./CustomerTransactionTimeline";

interface CustomerDetailsDialogProps {

    open: boolean;

    loading?: boolean;

    customer?: CustomerDetail | null;

    onClose: () => void;

    onEdit: () => void;

    onRecharge: () => void;

    onOrderClick?(orderId: string): void;
}

export function CustomerDetailsDialog({
                                          open,
                                          loading = false,
                                          customer,
                                          onClose,
                                          onEdit,
                                          onRecharge,
                                          onOrderClick,
                                      }: CustomerDetailsDialogProps) {

    if (!open) {
        return null;
    }

    if (loading) {

        return (
            <Dialog
                open={open}
                onClose={onClose}
                maxWidth="md"
                fullWidth
            >
                <DialogContent
                    sx={{
                        py: 8,
                        textAlign: "center",
                    }}
                >
                    <Typography>
                        در حال دریافت اطلاعات...
                    </Typography>
                </DialogContent>
            </Dialog>
        );
    }

    if (!customer) {
        return null;
    }

    const info = customer.customer;

    const account = customer.account;

    const balance =
        account?.balance ?? 0;

    const transactions =
        customer.transactions ?? [];

    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="md"
            fullWidth
        >

            <DialogTitle
                sx={{
                    p: 3,
                }}
            >

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >

                    <Stack
                        sx={{
                            flexDirection: "row",
                            gap: 2,
                            alignItems: "center",
                        }}
                    >
                        <Avatar
                            sx={{
                                width: 56,
                                height: 56,
                                bgcolor: "primary.main",
                                fontWeight: 700,
                                fontSize: 24,
                            }}
                        >
                            {info.name.charAt(0)}
                        </Avatar>

                        <Box>

                            <Typography
                                variant="h6"
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                {info.name}
                            </Typography>

                            <Typography
                                color="text.secondary"
                            >
                                {info.phone}
                            </Typography>

                        </Box>

                    </Stack>

                    <IconButton
                        onClick={onClose}
                    >
                        <CloseIcon/>
                    </IconButton>

                </Stack>

            </DialogTitle>

            <Divider/>

            <DialogContent
                sx={{
                    p: 3,
                }}
            >

                {/* =========================
                    Customer Summary
                ========================== */}

                <Grid
                    container
                    spacing={2}
                >

                    <Grid
                        size={{
                            xs: 12,
                            sm: 6,
                        }}
                    >
                        <InfoItem
                            title="مانده حساب"
                            value={formatCurrency(
                                balance,
                            )}
                            color={
                                balance > 0
                                    ? "success.main"
                                    : balance < 0
                                        ? "error.main"
                                        : "text.primary"
                            }
                        />
                    </Grid>

                    <Grid
                        size={{
                            xs: 12,
                            sm: 6,
                        }}
                    >
                        <InfoItem
                            title="تعداد سفارش"
                            value={String(
                                0
                            )}
                        />
                    </Grid>

                    <Grid
                        size={{
                            xs: 12,
                            sm: 6,
                        }}
                    >
                        <InfoItem
                            title="مجموع خرید"
                            value={formatCurrency(
                                0
                            )}
                        />
                    </Grid>

                    <Grid
                        size={{
                            xs: 12,
                            sm: 6,
                        }}
                    >
                        <InfoItem
                            title="تاریخ عضویت"
                            value={
                                info.createdAt
                                    ? formatDate(
                                        info.createdAt,
                                    )
                                    : "-"
                            }
                        />
                    </Grid>

                </Grid>

                {/* =========================
                    Transactions
                ========================== */}

                <Divider
                    sx={{
                        my: 3,
                    }}
                />

                <Typography
                    sx={{
                        mb: 2,
                        fontWeight: 700,
                    }}
                >
                    تراکنش‌های حساب
                </Typography>

                <Box
                    sx={{
                        maxHeight: 360,
                        overflowY: "auto",
                        pr: 1,
                    }}
                >
                    <CustomerTransactionTimeline
                        transactions={
                            transactions
                        }
                        onOrderClick={
                            onOrderClick
                        }
                    />
                </Box>

                {/* =========================
                    Actions
                ========================== */}

                <Divider
                    sx={{
                        my: 3,
                    }}
                />

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 2,
                        justifyContent: "flex-end",
                    }}
                >

                    <Button
                        variant="outlined"
                        startIcon={
                            <EditOutlined/>
                        }
                        onClick={onEdit}
                    >
                        ویرایش
                    </Button>

                    <Button
                        variant="contained"
                        startIcon={
                            <AccountBalanceWalletOutlined/>
                        }
                        onClick={onRecharge}
                    >
                        شارژ حساب
                    </Button>

                </Stack>

            </DialogContent>

        </Dialog>
    );
}

interface InfoItemProps {
    title: string;
    value: string;
    color?: string;
}

function InfoItem({
                      title,
                      value,
                      color = "text.primary",
                  }: InfoItemProps) {

    return (
        <Box
            sx={{
                p: 2,
                height: "100%",
                border: 1,
                borderRadius: 2,
                borderColor: "divider",
            }}
        >

            <Typography
                variant="caption"
                color="text.secondary"
            >
                {title}
            </Typography>

            <Typography
                sx={{
                    mt: 1,
                    fontWeight: 700,
                }}
                color={color}
            >
                {value}
            </Typography>

        </Box>
    );
}

