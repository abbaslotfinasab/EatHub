import {
    Card,
    CardContent,
    Typography,
    IconButton,
} from "@mui/material";

import MoreVertIcon from "@mui/icons-material/MoreVert";

import {
    MaterialReactTable,
    type MRT_ColumnDef,
} from "material-react-table";

import { useMemo } from "react";

import { OrderStatusChip } from "./OrderStatusChip";
import type {OrderTableItem} from "../../../domain/entities/product/OrderTableItem.ts";

export const OrdersTable = () => {
    const data = [
        {
            id: "#1024",
            tableNumber: 12,
            itemsCount: 2,
            totalPrice: 450000,
            status: "preparing",
            createdAt: "15 دقیقه قبل",
        },

        {
            id: "#1025",
            tableNumber: 8,
            itemsCount: 5,
            totalPrice: 890000,
            status: "ready",
            createdAt: "8 دقیقه قبل",
        },
    ];

   const columns = useMemo<
    MRT_ColumnDef<OrderTableItem>[]
>(
    () => [
        {
            accessorKey: "id",
            header: "سفارش",
        },

        {
            accessorKey: "tableNumber",
            header: "میز",
        },

        {
            accessorKey: "itemsCount",
            header: "آیتم",
        },

        {
            accessorKey: "totalPrice",
            header: "مبلغ",

            Cell: ({ cell }) =>
                `${cell.getValue<number>().toLocaleString()} تومان`,
        },

        {
            accessorKey: "status",
            header: "وضعیت",

            Cell: ({ cell }) => (
                <OrderStatusChip
                    status={cell.getValue<string>()}
                />
            ),
        },

        {
            accessorKey: "createdAt",
            header: "زمان",
        },

        {
            id: "actions",

            header: "",

            Cell: () => (
                <IconButton>
                    <MoreVertIcon />
                </IconButton>
            ),
        },
    ],
    []
);
    return (
        <Card
            elevation={0}
            sx={{
                borderRadius: 4,
                border: "1px solid",
                borderColor: "divider",
            }}
        >
            <CardContent>
                <Typography
                    variant="h6"
                    sx={{
                        fontWeight:600,
                        mb:2
                }}
                >
                    آخرین سفارشات
                </Typography>

                <MaterialReactTable
                    columns={columns}
                    data={data}
                    enableColumnActions={false}
                    enableDensityToggle={false}
                    enableFullScreenToggle={false}
                    enableHiding={false}
                    enableRowSelection={false}
                    enableTopToolbar={false}
                    muiTablePaperProps={{
                        elevation: 0,
                    }}
                />
            </CardContent>
        </Card>
    );
};