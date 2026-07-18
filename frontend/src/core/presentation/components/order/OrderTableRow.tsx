import MoreVertRoundedIcon from "@mui/icons-material/MoreVertRounded";
import {
    IconButton,
    TableCell,
    TableRow,
    Tooltip,
} from "@mui/material";

import {OrderStatusChip} from "./OrderStatusChip";
import type {OrderWithItems} from "../../../domain/entities/product/order/OrderWithItems";
import {formatDateTime} from "../../utils/formatDateTime.ts";
import {formatCurrency} from "../../utils/formatCurrency.ts";
import {ORDER_TYPE_CONFIG} from "../../../../config/constants.ts";

interface OrderTableRowProps {
    order: OrderWithItems;
    onClick?: (order: OrderWithItems) => void;
    onMenuClick?: (
        event: React.MouseEvent<HTMLElement>,
        order: OrderWithItems,
    ) => void;
}



export const OrderTableRow = ({
                                  order,
                                  onClick,
                                  onMenuClick,
                              }: OrderTableRowProps) => {
    return (
        <TableRow
            hover
            onClick={() => onClick?.(order)}
            sx={{
                cursor: "pointer",
                "&:last-child td": {
                    borderBottom: 0,
                },
            }}
        >
            <TableCell>#{order.order.id}</TableCell>

            <TableCell>{order.order.customerName}</TableCell>

            <TableCell>
                {ORDER_TYPE_CONFIG[order.order.orderType].label}
            </TableCell>

            <TableCell>
                {order.order.tableId ?? "-"}
            </TableCell>

            <TableCell>{order.order.notes}</TableCell>

            <TableCell>
                {formatCurrency(order.order.totalAmount)}
            </TableCell>

            <TableCell>
                <OrderStatusChip status={order.order.status}/>
            </TableCell>

            <TableCell>{formatDateTime(order.order.createdAt)}</TableCell>

            <TableCell
                align="right"
                onClick={(e) => e.stopPropagation()}
            >
                <Tooltip title="عملیات">
                    <IconButton
                        size="small"
                        onClick={(e) =>
                            onMenuClick?.(e, order)
                        }
                    >
                        <MoreVertRoundedIcon fontSize="small"/>
                    </IconButton>
                </Tooltip>
            </TableCell>
        </TableRow>
    );
};