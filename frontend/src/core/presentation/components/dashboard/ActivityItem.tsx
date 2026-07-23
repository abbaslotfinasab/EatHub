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

    userName?: string;

    title: string;

    description?: string;

    createdAt: string;

    action: string;

}


const activityIcons = {

    order_created: <ShoppingBagRoundedIcon/>,

    order_completed: <ShoppingBagRoundedIcon/>,

    order_cancelled: <ShoppingBagRoundedIcon/>,

    stock_low: <Inventory2RoundedIcon/>,

    invoice_created: <ReceiptLongRoundedIcon/>,

    reservation_created: <EventSeatRoundedIcon/>,

    menu_updated: <RestaurantMenuRoundedIcon/>,

};


export const ActivityItem = ({
                                 userName,
                                 title,
                                 description,
                                 createdAt,
                                 action,
                             }: Props) => {


    const icon =
        activityIcons[
            action as keyof typeof activityIcons
            ] ?? <ReceiptLongRoundedIcon/>;


    return (

        <Stack
            direction="row"
            spacing={2}
            sx={{
                alignItems: "flex-start",
            }}
        >

            <Avatar
                sx={{
                    bgcolor: "#10281A",
                    width: 42,
                    height: 42,
                }}
            >
                {icon}
            </Avatar>


            <Box
                sx={{
                    flex: 1,
                }}
            >

                <Typography
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    {userName ?? "سیستم"}
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    {title}
                </Typography>


                {
                    description && (
                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {description}
                        </Typography>
                    )
                }


                <Typography
                    variant="caption"
                    color="text.disabled"
                >
                    {createdAt}
                </Typography>

            </Box>

        </Stack>
    );
};