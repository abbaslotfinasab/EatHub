// src/core/presentation/components/navbar/search/NavbarSearch.tsx

import { useState } from "react";

import {
    Box,
    InputAdornment,
    TextField,
    IconButton,
} from "@mui/material";

import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import ClearRoundedIcon from "@mui/icons-material/ClearRounded";

export const NavbarSearch = () => {
    const [search, setSearch] = useState("");

    const handleClear = () => {
        setSearch("");
    };

    return (
        <Box
            sx={{
                flex: 1,
                maxWidth: 500,
                mx: 2,

                display: {
                    xs: "none",
                    md: "block",
                },
            }}
        >
            <TextField
                fullWidth
                size="small"
                value={search}
                onChange={(e) =>
                    setSearch(e.target.value)
                }
                placeholder="جستجو در مواد اولیه، رسپی، سفارش‌ها..."
                variant="outlined"
                slotProps={{
                    input: {
                        startAdornment: (
                            <InputAdornment position="start">
                                <SearchRoundedIcon
                                    fontSize="small"
                                />
                            </InputAdornment>
                        ),

                        endAdornment: search ? (
                            <InputAdornment position="end">
                                <IconButton
                                    size="small"
                                    onClick={handleClear}
                                >
                                    <ClearRoundedIcon
                                        fontSize="small"
                                    />
                                </IconButton>
                            </InputAdornment>
                        ) : undefined,
                    },
                }}
                sx={{
                    "& .MuiOutlinedInput-root": {
                        borderRadius: 3,
                        bgcolor: "#FFFFFF",

                        "& fieldset": {
                            borderColor: "#E5E7EB",
                        },

                        "&:hover fieldset": {
                            borderColor: "#CBD5E1",
                        },

                        "&.Mui-focused fieldset": {
                            borderColor: "#10281A",
                        },
                    },
                }}
            />
        </Box>
    );
};