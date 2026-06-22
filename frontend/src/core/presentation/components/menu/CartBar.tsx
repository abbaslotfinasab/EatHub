import { Box, Button, Typography } from "@mui/material";

export const CartBar = () => {
    return (
        <Box
            sx={{
                position: "sticky",
                bottom: 0,
                background: "#10281a",
                color: "#fff",
                p: 2,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
            }}
        >
            <Typography>3 items • $45</Typography>

            <Button
                variant="contained"
                sx={{
                    background: "#fff",
                    color: "#10281a",
                    fontWeight: 700,
                }}
            >
                Checkout
            </Button>
        </Box>
    );
};