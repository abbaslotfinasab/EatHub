import CloseIcon from "@mui/icons-material/Close";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import AccountBalanceWalletOutlinedIcon from "@mui/icons-material/AccountBalanceWalletOutlined";
import {
    Avatar,
    Box,
    Button,
    Dialog,
    DialogContent,
    DialogTitle,
    Divider,
    Grid,
    IconButton,
    Stack,
    Typography,
} from "@mui/material";
import {formatCurrency} from "../../utils/formatCurrency.ts";
import {formatDate} from "../../utils/formatDate.ts";
import type {CustomerListItem} from "../../../domain/entities/product/customer/CustomerListItem.ts";


interface CustomerDetailsDialogProps {
    open: boolean;

    customer?: CustomerListItem | null;

    onClose(): void;

    onEdit(customer: CustomerListItem): void;

    onRecharge(customer: CustomerListItem): void;
}

export function CustomerDetailsDialog({
                                          open,
                                          customer,
                                          onClose,
                                          onEdit,
                                          onRecharge,
                                      }: CustomerDetailsDialogProps) {

    if (!customer) {
        return null;
    }

    const balance = customer.balance ?? 0;

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
                                fontSize: 24,
                                fontWeight: 700,
                            }}
                        >
                            {customer.name.charAt(0)}
                        </Avatar>

                        <Box>
                            <Typography
                                variant="h6"
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                {customer.name}
                            </Typography>

                            <Typography color="text.secondary">
                                {customer.phone}
                            </Typography>
                        </Box>
                    </Stack>

                    <IconButton onClick={onClose}>
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
                    <Grid size={{xs: 12, md: 6}}>
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

                    <Grid size={{xs: 12, md: 6}}>
                        <InfoItem
                            title="تعداد سفارش"
                            value={`${customer.totalOrders ?? 0}`}
                        />
                    </Grid>

                    <Grid size={{xs: 12, md: 6}}>
                        <InfoItem
                            title="مجموع خرید"
                            value={formatCurrency(customer.totalSpent ?? 0)}
                        />
                    </Grid>

                    <Grid size={{xs: 12, md: 6}}>
                        <InfoItem
                            title="تاریخ عضویت"
                            value={
                                customer.createdAt
                                    ? formatDate(customer.createdAt)
                                    : "-"
                            }
                        />
                    </Grid>
                </Grid>

                <Divider sx={{my: 3}}/>

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 2,
                        justifyContent: "flex-end",
                    }}
                >
                    <Button
                        variant="outlined"
                        startIcon={<EditOutlinedIcon/>}
                        onClick={() => onEdit(customer)}
                    >
                        ویرایش
                    </Button>

                    <Button
                        variant="contained"
                        startIcon={<AccountBalanceWalletOutlinedIcon/>}
                        onClick={() => onRecharge(customer)}
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
                border: 1,
                borderColor: "divider",
                borderRadius: 2,
                p: 2,
                height: "100%",
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