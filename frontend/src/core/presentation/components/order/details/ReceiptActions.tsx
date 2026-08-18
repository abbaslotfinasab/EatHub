import {
    Button,
    DialogActions,
    Divider,
    Menu,
    MenuItem,
    Stack,
    Typography,
} from "@mui/material";

import PrintRoundedIcon from "@mui/icons-material/PrintRounded";
import PictureAsPdfRoundedIcon from "@mui/icons-material/PictureAsPdfRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import TaskAltRoundedIcon from "@mui/icons-material/TaskAltRounded";
import KeyboardArrowDownRoundedIcon from "@mui/icons-material/KeyboardArrowDownRounded";

import {useState} from "react";


interface ReceiptActionsProps {

    onPrint58?(): void;

    onPrint80?(): void;

    onDownloadPdf?(): void;

    onEdit?(): void;

    onChangeStatus?(): void;

}


export function ReceiptActions({

    onPrint58,

    onPrint80,

    onDownloadPdf,

    onEdit,

    onChangeStatus,

}: ReceiptActionsProps) {

    const [
        anchorEl,
        setAnchorEl,
    ] = useState<HTMLElement | null>(null);


    const menuOpen =
        Boolean(anchorEl);


    const handleOutputClick = (
        event: React.MouseEvent<HTMLButtonElement>,
    ) => {

        setAnchorEl(
            event.currentTarget,
        );

    };


    const handleMenuClose = () => {

        setAnchorEl(null);

    };


    const executeAction = (
        action?: () => void,
    ) => {

        setAnchorEl(null);

        action?.();

    };


    const hasOutputActions =
        Boolean(
            onPrint58 ||
            onPrint80 ||
            onDownloadPdf,
        );


    const hasActions =
        Boolean(
            hasOutputActions ||
            onEdit ||
            onChangeStatus,
        );


    if (!hasActions) {
        return null;
    }


    return (

        <DialogActions
            dir="rtl"
            sx={{
                px: {
                    xs: 2,
                    sm: 3,
                },

                py: 2,

                bgcolor: "background.paper",

                display: "block",

                direction: "rtl",
            }}
        >

            <Stack
                direction={{
                    xs: "column",
                    sm: "row",
                }}

                spacing={1.5}

                sx={{
                    width: "100%",

                           direction: "ltr",


                    /**
                     * مهم:
                     * روی flex row ترتیب را RTL می‌کنیم.
                     */
                    "@media (min-width:600px)": {
                        flexDirection: "row",
                    },
                }}
            >

                {/* =================================================
                    Output
                ================================================= */}

                {hasOutputActions && (

                    <>
                        <Button
                            fullWidth
                            size="large"
                            variant="contained"

                            onClick={
                                handleOutputClick
                            }

                            sx={{
                                flex: 1,

                                minHeight: 52,

                                borderRadius: 2.5,

                                fontWeight: 700,

                                boxShadow: 0,

                                px: 2,

                                /**
                                 * خود Button را RTL می‌کنیم.
                                 */
                                direction: "rtl",

                                /**
                                 * مهم:
                                 * محتویات Button به صورت flex
                                 * کنترل می‌شوند.
                                 */
                                display: "flex",

                                alignItems: "center",

                                justifyContent:
                                    "space-between",

                                gap: 1,

                                "&:hover": {
                                    boxShadow: 2,
                                },
                            }}
                        >

                            <span
                                style={{
                                    display: "inline-flex",

                                    alignItems: "center",

                                    gap: "8px",
                                }}
                            >

                                <PrintRoundedIcon
                                    fontSize="small"
                                />

                                <span>
                                    چاپ رسید
                                </span>

                            </span>


                            <KeyboardArrowDownRoundedIcon
                                fontSize="small"
                            />

                        </Button>


                        <Menu
                            anchorEl={anchorEl}

                            open={menuOpen}

                            onClose={
                                handleMenuClose
                            }

                            dir="rtl"

                            anchorOrigin={{
                                vertical: "top",
                                horizontal: "right",
                            }}

                            transformOrigin={{
                                vertical: "bottom",
                                horizontal: "right",
                            }}

                            slotProps={{
                                paper: {
                                    dir: "rtl",

                                    sx: {
                                        minWidth: 280,

                                        mb: 1,

                                        p: 0.75,

                                        borderRadius: 2.5,

                                        border:
                                            "1px solid",

                                        borderColor:
                                            "divider",

                                        boxShadow:
                                            "0 12px 40px rgba(0,0,0,.14)",

                                        direction: "rtl",
                                    },
                                },
                            }}
                        >

                            {onPrint80 && (

                                <MenuItem
                                    onClick={() =>
                                        executeAction(
                                            onPrint80,
                                        )
                                    }

                                    sx={{
                                        minHeight: 58,

                                        borderRadius: 2,

                                        gap: 1.5,

                                        direction: "rtl",

                                        textAlign: "right",
                                    }}
                                >

                                    <PrintRoundedIcon/>

                                    <Stack
                                        sx={{
                                            alignItems:
                                                "flex-start",
                                        }}
                                    >

                                        <Typography
                                            sx={{
                                                fontWeight: 700,

                                                fontSize: 14,

                                                direction: "rtl",

                                                textAlign:
                                                    "right",
                                            }}
                                        >
                                            چاپ رسید ۸۰ mm
                                        </Typography>


                                        <Typography
                                            variant="caption"
                                            color="text.secondary"
                                            sx={{
                                                direction: "rtl",

                                                textAlign:
                                                    "right",
                                            }}
                                        >
                                            پرینتر حرارتی
                                        </Typography>

                                    </Stack>

                                </MenuItem>

                            )}


                            {onPrint58 && (

                                <MenuItem
                                    onClick={() =>
                                        executeAction(
                                            onPrint58,
                                        )
                                    }

                                    sx={{
                                        minHeight: 58,

                                        borderRadius: 2,

                                        gap: 1.5,

                                        direction: "rtl",

                                        textAlign: "right",
                                    }}
                                >

                                    <PrintRoundedIcon/>

                                    <Stack
                                        sx={{
                                            alignItems:
                                                "flex-start",
                                        }}
                                    >

                                        <Typography
                                            sx={{
                                                fontWeight: 700,

                                                fontSize: 14,

                                                direction: "rtl",

                                                textAlign:
                                                    "right",
                                            }}
                                        >
                                            چاپ رسید ۵۸ mm
                                        </Typography>


                                        <Typography
                                            variant="caption"
                                            color="text.secondary"
                                            sx={{
                                                direction: "rtl",

                                                textAlign:
                                                    "right",
                                            }}
                                        >
                                            پرینتر حرارتی
                                        </Typography>

                                    </Stack>

                                </MenuItem>

                            )}


                            {(
                                onPrint58 ||
                                onPrint80
                            ) && onDownloadPdf && (

                                <Divider
                                    sx={{
                                        my: 0.75,
                                    }}
                                />

                            )}


                            {onDownloadPdf && (

                                <MenuItem
                                    onClick={() =>
                                        executeAction(
                                            onDownloadPdf,
                                        )
                                    }

                                    sx={{
                                        minHeight: 58,

                                        borderRadius: 2,

                                        gap: 1.5,

                                        direction: "rtl",

                                        textAlign: "right",
                                    }}
                                >

                                    <PictureAsPdfRoundedIcon/>

                                    <Stack
                                        sx={{
                                            alignItems:
                                                "flex-start",
                                        }}
                                    >

                                        <Typography
                                            sx={{
                                                fontWeight: 700,

                                                fontSize: 14,

                                                direction: "rtl",

                                                textAlign:
                                                    "right",
                                            }}
                                        >
                                            ذخیره PDF
                                        </Typography>


                                        <Typography
                                            variant="caption"
                                            color="text.secondary"
                                            sx={{
                                                direction: "rtl",

                                                textAlign:
                                                    "right",
                                            }}
                                        >
                                            دریافت نسخه دیجیتال رسید
                                        </Typography>

                                    </Stack>

                                </MenuItem>

                            )}

                        </Menu>

                    </>

                )}


                {/* =================================================
                    Change Status
                ================================================= */}

                {onChangeStatus && (

                    <Button
                        fullWidth
                        size="large"
                        variant="outlined"

                        onClick={
                            onChangeStatus
                        }

                        sx={{
                            flex: 1,

                            minHeight: 52,

                            borderRadius: 2.5,

                            fontWeight: 600,

                            whiteSpace: "nowrap",

                            direction: "rtl",

                            display: "flex",

                            alignItems: "center",

                            justifyContent: "center",

                            gap: 1,
                        }}
                    >

                        <TaskAltRoundedIcon/>

                        <span>
                            تغییر وضعیت
                        </span>

                    </Button>

                )}


                {/* =================================================
                    Edit
                ================================================= */}

                {onEdit && (

                    <Button
                        fullWidth
                        size="large"
                        variant="outlined"
                        color="inherit"

                        onClick={
                            onEdit
                        }

                        sx={{
                            flex: 1,

                            minHeight: 52,

                            borderRadius: 2.5,

                            fontWeight: 600,

                            whiteSpace: "nowrap",

                            borderColor:
                                "divider",

                            direction: "rtl",

                            display: "flex",

                            alignItems: "center",

                            justifyContent: "center",

                            gap: 1,

                            "&:hover": {
                                borderColor:
                                    "text.primary",
                            },
                        }}
                    >

                        <EditRoundedIcon/>

                        <span>
                            ویرایش سفارش
                        </span>

                    </Button>

                )}

            </Stack>

        </DialogActions>

    );

}