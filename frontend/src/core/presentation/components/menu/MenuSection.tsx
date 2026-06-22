import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Box,
    Chip,
    Typography,
    IconButton,
    Tooltip,
} from "@mui/material";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import RestaurantMenuIcon from "@mui/icons-material/RestaurantMenu";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";

import { MenuGrid } from "./MenuGrid";

export const MenuSection = ({
    group,
    search,
    onEdit,
    onDelete,
}) => {
    const filteredItems = group.items.filter(
        (item) =>
            item.name
                .toLowerCase()
                .includes(search.toLowerCase())
    );

    if (
        search &&
        filteredItems.length === 0
    ) {
        return null;
    }

    return (
        <Accordion
            disableGutters
            elevation={0}
            defaultExpanded
            sx={{
                overflow: "hidden",
                borderRadius:
                    "24px !important",
                border:
                    "1px solid #E5E7EB",
                bgcolor: "#fff",
                transition: ".25s",

                "&:before": {
                    display: "none",
                },

                "&:hover": {
                    borderColor:
                        "#CBD5E1",

                    boxShadow:
                        "0 10px 30px rgba(15,23,42,.05)",
                },
            }}
        >
            <AccordionSummary
                expandIcon={
                    <ExpandMoreIcon />
                }
                sx={{
                    px: 3,
                    py: 1.5,

                    "& .MuiAccordionSummary-content":
                        {
                            margin: 0,
                        },
                }}
            >
                <Box
                    sx={{
                        width: "100%",

                        display: "flex",

                        justifyContent:
                            "space-between",

                        alignItems:
                            "center",

                        gap: 2,
                    }}
                >
                    <Box
                        sx={{
                            display: "flex",
                            alignItems:
                                "center",
                            gap: 2,
                        }}
                    >
                        <Box
                            sx={{
                                width: 52,
                                height: 52,

                                borderRadius: 3,

                                bgcolor:
                                    "#F1F5F9",

                                display: "flex",

                                alignItems:
                                    "center",

                                justifyContent:
                                    "center",

                                color:
                                    "#10281A",
                            }}
                        >
                            <RestaurantMenuIcon />
                        </Box>

                        <Box>
                            <Typography
                                sx={{
                                    fontWeight: 800,
                                    fontSize: 18,
                                }}
                            >
                                {
                                    group.menu
                                        .name
                                }
                            </Typography>

                            <Typography
                                sx={{
                                    color:
                                        "#64748B",
                                    fontSize: 13,
                                }}
                            >
                                {
                                    group.menu
                                        .description
                                }
                            </Typography>
                        </Box>
                    </Box>

                    <Box
                        sx={{
                            display: "flex",
                            alignItems:
                                "center",
                            gap: 1,
                        }}
                    >
                        <Chip
                            label={`${filteredItems.length} آیتم`}
                            sx={{
                                fontWeight: 700,

                                bgcolor:
                                    "#ECFDF5",

                                color:
                                    "#166534",

                                borderRadius: 999,
                            }}
                        />

                        <Tooltip title="ویرایش منو">
                            <IconButton
                                size="small"
                                onClick={(
                                    e
                                ) => {
                                    e.stopPropagation();


                                }}
                                sx={{
                                    bgcolor:
                                        "#F8FAFC",

                                    "&:hover":
                                        {
                                            bgcolor:
                                                "#E2E8F0",
                                        },
                                }}
                            >
                                <EditRoundedIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>

                        <Tooltip title="حذف منو">
                            <IconButton
                                size="small"
                                onClick={(
                                    e
                                ) => {
                                    e.stopPropagation();

                                    onDelete?.(
                                        group.menu
                                    );
                                }}
                                sx={{
                                    bgcolor:
                                        "#FEF2F2",

                                    color:
                                        "#DC2626",

                                    "&:hover":
                                        {
                                            bgcolor:
                                                "#FEE2E2",
                                        },
                                }}
                            >
                                <DeleteRoundedIcon fontSize="small" />
                            </IconButton>
                        </Tooltip>
                    </Box>
                </Box>
            </AccordionSummary>

            <AccordionDetails
                sx={{
                    px: 3,
                    pb: 3,
                    pt: 0,
                }}
            >
                <Box
                    sx={{
                        height: 1,
                        bgcolor:
                            "#F1F5F9",
                        mb: 3,
                    }}
                />

                <MenuGrid
                    items={
                        filteredItems
                    }
                />
            </AccordionDetails>
        </Accordion>
    );
};