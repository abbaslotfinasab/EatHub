import {
    Avatar,
    Box,
    Chip,
    Paper,
    Typography,
} from "@mui/material";

import AccessTimeIcon from "@mui/icons-material/AccessTime";
import LocationOnIcon from "@mui/icons-material/LocationOn";

type RestaurantHeaderProps = {
    restaurant: {
        name: string;
        description?: string;
        logoUrl?: string;
        coverUrl?: string;
        address?: string;
        openingHours?: string;
    };
};

export const RestaurantHeader = ({
    restaurant,
}: RestaurantHeaderProps) => {
    return (
        <Paper
            elevation={0}
            sx={{
                overflow: "hidden",
                borderRadius: 4,
                mb: 3,
                border: "1px solid",
                borderColor: "divider",
            }}
        >
            {/* Cover */}
            <Box
                sx={{
                    position: "relative",
                    height: {
                        xs: 180,
                        sm: 240,
                    },
                }}
            >
                <Box
                    component="img"
                    src={
                        restaurant.coverUrl ||
                        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4"
                    }
                    alt={restaurant.name}
                    sx={{
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                    }}
                />

                <Box
                    sx={{
                        position: "absolute",
                        inset: 0,
                        background:
                            "linear-gradient(to top, rgba(0,0,0,.65), rgba(0,0,0,.15))",
                    }}
                />

                {/* Logo */}
                <Avatar
                    src={restaurant.logoUrl}
                    alt={restaurant.name}
                    sx={{
                        width: 90,
                        height: 90,

                        position: "absolute",

                        left: 24,
                        bottom: -45,

                        border: "4px solid white",
                        bgcolor: "#fff",
                    }}
                />
            </Box>

            {/* Content */}
            <Box
                sx={{
                    pt: 7,
                    px: 3,
                    pb: 3,
                }}
            >
                <Typography
                    variant="h4"
                    sx={{
                        fontWeight: 800,
                        mb: 1,
                    }}
                >
                    {restaurant.name}
                </Typography>

                {restaurant.description && (
                    <Typography
                        color="text.secondary"
                        sx={{
                            mb: 2,
                            maxWidth: 700,
                        }}
                    >
                        {restaurant.description}
                    </Typography>
                )}

                <Box
                    sx={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: 1,
                    }}
                >
                    {restaurant.openingHours && (
                        <Chip
                            icon={
                                <AccessTimeIcon />
                            }
                            label={
                                restaurant.openingHours
                            }
                            variant="outlined"
                        />
                    )}

                    {restaurant.address && (
                        <Chip
                            icon={
                                <LocationOnIcon />
                            }
                            label={
                                restaurant.address
                            }
                            variant="outlined"
                        />
                    )}
                </Box>
            </Box>
        </Paper>
    );
};