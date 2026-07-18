// presentation/components/order/OrderMenuPicker/MenuItemQuantity.tsx

import AddRoundedIcon from "@mui/icons-material/AddRounded";
import RemoveRoundedIcon from "@mui/icons-material/RemoveRounded";

import {
    Button,
    IconButton,
    Stack,
    Typography,
} from "@mui/material";

interface MenuItemQuantityProps {
    quantity: number;

    onAdd: () => void;

    onIncrease: () => void;

    onDecrease: () => void;
}

export const MenuItemQuantity = ({
    quantity,
    onAdd,
    onIncrease,
    onDecrease,
}: MenuItemQuantityProps) => {

    if (quantity === 0) {
        return (
            <Button
                variant="contained"
                startIcon={<AddRoundedIcon />}
                onClick={onAdd}
                sx={{
                    minWidth: 120,
                    borderRadius: 3,
                    fontWeight: 700,
                }}
            >
                افزودن
            </Button>
        );
    }

    return (
        <Stack
            direction="row"
            spacing={1}
            alignItems="center"
            sx={{
                bgcolor: "grey.100",
                borderRadius: 3,
                px: 1,
                py: 0.5,
            }}
        >

            <IconButton
                color="primary"
                size="small"
                onClick={onDecrease}
            >
                <RemoveRoundedIcon />
            </IconButton>

            <Typography
                sx={{
                    minWidth: 28,
                    textAlign: "center",
                    fontWeight: 700,
                    fontSize: 16,
                }}
            >
                {quantity}
            </Typography>

            <IconButton
                color="primary"
                size="small"
                onClick={onIncrease}
            >
                <AddRoundedIcon />
            </IconButton>

        </Stack>
    );
};