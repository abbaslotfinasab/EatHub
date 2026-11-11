import {
    Box,
    Typography,
    Chip,
    IconButton,
    Tooltip,
} from "@mui/material";

import EditRoundedIcon from "@mui/icons-material/EditRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import type {MenuItem} from "../../../domain/entities/product/menu/MenuItem.ts";
import {buildMediaUrl} from "../../utils/media.ts";


const allergenLabels: Record<string, string> = {
    celery: "کرفس",
    cereals_gluten: "غلات حاوی گلوتن",
    crustaceans: "سخت‌پوستان",
    eggs: "تخم‌مرغ",
    fish: "ماهی",
    lupin: "لوپین",
    milk: "شیر",
    molluscs: "نرم‌تنان",
    mustard: "خردل",
    peanuts: "بادام‌زمینی",
    sesame: "کنجد",
    soybeans: "سویا",
    sulphites: "سولفیت",
    tree_nuts: "مغزها",
};

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
                borderRadius: 1,

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
                    src={
                        item.imageUrl
                            ? buildMediaUrl(item.imageUrl)
                            : ""
                    }
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
                    label={item.isAvailable === true ? "فعال" : "غیرفعال"}
                    size="small"
                    sx={{
                        position: "absolute",
                        top: 12,
                        left: 12,
                        bgcolor: item.isAvailable === true ? "#DCFCE7" : "#FEE2E2",
                        color: item.isAvailable === true ? "#166534" : "#991B1B",
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

                {(item.recipeAllergens != null || item.catalogProductAllergens != null) ? (
                    <Box sx={{ mt: 2, display: "flex", flexDirection: "column", gap: 1.25 }}>
                        {item.recipeAllergens != null ? (
                            <Box>
                                <Typography sx={{ fontSize: 12, color: "text.secondary", mb: 0.75 }}>
                                    آلرژن‌های رسپی
                                </Typography>
                                {item.recipeAllergens.length ? (
                                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                                        {item.recipeAllergens.map((allergen) => (
                                        <Chip
                                            key={`recipe-${allergen.code}`}
                                            size="small"
                                            variant="outlined"
                                            color={allergen.presence === "contains" ? "error" : "warning"}
                                            label={`${allergenLabels[allergen.code] ?? allergen.code} · ${allergen.presence === "contains" ? "حاوی" : "احتمال وجود"}`}
                                        />
                                        ))}
                                    </Box>
                                ) : (
                                    <Typography sx={{ fontSize: 12, color: "text.disabled" }}>
                                        اعلامیه‌ای برای آلرژن‌های رسپی ثبت نشده است.
                                    </Typography>
                                )}
                            </Box>
                        ) : null}
                        {item.catalogProductAllergens != null ? (
                            <Box>
                                <Typography sx={{ fontSize: 12, color: "text.secondary", mb: 0.75 }}>
                                    اعلام آلرژن محصول
                                </Typography>
                                {item.catalogProductAllergens.length ? (
                                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                                        {item.catalogProductAllergens.map((allergen) => (
                                        <Chip
                                            key={`catalog-${allergen.code}`}
                                            size="small"
                                            variant="outlined"
                                            color={allergen.presence === "contains" ? "error" : "warning"}
                                            label={`${allergenLabels[allergen.code] ?? allergen.code} · ${allergen.presence === "contains" ? "حاوی" : "احتمال وجود"}`}
                                        />
                                        ))}
                                    </Box>
                                ) : (
                                    <Typography sx={{ fontSize: 12, color: "text.disabled" }}>
                                        اعلامیه‌ای برای آلرژن‌های محصول ثبت نشده است.
                                    </Typography>
                                )}
                            </Box>
                        ) : null}
                    </Box>
                ) : null}

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
                            {Number(item.price).toLocaleString("fa-IR")}
                            {" "}
                            تومان
                        </Typography>
                    </Box>
                </Box>
            </Box>
        </Box>
    );
};