// src/presentation/components/menu/MenuItemsSection.tsx

import {Box, Card, CardContent, Divider, Stack, Typography} from "@mui/material";
import type {FieldArrayWithId, UseFieldArrayRemove} from "react-hook-form";


import {MenuItemCard} from "./MenuItemCard";
import {EmptyMenuItems} from "./EmptyMenuItems";
import {RestaurantMenu} from "@mui/icons-material";
import type { MenuFormInput } from "../../../forms/menu/MenuFormInput.ts";


interface Props {
    fields: FieldArrayWithId<MenuFormInput, "items", "id">[];

    remove: UseFieldArrayRemove;
}

export const MenuItemsSection = ({
                                     fields,
                                     remove,
                                 }: Props) => {

    return (
        <Card elevation={0}>
            <Box
                sx={{
                    px: 3,
                    py: 2.5,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    borderBottom: "1px solid",
                    borderColor: "divider",
                }}
            >
                <Stack spacing={0.5}>
                    <Stack
                        sx={{
                            flexDirection: "row",
                            alignItems: "center",
                            gap: 1,
                        }}
                    >
                        <RestaurantMenu
                            sx={{
                                color: "primary.main",
                                fontSize: 24,
                            }}
                        />

                        <Typography
                            sx={{
                                typography: "h6",
                                fontWeight: 700,
                            }}
                        >
                            آیتم‌های منو
                        </Typography>
                    </Stack>

                    <Typography
                        sx={{
                            typography: "body2",
                            color: "text.secondary",
                        }}
                    >
                        غذاها، نوشیدنی‌ها و سایر آیتم‌های این منو را مدیریت کنید.
                    </Typography>
                </Stack>
            </Box>

            <Divider/>

            <CardContent>
                {fields.length === 0 ? (
                    <EmptyMenuItems/>
                ) : (
                    <Stack spacing={2}>
                        {fields.map((field, index) => (
                            <MenuItemCard
                                key={field.id}
                                index={index}
                                onDelete={() => remove(index)}
                            />
                        ))}
                    </Stack>
                )}
            </CardContent>
        </Card>
    );
};