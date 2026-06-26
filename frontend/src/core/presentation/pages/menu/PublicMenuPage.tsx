import {useState} from "react";
import {useParams} from "react-router-dom";

import {
    Alert,
    Box,
    CircularProgress,
    Container,
    Typography, Paper, InputAdornment, TextField,
} from "@mui/material";

import {MenuSection} from "../../components/menu/public/MenuSection.tsx";
import {useGetPublicMenus} from "../../hooks/useGetPublicMenu.tsx";
import {StatCard} from "../../components/menu/StatCard.tsx";
import SearchIcon from "@mui/icons-material/Search";

export const PublicMenuPage = () => {
    const {restaurantSlug} = useParams();

    const [search, setSearch] = useState("");
    useState("all");

    const {
        data,
        isLoading,
        isError,
    } = useGetPublicMenus(
        restaurantSlug!
    );

    const restaurant = data?.restaurant;

    const menus = data?.menus ?? [];


    /*
     * Loading
     */
    if (isLoading) {
        return (
            <Box
                sx={{
                    minHeight: "100vh",
                    display: "flex",
                    justifyContent:
                        "center",
                    alignItems: "center",
                }}
            >
                <CircularProgress/>
            </Box>
        );
    }

    /*
     * Error
     */
    if (isError || !restaurant) {
        return (
            <Container maxWidth="sm">
                <Alert
                    severity="error"
                    sx={{mt: 5}}
                >
                    خطا در دریافت منو
                </Alert>
            </Container>
        );
    }

    return (
        <Box
            sx={{
                minHeight: "100vh",
                bgcolor: "#F8FAFC",

                p: {
                    xs: 2,
                    md: 3,
                },
            }}
        >
            <Paper
                elevation={0}
                sx={{
                    position: "relative",

                    overflow: "hidden",

                    borderRadius: 6,

                    p: {
                        xs: 3,
                        md: 4,
                    },

                    mb: 4,

                    background:
                        "linear-gradient(135deg,#10281A 0%, #1F4A33 100%)",

                    color: "#fff",
                }}
            >
                <Box
                    sx={{
                        position: "absolute",

                        top: -120,
                        right: -120,

                        width: 300,
                        height: 300,

                        borderRadius:
                            "50%",

                        background:
                            "rgba(255,255,255,.08)",

                        filter:
                            "blur(50px)",
                    }}
                />

                <Box
                    sx={{
                        position: "relative",

                        zIndex: 1,

                        display: "flex",

                        flexDirection: {
                            xs: "column",
                            md: "row",
                        },

                        alignItems:
                            "center",

                        gap: 4,
                    }}
                >
                    <Box
                        sx={{
                            flex: 1,
                            width: "100%",
                        }}
                    >
                        <Typography
                            sx={{
                                fontSize: {
                                    xs: 28,
                                    md: 36,
                                },

                                fontWeight: 900,

                                textAlign: {
                                    xs: "center",
                                    md: "right",
                                },

                                mb: 1,
                            }}
                        >
                            🍽️ {restaurant.name}
                        </Typography>

                        <Typography
                            sx={{
                                color:
                                    "rgba(255,255,255,.8)",

                                textAlign: {
                                    xs: "center",
                                    md: "right",
                                },

                                mb: 4,
                            }}
                        >
                            مدیریت منوها و
                            آیتم‌های رستوران
                        </Typography>

                        <Box
                            sx={{
                                display:
                                    "grid",

                                gridTemplateColumns:
                                    {
                                        xs: "repeat(2,1fr)",
                                        md: "repeat(3,1fr)",
                                    },

                                gap: 2,
                            }}
                        >
                            <StatCard
                                title="شماره تلفن"
                                value={
                                    restaurant.phone
                                }
                            />

                            <StatCard
                                title="ادرس"
                                value={
                                    restaurant.address
                                }
                            />

                            <StatCard
                                title="وضعیت"
                                value="فعال"
                            />
                        </Box>
                    </Box>


                    <Paper
                        elevation={0}
                        sx={{
                            width: {
                                xs: 160,
                                md: 200,
                            },

                            height: {
                                xs: 160,
                                md: 200,
                            },

                            p: 2,

                            bgcolor:
                                "#fff",

                            borderRadius: 5,

                            cursor:
                                "pointer",

                            transition:
                                ".25s",

                            display:
                                "flex",

                            alignItems:
                                "center",

                            justifyContent:
                                "center",

                            "&:hover":
                                {
                                    transform:
                                        "translateY(-4px)",

                                    boxShadow:
                                        "0 20px 40px rgba(0,0,0,.2)",
                                },
                        }}
                    >
                        <img
                            src={restaurant.logoUrl??""}
                            alt={restaurant.name}
                            style={{
                                width: "100%",
                                height: "100%",
                                objectFit: "cover",
                            }}
                        />
                    </Paper>
                </Box>
            </Paper>

            <TextField
                fullWidth
                placeholder="جستجو در آیتم‌های منو..."
                value={search}
                onChange={(e) =>
                    setSearch(e.target.value)
                }
                sx={{
                    mb: 4,

                    "& .MuiOutlinedInput-root": {
                        height: 58,
                        borderRadius: 4,
                        bgcolor: "#fff",

                        "& fieldset": {
                            borderColor: "#E2E8F0",
                        },

                        "&:hover fieldset": {
                            borderColor: "#1F4A33",
                        },

                        "&.Mui-focused fieldset": {
                            borderColor: "#10281A",
                            borderWidth: "2px",
                        },
                    },
                }}
                slotProps={{
                    input: {
                        startAdornment: (
                            <InputAdornment position="start">
                                <SearchIcon/>
                            </InputAdornment>
                        ),
                    },
                }}
            />

            <Box
                sx={{
                    display: "flex",
                    flexDirection:
                        "column",
                    gap: 2,
                }}
            >
                {menus?.map((group) => (
                    <MenuSection
                        key={group.menu.id}
                        group={group}
                        search={search}
                    />
                ))}
            </Box>


        </Box>
    );
};