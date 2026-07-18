// presentation/components/order-form/SelectedOrderItemCard.tsx

import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import RemoveRoundedIcon from "@mui/icons-material/RemoveRounded";

import {
    Avatar,
    Chip,
    Divider,
    IconButton,
    Paper,
    Stack,
    Typography,
} from "@mui/material";
import type { MenuItem } from "../../../domain/entities/product/menu/MenuItem.ts";
import type { OrderFormItemInput } from "../../forms/order/OrderFormItemInput.ts";
import {formatCurrency} from "../../utils/formatCurrency.ts";



interface SelectedOrderItemCardProps {
    menuItem: MenuItem;

    item: OrderFormItemInput;

    onIncrease: () => void;

    onDecrease: () => void;

    onRemove: () => void;
}

export const SelectedOrderItemCard = ({
    menuItem,
    item,
    onIncrease,
    onDecrease,
    onRemove,
}: SelectedOrderItemCardProps) => {

    const total =
        menuItem.price * item.quantity;

    return (
        <Paper
            variant="outlined"
            sx={{
                p: 2,
                borderRadius: 3,
            }}
        >
            <Stack spacing={2}>

                {/* Header */}

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        gap: 2,
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
                            variant="rounded"
                            src={menuItem.imageUrl ?? ""}
                            sx={{
                                width: 64,
                                height: 64,
                                borderRadius: 2,
                            }}
                        >
                            {menuItem.name[0]}
                        </Avatar>

                        <Stack spacing={0.5}>

                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                {menuItem.name}
                            </Typography>

                            {menuItem.description && (
                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    {menuItem.description}
                                </Typography>
                            )}

                            <Typography
                                variant="body2"
                                color="primary"
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                {formatCurrency(menuItem.price)}
                            </Typography>

                        </Stack>

                    </Stack>

                    <IconButton
                        color="error"
                        onClick={onRemove}
                    >
                        <DeleteOutlineRoundedIcon />
                    </IconButton>

                </Stack>

                <Divider />

                {/* Footer */}

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
                            alignItems: "center",
                            gap: 1,
                        }}
                    >

                        <IconButton
                            color="primary"
                            onClick={onDecrease}
                        >
                            <RemoveRoundedIcon />
                        </IconButton>

                        <Chip
                            label={item.quantity}
                            color="primary"
                            variant="outlined"
                            sx={{
                                minWidth: 52,
                                fontWeight: 700,
                            }}
                        />

                        <IconButton
                            color="primary"
                            onClick={onIncrease}
                        >
                            <AddRoundedIcon />
                        </IconButton>

                    </Stack>

                    <Typography
                        sx={{
                            fontWeight: 800,
                            fontSize: 16,
                        }}
                    >
                        {formatCurrency(total)}
                    </Typography>

                </Stack>

            </Stack>
        </Paper>
    );
};