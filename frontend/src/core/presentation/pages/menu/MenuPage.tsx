import {
    Box,
    CircularProgress,
    Fab,
    Paper,
    Typography,
    TextField,
    InputAdornment,
    Dialog,
    DialogTitle,
    DialogContent,
    Button,
    DialogActions,
} from "@mui/material";

import SearchIcon from "@mui/icons-material/Search";
import AddIcon from "@mui/icons-material/Add";

import {useNavigate} from "react-router-dom";
import {useState} from "react";

import {useGetMenus} from "../../hooks/menu/useGetMenus.ts";
import {MenuSection} from "../../components/menu/MenuSection.tsx";
import {StatCard} from "../../components/menu/StatCard.tsx";

import {useAuthStore} from "../../store/auth.store.ts";
import type {Menu} from "../../../domain/entities/product/menu/Menu.ts";
import {useDeleteMenu} from "../../hooks/menu/useDeleteMenu.tsx";

export const MenuPage = () => {
    const navigate = useNavigate();

    const me = useAuthStore((s) => s.me);

    const [search, setSearch] = useState("");

    const [deleteTarget, setDeleteTarget] = useState<Menu | null>(null);

    const {
    mutate: deleteMenu,
} = useDeleteMenu();

    const {data, isLoading, isError} =
        useGetMenus();

    if (isLoading) {
        return (
            <Box
                sx={{
                    height: "100vh",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                }}
            >
                <CircularProgress/>
            </Box>
        );
    }

    if (isError) {
        return (
            <Box>
                Failed to load menus
            </Box>
        );
    }

    const totalMenus =
        data?.length ?? 0;

    const totalItems =
        data?.reduce(
            (acc, group) =>
                acc +
                group.items.length,
            0
        ) ?? 0;

    const publicMenuUrl =
        `${window.location.origin}/products/${me?.active_business?.slug}/menu`;

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
                            🍽️ منو دیجیتال
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
                                title="منو"
                                value={
                                    totalMenus
                                }
                            />

                            <StatCard
                                title="آیتم"
                                value={
                                    totalItems
                                }
                            />

                            <StatCard
                                title="وضعیت"
                                value="فعال"
                            />
                        </Box>
                    </Box>

                    {me?.active_business
                        ?.qr && (
                        <Paper
                            elevation={0}
                            onClick={() =>
                                window.open(
                                    publicMenuUrl,
                                    "_blank"
                                )
                            }
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
                            <Box
                                component="img"
                                src={
                                    me
                                        .active_business
                                        .qr
                                }
                                alt="QR Menu"
                                sx={{
                                    width:
                                        "100%",

                                    height:
                                        "100%",

                                    objectFit:
                                        "contain",
                                }}
                            />
                        </Paper>
                    )}
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
                {data?.map((group) => (
                    <MenuSection
                        key={group.menu.id}
                        group={group}
                        search={search}
                        onEdit={(menu) => navigate(`/menus/${menu.id}/edit`)}
                        onDelete={(menu) => setDeleteTarget(menu)}
                    />
                ))}
            </Box>

            <Fab
                variant="extended"
                onClick={() =>
                    navigate(
                        "/menus/create"
                    )
                }
                sx={{
                    position:
                        "fixed",

                    left: 24,
                    bottom: 24,

                    bgcolor:
                        "#10281A",

                    color: "#fff",

                    "&:hover": {
                        bgcolor:
                            "#173724",
                    },
                }}
            >
                <AddIcon/>
                منو جدید
            </Fab>

             <Dialog
            open={!!deleteTarget}
            onClose={() => setDeleteTarget(null)}
        >
            <DialogTitle>حذف منو</DialogTitle>

            <DialogContent>
                آیا مطمئنید میخواهید این منو حذف شود؟
            </DialogContent>

            <DialogActions>
                <Button onClick={() => setDeleteTarget(null)}>
                    لغو
                </Button>

                <Button
                    color="error"
                    onClick={() => {
                if (!deleteTarget) return;

                deleteMenu(deleteTarget.id??"");

                setDeleteTarget(null);
            }}
                >
                    حذف
                </Button>
            </DialogActions>
        </Dialog>

        </Box>
    );

};