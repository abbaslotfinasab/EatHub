import {
    Avatar,
    Box,
    Stack,
    Typography,
} from "@mui/material";

import ShoppingBagRoundedIcon from "@mui/icons-material/ShoppingBagRounded";
import Inventory2RoundedIcon from "@mui/icons-material/Inventory2Rounded";
import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLongRounded";
import EventSeatRoundedIcon from "@mui/icons-material/EventSeatRounded";
import RestaurantMenuRoundedIcon from "@mui/icons-material/RestaurantMenuRounded";

interface Props {
    userName: string;
    action: string;
    timestamp: string;
    type:
        | "order"
        | "inventory"
        | "accounting"
        | "reservation"
        | "menu";
}

const activityIcons = {
    order: <ShoppingBagRoundedIcon />,
    inventory: <Inventory2RoundedIcon />,
    accounting: <ReceiptLongRoundedIcon />,
    reservation: <EventSeatRoundedIcon />,
    menu: <RestaurantMenuRoundedIcon />,
};

export const ActivityItem = ({
                                 userName,
                                 action,
                                 timestamp,
                                 type,
                             }: Props) => {
    return (
        <Stack
            direction="row"
    spacing={2}
    alignItems="flex-start"
    >
    <Avatar
        sx={{
        bgcolor: "#10281A",
            width: 42,
            height: 42,
    }}
>
    {activityIcons[type]}
    </Avatar>

    <Box flex={1}>
    <Typography
        fontWeight={600}
    variant="body2"
        >
        {userName}
        </Typography>

        <Typography
    variant="body2"
    color="text.secondary"
        >
        {action}
        </Typography>

        <Typography
    variant="caption"
    color="text.disabled"
        >
        {timestamp}
        </Typography>
        </Box>
        </Stack>
);
};