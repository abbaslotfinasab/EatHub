// src/core/presentation/components/navbar/notifications/NotificationButton.tsx

import { useState } from "react";

import {
    Badge,
    Box,
    Divider,
    IconButton,
    List,
    ListItem,
    ListItemText,
    Popover,
    Typography,
} from "@mui/material";

import NotificationsRoundedIcon from "@mui/icons-material/NotificationsRounded";

interface Notification {
    id: string;
    title: string;
    description: string;
    time: string;
}

export const NotificationButton = () => {
    const [anchorEl, setAnchorEl] =
        useState<HTMLElement | null>(null);

    const notifications: Notification[] = [
        {
            id: "1",
            title: "کمبود موجودی",
            description:
                "پنیر پیتزا کمتر از حد مجاز شده است",
            time: "5 دقیقه پیش",
        },
        {
            id: "2",
            title: "سفارش جدید",
            description:
                "سفارش شماره #125 ثبت شد",
            time: "12 دقیقه پیش",
        },
        {
            id: "3",
            title: "رزرو جدید",
            description:
                "یک رزرو برای ساعت 20 ثبت شد",
            time: "30 دقیقه پیش",
        },
    ];

    const handleOpen = (
        event: React.MouseEvent<HTMLElement>
    ) => {
        setAnchorEl(event.currentTarget);
    };

    const handleClose = () => {
        setAnchorEl(null);
    };

    const open = Boolean(anchorEl);

    return (
        <>
            <IconButton
                onClick={handleOpen}
                sx={{
                    color: "#374151",
                }}
            >
                <Badge
                    badgeContent={
                        notifications.length
                    }
                    color="error"
                >
                    <NotificationsRoundedIcon />
                </Badge>
            </IconButton>

            <Popover
                open={open}
                anchorEl={anchorEl}
                onClose={handleClose}
                anchorOrigin={{
                    vertical: "bottom",
                    horizontal: "right",
                }}
                transformOrigin={{
                    vertical: "top",
                    horizontal: "right",
                }}
                PaperProps={{
                    sx: {
                        width: 360,
                        mt: 1,
                        borderRadius: 3,
                    },
                }}
            >
                <Box p={2}>
                    <Typography
                        variant="h6"
                        sx={{
                            fontWeight: 700,
                            mb: 1,
                        }}
                    >
                        اعلان‌ها
                    </Typography>

                    <Divider />

                    <List
                        sx={{
                            py: 0,
                        }}
                    >
                        {notifications.map(
                            (notification) => (
                                <ListItem
                                    key={
                                        notification.id
                                    }
                                    sx={{
                                        px: 0,
                                        py: 1.5,
                                    }}
                                >
                                    <ListItemText
                                        primary={
                                            notification.title
                                        }
                                        secondary={
                                            <>
                                                <Typography
                                                    component="span"
                                                    variant="body2"
                                                    display="block"
                                                >
                                                    {
                                                        notification.description
                                                    }
                                                </Typography>

                                                <Typography
                                                    component="span"
                                                    variant="caption"
                                                    color="text.secondary"
                                                >
                                                    {
                                                        notification.time
                                                    }
                                                </Typography>
                                            </>
                                        }
                                    />
                                </ListItem>
                            )
                        )}
                    </List>
                </Box>
            </Popover>
        </>
    );
};