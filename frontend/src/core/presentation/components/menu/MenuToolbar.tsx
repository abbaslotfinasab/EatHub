import {useMemo, useState} from "react";

import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import FilterListRoundedIcon from "@mui/icons-material/FilterListRounded";

import {
    Badge,
    Button,
    InputAdornment,
    Paper,
    Stack,
    TextField,
} from "@mui/material";

import {
    type MenuItemsFilter,
    type MenuOrdering,
    type MenuStatusFilter,
} from "../../../domain/objects/filters/MenuFilters";

import {MenuFilterPopover} from "./MenuFilterPopover";

export interface MenuToolbarProps {
    search: string;

    hasFilters?: boolean;

    onSearchChange(
        value: string,
    ): void;

    onFilterClick?(): void;
}

export function MenuToolbar({
                                search,
                                hasFilters = false,
                                onSearchChange,
                                onFilterClick,
                            }: MenuToolbarProps) {

    const [anchorEl, setAnchorEl] =
        useState<HTMLElement | null>(null);

    const [status, setStatus] =
        useState<MenuStatusFilter>("ALL");

    const [items, setItems] =
        useState<MenuItemsFilter>("ALL");

    const [ordering, setOrdering] =
        useState<MenuOrdering>("-created_at");

    const filtersActive = useMemo(
        () => hasFilters,
        [hasFilters],
    );

    return (
        <>
            <Paper
                elevation={0}
                sx={{
                    p: 2,
                    borderRadius: 1,
                    border: "1px solid",
                    borderColor: "divider",
                    bgcolor: "background.paper",
                }}
            >
                <Stack
                    sx={{
                        flexDirection: {
                            xs: "column",
                            md: "row",
                        },
                        gap: 2,
                        alignItems: "center",
                    }}
                >
                    <TextField
                        fullWidth
                        value={search}
                        placeholder="جستجو در منو یا آیتم..."
                        onChange={(e) =>
                            onSearchChange(
                                e.target.value,
                            )
                        }
                        sx={{
                            flex: 1,

                            "& .MuiOutlinedInput-root": {
                                height: 56,
                                borderRadius: 1,
                                bgcolor: "#fff",

                                "& fieldset": {
                                    borderColor:
                                        "#E2E8F0",
                                },

                                "&:hover fieldset": {
                                    borderColor:
                                        "#1F4A33",
                                },

                                "&.Mui-focused fieldset": {
                                    borderColor:
                                        "#10281A",
                                    borderWidth: 2,
                                },
                            },
                        }}
                        slotProps={{
                            input: {
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <SearchRoundedIcon/>
                                    </InputAdornment>
                                ),
                            },
                        }}
                    />

                    <Badge
                        variant="dot"
                        color="primary"
                        invisible={!filtersActive}
                    >
                        <Button
                            variant="outlined"
                            startIcon={
                                <FilterListRoundedIcon/>
                            }
                            onClick={(e) => {

                                setAnchorEl(
                                    e.currentTarget,
                                );

                                onFilterClick?.();

                            }}
                            sx={{
                                width: {
                                    xs: "100%",
                                    md: 150,
                                },

                                minWidth: 150,

                                height: 56,

                                borderRadius: 1,

                                flexShrink: 0,
                            }}
                        >
                            فیلترها
                        </Button>
                    </Badge>
                </Stack>
            </Paper>

            <MenuFilterPopover
                open={Boolean(anchorEl)}
                anchorEl={anchorEl}
                status={status}
                items={items}
                ordering={ordering}
                onStatusChange={setStatus}
                onItemsChange={setItems}
                onOrderingChange={setOrdering}
                onClear={() => {
                    setStatus("ALL");
                    setItems("ALL");
                    setOrdering("-created_at");
                }}
                onClose={() =>
                    setAnchorEl(null)
                }
            />
        </>
    );
}