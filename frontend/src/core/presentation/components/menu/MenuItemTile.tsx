import {
    Box,
    Typography,
    Chip,
    IconButton,
    Tooltip,
} from "@mui/material";

import EditRoundedIcon from "@mui/icons-material/EditRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import type {MenuItem} from "../../../domain/entities/product/MenuItem.ts";


interface Props {
    item: MenuItem;
    onEdit?: (item: MenuItem) => void;
    onDelete?: (item: MenuItem) => void;
}

export const MenuItemTile = ({
                                 item,
                                 onEdit,
                                 onDelete,
                             }: Props) => {
    return (
        <Box
            sx={{
                overflow: "hidden",
                borderRadius: 5,

                bgcolor: "#fff",

                border:
                    "1px solid #E2E8F0",

                transition: ".25s",

                position: "relative",

                "&:hover": {
                    transform:
                        "translateY(-4px)",

                    boxShadow:
                        "0 20px 40px rgba(0,0,0,.08)",

                    borderColor:
                        "#CBD5E1",
                },
            }}
        >
            {/* IMAGE */}
            <Box
                sx={{
                    position:
                        "relative",

                    height: 220,
                }}
            >
                <img
                    src={item.imageUrl??""}
                    alt={item.name}
                    style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                    }}
                />

                <Box
                    sx={{
                        position:
                            "absolute",

                        inset: 0,

                        background:
                            "linear-gradient(to top, rgba(0,0,0,.7), rgba(0,0,0,.1))",
                    }}
                />

                {/* ACTIONS */}
                <Box
                    sx={{
                        position:
                            "absolute",

                        top: 12,
                        right: 12,

                        display:
                            "flex",

                        gap: 1,
                    }}
                >
                    <Tooltip title="ویرایش">
                        <IconButton
                            size="small"
                            onClick={(e) => {
                                e.stopPropagation();
                                onEdit?.(
                                    item
                                );
                            }}
                            sx={{
                                bgcolor:
                                    "rgba(255,255,255,.9)",

                                "&:hover":
                                    {
                                        bgcolor:
                                            "#fff",
                                    },
                            }}
                        >
                            <EditRoundedIcon
                                fontSize="small"
                            />
                        </IconButton>
                    </Tooltip>

                    <Tooltip title="حذف">
                        <IconButton
                            size="small"
                            onClick={(e) => {
                                e.stopPropagation();
                                onDelete?.(
                                    item
                                );
                            }}
                            sx={{
                                bgcolor:
                                    "rgba(255,255,255,.9)",

                                "&:hover":
                                    {
                                        bgcolor:
                                            "#fff",
                                        color:
                                            "error.main",
                                    },
                            }}
                        >
                            <DeleteRoundedIcon
                                fontSize="small"
                            />
                        </IconButton>
                    </Tooltip>
                </Box>

                <Chip
                    label="فعال"
                    size="small"
                    sx={{
                        position:
                            "absolute",

                        top: 12,
                        left: 12,

                        bgcolor:
                            "#DCFCE7",

                        color:
                            "#166534",

                        fontWeight: 700,
                    }}
                />
            </Box>

            {/* CONTENT */}
            <Box
                sx={{
                    p: 2.5,
                }}
            >
                <Typography
                    sx={{
                        fontSize: 18,
                        fontWeight: 800,

                        mb: 1,

                        overflow:
                            "hidden",

                        textOverflow:
                            "ellipsis",

                        whiteSpace:
                            "nowrap",
                    }}
                >
                    {item.name}
                </Typography>

                {item.description && (
                    <Typography
                        sx={{
                            color:
                                "#64748B",

                            fontSize: 14,

                            mb: 2,

                            display:
                                "-webkit-box",

                            WebkitLineClamp: 2,

                            WebkitBoxOrient:
                                "vertical",

                            overflow:
                                "hidden",
                        }}
                    >
                        {
                            item.description
                        }
                    </Typography>
                )}

                <Box
                    sx={{
                        mt: 2,

                        display:
                            "flex",

                        justifyContent:
                            "space-between",

                        alignItems:
                            "center",
                    }}
                >
                    <Box>
                        <Typography
                            sx={{
                                fontSize: 12,

                                color:
                                    "#94A3B8",
                            }}
                        >
                            قیمت
                        </Typography>

                        <Typography
                            sx={{
                                fontSize: 20,

                                fontWeight: 900,

                                color:
                                    "#10281A",
                            }}
                        >
                            {item.price.toLocaleString(
                                "fa-IR"
                            )}{" "}
                            تومان
                        </Typography>
                    </Box>
                </Box>
            </Box>
        </Box>
    );
};