// presentation/components/order/OrderMenuPicker/OrderMenuPicker.tsx

import {useMemo, useState} from "react";

import {
    Box,
    CircularProgress,
    Paper,
    Stack,
    Typography,
} from "@mui/material";

import {useGetMenus} from "../../../hooks/menu/useGetMenus";

import {MenuSearch} from "./MenuSearch";
import {MenuCategoryTabs} from "./MenuCategoryTabs";
import {MenuItemsList} from "./MenuItemsList";

export const OrderMenuPicker = () => {

    const {
        data: menus = [],
        isLoading,
    } = useGetMenus();

    const [search, setSearch] =
        useState("");

    const [selectedMenuId, setSelectedMenuId] =
        useState<string>();

    // ===========================
    // Filter Menus
    // ===========================

    const filteredMenus = useMemo(() => {

        const keyword =
            search
                .trim()
                .toLowerCase();

        if (!keyword) {
            return menus;
        }

        return menus
            .map(menu => ({
                ...menu,

                items: menu.items.filter(item => {

                    return (
                        item.name
                            .toLowerCase()
                            .includes(keyword) ||

                        item.description
                            ?.toLowerCase()
                            .includes(keyword)
                    );

                }),
            }))
            .filter(menu =>
                menu.items.length > 0,
            );

    }, [
        menus,
        search,
    ]);

    // ===========================
    // Selected Menu
    // ===========================

    const selectedMenu = useMemo(() => {

        if (
            filteredMenus.length === 0
        ) {
            return undefined;
        }

        return (
            filteredMenus.find(
                menu =>
                    menu.menu.id ===
                    selectedMenuId,
            ) ??
            filteredMenus[0]
        );

    }, [
        filteredMenus,
        selectedMenuId,
    ]);

    // ===========================
    // Loading
    // ===========================

    if (isLoading) {

        return (

            <Paper
                elevation={0}
                sx={{
                    p: 5,
                    borderRadius: 3,
                    border: "1px solid",
                    borderColor: "divider",
                }}
            >

                <Box
                    sx={{
                        display: "flex",
                        justifyContent: "center",
                    }}
                >

                    <CircularProgress/>

                </Box>

            </Paper>

        );

    }

    // ===========================
    // Empty
    // ===========================

    if (
        filteredMenus.length === 0
    ) {

        return (

            <Paper
                elevation={0}
                sx={{
                    p: 4,
                    borderRadius: 3,
                    border: "1px solid",
                    borderColor: "divider",
                }}
            >

                <Stack
                    sx={{
                        gap: 1,
                        alignItems: "center",
                    }}
                >

                    <Typography
                        variant="h6"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        غذایی پیدا نشد
                    </Typography>

                    <Typography
                        color="text.secondary"
                    >
                        عبارت جستجو را تغییر دهید.
                    </Typography>

                </Stack>

            </Paper>

        );

    }

    // ===========================
    // Render
    // ===========================

    return (

        <Paper
            elevation={0}
            sx={{
                p: 3,
                borderRadius: 3,
                border: "1px solid",
                borderColor: "divider",
            }}
        >

            <Stack spacing={3}>

                <Typography
                    variant="h6"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    انتخاب غذا
                </Typography>

                <MenuSearch
                    value={search}
                    onChange={setSearch}
                />

                <MenuCategoryTabs
                    menus={filteredMenus}
                    selectedMenuId={
                        selectedMenu?.menu.id
                    }
                    onChange={
                        setSelectedMenuId
                    }
                />

                {selectedMenu && (

                    <MenuItemsList
                        menu={selectedMenu}
                    />

                )}

            </Stack>

        </Paper>

    );

};