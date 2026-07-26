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

import CloseIcon from "@mui/icons-material/Close";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import AccountBalanceWalletOutlinedIcon from "@mui/icons-material/AccountBalanceWalletOutlined";

import type {CustomerDetail} from "../../../domain/entities/product/customer/CustomerDetail";
import {formatCurrency} from "../../utils/formatCurrency";
import {formatDate} from "../../utils/formatDate.ts";


interface CustomerDetailsDialogProps {

    open: boolean;

    loading?: boolean;

    customer?: CustomerDetail | null;

    onClose: () => void;

    onEdit: () => void;

    onRecharge: () => void;

}

export function CustomerDetailsDialog({

                                          open,

                                          loading,

                                          customer,

                                          onClose,

                                          onEdit,

                                          onRecharge,

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

    const balance = account?.balance ?? 0;

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

                <Grid
                    container
                    spacing={2}
                >

                    <Grid
                        size={{
                            xs: 12,
                            md: 6,
                        }}
                    >
                        <InfoItem
                            title="مانده حساب"
                            value={formatCurrency(balance)}
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
                            md: 6,
                        }}
                    >
                        <InfoItem
                            title="تعداد سفارش"
                            value={`${info.name ?? 0}`}
                        />
                    </Grid>

                    <Grid
                        size={{
                            xs: 12,
                            md: 6,
                        }}
                    >
                        <InfoItem
                            title="مجموع خرید"
                            value={formatCurrency(
                                customer?.account?.balance ?? 0,
                            )}
                        />
                    </Grid>

                    <Grid
                        size={{
                            xs: 12,
                            md: 6,
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
                            <EditOutlinedIcon/>
                        }
                        onClick={onEdit}
                    >
                        ویرایش
                    </Button>

                    <Button
                        variant="contained"
                        startIcon={
                            <AccountBalanceWalletOutlinedIcon/>
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