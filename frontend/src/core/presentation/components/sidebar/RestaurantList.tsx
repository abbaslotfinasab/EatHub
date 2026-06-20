// src/core/presentation/components/sidebar/RestaurantList.tsx

import {
    Avatar,
    Box,
    List,
    ListItemButton,
    ListItemText,
    Typography,
} from "@mui/material";

import AddRoundedIcon from "@mui/icons-material/AddRounded";

interface Restaurant {
    id: string;
    name: string;
    logo?: string;
}

interface RestaurantListProps {
    restaurants?: Restaurant[];
    selectedRestaurantId: string;
    onSelect: (restaurantId: string) => void;
    onAddRestaurant: () => void;
}

export const RestaurantList = ({
                                   restaurants,
                                   selectedRestaurantId,
                                   onSelect,
                                   onAddRestaurant,
                               }: RestaurantListProps) => {
    return (
        <Box>
            <List disablePadding>
                {restaurants!.map((restaurant) => {
                    const isSelected =
                        restaurant.id === selectedRestaurantId;

                    return (
                        <ListItemButton
                            key={restaurant.id}
                            onClick={() =>
                                onSelect(restaurant.id)
                            }
                            sx={{
                                mx: 1,
                                my: 0.5,
                                borderRadius: 2,

                                backgroundColor: isSelected
                                    ? "rgba(255,255,255,0.14)"
                                    : "transparent",

                                "&:hover": {
                                    backgroundColor:
                                        "rgba(255,255,255,0.08)",
                                },
                            }}
                        >
                            <Avatar
                                src={restaurant.logo}
                                sx={{
                                    width: 32,
                                    height: 32,
                                    ml: 1.5,
                                    fontSize: 14,
                                }}
                            >
                                🍕
                            </Avatar>

                            <ListItemText
                                primary={restaurant.name}
                                primaryTypographyProps={{
                                    sx: {
                                        color: "#FFFFFF",
                                        fontSize: 14,
                                        fontWeight: isSelected
                                            ? 700
                                            : 500,
                                    },
                                }}
                            />
                        </ListItemButton>
                    );
                })}

                <ListItemButton
                    onClick={onAddRestaurant}
                    sx={{
                        mx: 1,
                        my: 1,
                        borderRadius: 2,

                        "&:hover": {
                            backgroundColor:
                                "rgba(255,255,255,0.08)",
                        },
                    }}
                >
                    <AddRoundedIcon
                        sx={{
                            color: "#FFFFFF",
                            ml: 1.5,
                        }}
                    />

                    <Typography
                        sx={{
                            color: "#FFFFFF",
                            fontSize: 14,
                            fontWeight: 500,
                        }}
                    >
                        افزودن رستوران
                    </Typography>
                </ListItemButton>
            </List>
        </Box>
    );
};