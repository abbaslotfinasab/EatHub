import { Box, Chip } from "@mui/material";

export interface Menu {
    id: string;
    name: string;
}

type MenuTabsProps = {
    active: Menu["id"];
    menus: Menu[];
    onChange: (menuId: Menu["id"]) => void;
};

export const MenuTabs = ({
    active,
    menus,
    onChange,
}: MenuTabsProps) => {
    return (
        <Box sx={{ display: "flex", gap: 1, overflowX: "auto" }}>
            {menus.map((menu) => (
                <Chip
                    key={menu.id}
                    label={menu.name}
                    onClick={() => onChange(menu.id)}
                    color={
                        active === menu.id ? "primary" : "default"
                    }
                />
            ))}
        </Box>
    );
};