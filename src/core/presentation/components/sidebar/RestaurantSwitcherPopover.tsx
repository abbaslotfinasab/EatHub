// src/core/presentation/components/sidebar/RestaurantSwitcherPopover.tsx

import {
    Paper,
    MenuList,
    MenuItem,
    ListItemIcon,
    ListItemText,
    Divider,
} from "@mui/material";

import AddRoundedIcon from "@mui/icons-material/AddRounded";

interface Restaurant {
    id: string;
    name: string;
    emoji: string;
}

interface Props {
    restaurants: Restaurant[];
    selectedRestaurantId: string;
    onSelect: (id: string) => void;
}

export const RestaurantSwitcherPopover = ({
                                              restaurants,
                                              selectedRestaurantId,
                                              onSelect,
                                          }: Props) => {
    return (
        <Paper
            elevation={12}
            sx={{
                width: 280,
                borderRadius: 3,
                overflow: "hidden",
            }}
        >
            <MenuList dense>
                {restaurants.map((restaurant) => (
                    <MenuItem
                        key={restaurant.id}
                        selected={
                            restaurant.id ===
                            selectedRestaurantId
                        }
                        onClick={() =>
                            onSelect(restaurant.id)
                        }
                    >
                        <ListItemIcon
                            sx={{
                                minWidth: 36,
                                fontSize: 22,
                            }}
                        >
                            {restaurant.emoji}
                        </ListItemIcon>

                        <ListItemText
                            primary={restaurant.name}
                        />
                    </MenuItem>
                ))}
            </MenuList>

            <Divider />

            <MenuItem>
                <ListItemIcon>
                    <AddRoundedIcon />
                </ListItemIcon>

                <ListItemText
                    primary="افزودن رستوران"
                />
            </MenuItem>
        </Paper>
    );
};