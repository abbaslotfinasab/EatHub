// src/presentation/components/menu/EmptyMenuItems.tsx

import {Paper, Stack, Typography} from "@mui/material";
import {PackageOpen} from "lucide-react";

export const EmptyMenuItems = () => {
    return (
        <Paper
            variant="outlined"
            sx={{
                py: 8,
                px: 4,
                borderStyle: "dashed",
                borderRadius: 3,
                bgcolor: "grey.50",
            }}
        >
            <Stack
                sx={{
                    gap: 2,
                    alignItems: "center",
                    justifyContent: "center",
                }}
            >
                <PackageOpen
                    size={48}
                    strokeWidth={1.5}
                    color="#9ca3af"
                />

                <Typography
                    sx={{
                        typography: "h6",
                        fontWeight: 600,
                        color: "text.primary",
                    }}
                >
                    هنوز آیتمی اضافه نشده است
                </Typography>

                <Typography
                    sx={{
                        typography: "body2",
                        color: "text.secondary",
                        textAlign: "center",
                        maxWidth: 420,
                    }}
                >
                    برای ساخت منو، روی دکمه
                    {" "}
                    <strong>«افزودن آیتم»</strong>
                    {" "}
                    کلیک کنید و اولین غذای خود را اضافه کنید.
                </Typography>
            </Stack>
        </Paper>
    );
};