import {
    Avatar,
    Badge,
    Box,
    IconButton,
    InputAdornment,
    Paper,
    Stack,
    TextField,
    Typography,
} from "@mui/material";

import NotificationsIcon from "@mui/icons-material/Notifications";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";

export const DashboardHeader = () => {
    const today = new Date().toLocaleDateString("fa-IR", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
    });

    return (
        <Paper
            elevation={0}
            sx={{
                p: 3,
                borderRadius: 4,
                border: "1px solid",
                borderColor: "divider",
                bgcolor: "background.paper",
            }}
        >
            <Stack
                direction={{xs: "column", lg: "row"}}
                spacing={2}
                sx={{
                    justifyContent: "space-between",
                    alignItems: {
                        xs: "stretch",
                        lg: "center",
                    },
                }}
            >
                {/* Welcome */}
                <Box>
                    <Typography
                        variant="h5"
                        sx={{fontWeight: 700}}
                        gutterBottom
                    >
                        سلام عباس 👋
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        {today}
                    </Typography>
                </Box>

                {/* Search */}
                <Box
                    sx={{
                        width: {
                            xs: "100%",
                            lg: 400,
                        },
                    }}
                >
                    <TextField
                        fullWidth
                        size="small"
                        placeholder="جستجو در سفارشات، فاکتورها، مواد اولیه..."
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
                </Box>

                {/* Actions */}
                <Stack
                    direction="row"
                    spacing={2}
                    sx={{
                        alignItems: "center",
                    }}
                >
                    <IconButton>
                        <Badge
                            badgeContent={5}
                            color="error"
                        >
                            <NotificationsIcon/>
                        </Badge>
                    </IconButton>

                    <Stack
                        direction="row"
                        spacing={1.5}
                        sx={{
                            alignItems: "center",
                        }}
                    >
                        <Avatar
                            sx={{
                                bgcolor: "#10281A",
                            }}
                        >
                            A
                        </Avatar>

                        <Box>
                            <Typography
                                sx={{fontWeight:600}}
                            >
                                عباس لطفی نسب
                            </Typography>

                            <Typography
                                variant="caption"
                                color="text.secondary"
                            >
                                مدیر سیستم
                            </Typography>
                        </Box>
                    </Stack>
                </Stack>
            </Stack>
        </Paper>
    );
};