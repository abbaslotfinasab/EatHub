import { Box, CircularProgress, Typography } from "@mui/material";

export const FullPageLoader = ({
    text = "Loading...",
}: {
    text?: string;
}) => {
    return (
        <Box
            sx={{
                position: "fixed",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexDirection: "column",
                backgroundColor: "rgba(255,255,255,0.75)",
                backdropFilter: "blur(6px)",
                zIndex: 9999,
            }}
        >
            <CircularProgress size={48} thickness={4} />

            <Typography
                sx={{
                    mt: 2,
                    fontSize: 14,
                    color: "text.secondary",
                    fontWeight: 500,
                    letterSpacing: 0.5,
                }}
            >
                {text}
            </Typography>
        </Box>
    );
};