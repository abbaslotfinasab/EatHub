// src/presentation/components/menu/MenuItemsSection.tsx

import {Box, Card, CardContent, Divider, Stack, Typography} from "@mui/material";
import {Button} from "@mui/material";
import {Plus} from "lucide-react";
import type {FieldArrayWithId, UseFieldArrayAppend, UseFieldArrayRemove} from "react-hook-form";


import {MenuItemCard} from "./MenuItemCard";
import {EmptyMenuItems} from "./EmptyMenuItems";
import {RestaurantMenu} from "@mui/icons-material";
import type { MenuFormInput } from "../../../../domain/objects/forms/MenuFormInput";


interface Props {
    fields: FieldArrayWithId<MenuFormInput, "items", "id">[];

    append: UseFieldArrayAppend<MenuFormInput, "items">;

    remove: UseFieldArrayRemove;
}

export const MenuItemsSection = ({
                                     fields,
                                     append,
                                     remove,
                                 }: Props) => {
    const handleAddItem = () => {
        append({
            name: "",
            description: null,
            price: 0,
            imageFile: null,
            imageUrl: null,
            isAvailable: true,
        });
    };

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

                <Button
                    variant="contained"
                    endIcon={<Plus size={18}/>}
                    onClick={handleAddItem}
                    sx={{
                        borderRadius: 3,
                        px: 2.5,
                        height: 44,

                        "& .MuiButton-endIcon": {
                            mr: 1,
                            ml: 0,
                        },
                    }}
                >
                    افزودن آیتم
                </Button>
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