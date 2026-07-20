import {useState, type MouseEvent} from "react";
import {
    Avatar,
    Box,
    Chip,
    IconButton,
    ListItemIcon,
    ListItemText,
    Menu,
    MenuItem,
    TableCell,
    TableRow,
    Typography,
} from "@mui/material";
import {
    AccountBalanceWalletOutlined,
    DeleteOutlined,
    EditOutlined,
    MoreVert,
    VisibilityOutlined,
} from "@mui/icons-material";
import type {CustomerListItem} from "../../../domain/entities/product/customer/CustomerListItem";
import {formatCurrency} from "../../utils/formatCurrency.ts";
import {formatDate} from "../../utils/formatDate.ts";


interface CustomerTableRowProps {
    customer: CustomerListItem;

    onView(customer: CustomerListItem): void;

    onEdit(customer: CustomerListItem): void;

    onRecharge(customer: CustomerListItem): void;

    onDelete(customer: CustomerListItem): void;
}

export function CustomerTableRow({
                                     customer,
                                     onView,
                                     onEdit,
                                     onRecharge,
                                     onDelete,
                                 }: CustomerTableRowProps) {
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

    const open = Boolean(anchorEl);

    const handleMenuOpen = (event: MouseEvent<HTMLElement>) => {
        event.stopPropagation();
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleClick =
        (callback: (customer: CustomerListItem) => void) =>
            (event?: MouseEvent) => {
                event?.stopPropagation();
                handleMenuClose();
                callback(customer);
            };

    const balance = customer.balance ?? 0;

    const balanceColor =
        balance > 0
            ? "success"
            : balance < 0
                ? "error"
                : "default";

    return (
        <>
            <TableRow
                hover
                onClick={() => onView(customer)}
                sx={{
                    cursor: "pointer",
                    transition: "0.2s",

                    "&:hover": {
                        bgcolor: "action.hover",
                    },
                }}
            >
                <TableCell>
                    <Box
                        sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 2,
                        }}
                    >
                        <Avatar
                            sx={{
                                bgcolor: "primary.main",
                                width: 42,
                                height: 42,
                                fontWeight: 700,
                            }}
                        >
                            {customer.name.charAt(0)}
                        </Avatar>

                        <Box>
                            <Typography
                                variant="body2"
                                sx={{
                                    fontWeight: 600,
                                }}
                            >
                                {customer.name}
                            </Typography>

                            <Typography
                                variant="caption"
                                color="text.secondary"
                            >
                                مشتری
                            </Typography>
                        </Box>
                    </Box>
                </TableCell>

                <TableCell>
                    <Typography variant="body2">
                        {customer.phone}
                    </Typography>
                </TableCell>

                <TableCell align="center">
                    <Chip
                        size="small"
                        color={balanceColor}
                        variant={balance === 0 ? "outlined" : "filled"}
                        label={`${balance > 0 ? "+" : ""}${formatCurrency(balance)}`}
                    />
                </TableCell>

                <TableCell align="center">
                    <Typography
                        sx={{
                            fontWeight: 600,
                        }}
                    >
                        {customer.totalOrders ?? 0}
                    </Typography>
                </TableCell>

                <TableCell align="center">
                    <Typography
                        sx={{
                            fontWeight: 600,
                        }}
                    >
                        {formatCurrency(customer.totalSpent ?? 0)}
                    </Typography>
                </TableCell>

                <TableCell align="center">
                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        {customer.createdAt
                            ? formatDate(customer.createdAt)
                            : "-"}
                    </Typography>
                </TableCell>

                <TableCell align="right">
                    <IconButton
                        onClick={handleMenuOpen}
                        size="small"
                    >
                        <MoreVert fontSize="small"/>
                    </IconButton>
                </TableCell>
            </TableRow>

            <Menu
                anchorEl={anchorEl}
                open={open}
                onClose={handleMenuClose}
                anchorOrigin={{
                    vertical: "bottom",
                    horizontal: "right",
                }}
                transformOrigin={{
                    vertical: "top",
                    horizontal: "right",
                }}
            >
                <MenuItem onClick={handleClick(onView)}>
                    <ListItemIcon>
                        <VisibilityOutlined fontSize="small"/>
                    </ListItemIcon>

                    <ListItemText>
                        مشاهده
                    </ListItemText>
                </MenuItem>

                <MenuItem onClick={handleClick(onEdit)}>
                    <ListItemIcon>
                        <EditOutlined fontSize="small"/>
                    </ListItemIcon>

                    <ListItemText>
                        ویرایش
                    </ListItemText>
                </MenuItem>

                <MenuItem onClick={handleClick(onRecharge)}>
                    <ListItemIcon>
                        <AccountBalanceWalletOutlined fontSize="small"/>
                    </ListItemIcon>

                    <ListItemText>
                        شارژ حساب
                    </ListItemText>
                </MenuItem>

                <MenuItem
                    onClick={handleClick(onDelete)}
                    sx={{
                        color: "error.main",
                    }}
                >
                    <ListItemIcon
                        sx={{
                            color: "inherit",
                        }}
                    >
                        <DeleteOutlined fontSize="small"/>
                    </ListItemIcon>

                    <ListItemText>
                        حذف
                    </ListItemText>
                </MenuItem>
            </Menu>
        </>
    );
}