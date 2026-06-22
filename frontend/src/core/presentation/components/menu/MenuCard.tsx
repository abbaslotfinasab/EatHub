import { Box, Button, Typography } from "@mui/material";


type MenuItemCard = {
    id: string;
    name: string;
    price: number;
    menuId: string;
};

type MenuCardProps = {
    item: MenuItemCard;
};


export const MenuCard = ({ item }: MenuCardProps) => {
    return (
        <Box
            sx={{
                background: "#fff",
                borderRadius: 3,
                p: 2,
                boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
                display: "flex",
                flexDirection: "column",
                gap: 1,
            }}
        >
            <Box
                sx={{
                    height: 100,
                    background: "#eee",
                    borderRadius: 2,
                }}
            />

            <Typography>
                {item.name}
            </Typography>

            <Typography color="text.secondary">
                ${item.price}
            </Typography>

            <Button
                variant="contained"
                size="small"
                sx={{ mt: "auto" }}
            >
                Add
            </Button>
        </Box>
    );
};