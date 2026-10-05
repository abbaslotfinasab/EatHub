// presentation/components/order/OrderMenuPicker/OrderMenuPicker.tsx

import {useEffect, useMemo, useState} from "react";

import {
    Box,
    Button,
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
        useState<number>();

    // ===========================
    // Filter Menus
    // ===========================

    const filteredMenus = useMemo(() => {

        const keyword =
            search.trim().toLowerCase();

        // No search keyword:
        // return all menus as-is.
        if (!keyword) {
            return menus;
        }

        return menus
            .map(menu => ({
                ...menu,

                items: menu.items.filter(item => {

                    const name =
                        item.name?.toLowerCase() ?? "";

                    const description =
                        item.description?.toLowerCase() ?? "";

                    return (
                        name.includes(keyword) ||
                        description.includes(keyword)
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

        if (filteredMenus.length === 0) {
            return undefined;
        }

        return (
            filteredMenus.find(
                menu =>
                    menu.menu.id === selectedMenuId,
            ) ??
            filteredMenus[0]
        );

    }, [
        filteredMenus,
        selectedMenuId,
    ]);

    // ===========================
    // Keep Selected Menu Valid
    // ===========================

    useEffect(() => {

        if (filteredMenus.length === 0) {
            return;
        }

        const selectedMenuExists =
            filteredMenus.some(
                menu =>
                    menu.menu.id === selectedMenuId,
            );

        if (!selectedMenuExists) {
            setSelectedMenuId(
                filteredMenus[0].menu.id,
            );
        }

    }, [
        filteredMenus,
        selectedMenuId,
    ]);

    // ===========================
    // Clear Search
    // ===========================

    const handleClearSearch = () => {
        setSearch("");
    };

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
                    <CircularProgress />
                </Box>
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

                {/* Header */}

                <Typography
                    variant="h6"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    انتخاب غذا
                </Typography>

                {/* Search */}

                <MenuSearch
                    value={search}
                    onChange={setSearch}
                />

                {/* Empty Search Result */}

                {filteredMenus.length === 0 ? (

                    <Stack
                        sx={{
                            py: 5,
                            gap: 1.5,
                            alignItems: "center",
                            textAlign: "center",
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
                            برای عبارت «{search}» غذایی پیدا نشد.
                        </Typography>

                        <Button
                            variant="outlined"
                            onClick={handleClearSearch}
                            sx={{
                                mt: 1,
                            }}
                        >
                            پاک کردن جستجو
                        </Button>
                    </Stack>

                ) : (

                    <>
                        {/* Menu Categories */}

                        <MenuCategoryTabs
                            menus={filteredMenus}
                            selectedMenuId={
                                selectedMenu?.menu.id
                            }
                            onChange={
                                setSelectedMenuId
                            }
                        />

                        {/* Menu Items */}

                        {selectedMenu && (
                            <MenuItemsList
                                menu={selectedMenu}
                            />
                        )}
                    </>

                )}

            </Stack>
        </Paper>
    );
};