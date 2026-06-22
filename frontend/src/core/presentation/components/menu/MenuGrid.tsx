import {Box, Typography} from "@mui/material";
import {MenuItemTile} from "./MenuItemTile";
import {useNavigate} from "react-router-dom";

export const MenuGrid = ({items}) => {
       const navigate = useNavigate();

    if (!items.length) {
        return (
            <Box
                sx={{
                    py: 8,
                    textAlign: "center",
                }}
            >
                <Typography
                    variant="h6"
                    fontWeight={700}
                    color="text.secondary"
                >
                    آیتمی پیدا نشد
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{mt: 1}}
                >
                    عبارت جستجو را تغییر دهید
                </Typography>
            </Box>
        );
    }

    return (
        <Box
            sx={{
                display: "grid",

                gridTemplateColumns: {
                    xs: "1fr",
                    md: "repeat(2,1fr)",
                },

                gap: 2.5,
            }}
        >
            {items.map((item) => (
                <MenuItemTile
                    key={item.id}
                    item={item}
                    onEdit={(item) => {
                        navigate(
                            `/products/${item.id}/edit`
                        );
                    }}
                    onDelete={(item) => {
                        // setDeleteItem(item);
                    }}
                />
            ))}
        </Box>
    );
};