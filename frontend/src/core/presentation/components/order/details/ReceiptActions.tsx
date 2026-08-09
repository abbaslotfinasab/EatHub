import {
    Button,
    DialogActions,
    Menu,
    MenuItem,
    Stack,
    Typography,
    Divider,
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
            sx={{
                px: {
                    xs: 2,
                    sm: 3,
                },

                py: 2,

                bgcolor: "background.paper",

                display: "block",
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

                            startIcon={
                                <PrintRoundedIcon/>
                            }

                            endIcon={
                                <KeyboardArrowDownRoundedIcon/>
                            }

                            onClick={
                                handleOutputClick
                            }

                            sx={{
                                flex: 1,

                                minHeight: 52,

                                borderRadius: 2.5,

                                fontWeight: 700,

                                boxShadow: 0,

                                justifyContent:
                                    "space-between",

                                px: 2,

                                "&:hover": {
                                    boxShadow: 2,
                                },
                            }}
                        >
                            چاپ رسید
                        </Button>


                        <Menu
                            anchorEl={anchorEl}
                            open={menuOpen}
                            onClose={
                                handleMenuClose
                            }

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
                                    }}
                                >

                                    <PrintRoundedIcon/>

                                    <Stack>

                                        <Typography
                                            sx={{
                                                fontWeight: 700,
                                                fontSize: 14,
                                            }}
                                        >
                                            mm چاپ رسید ۸۰
                                        </Typography>

                                        <Typography
                                            variant="caption"
                                            color="text.secondary"
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
                                    }}
                                >

                                    <PrintRoundedIcon/>

                                    <Stack>

                                        <Typography
                                            sx={{
                                                fontWeight: 700,
                                                fontSize: 14,
                                            }}
                                        >
                                            mm چاپ رسید ۵۸
                                        </Typography>

                                        <Typography
                                            variant="caption"
                                            color="text.secondary"
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
                                    }}
                                >

                                    <PictureAsPdfRoundedIcon/>

                                    <Stack>

                                        <Typography
                                            sx={{
                                                fontWeight: 700,
                                                fontSize: 14,
                                            }}
                                        >
                                            ذخیره PDF
                                        </Typography>

                                        <Typography
                                            variant="caption"
                                            color="text.secondary"
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

                        startIcon={
                            <TaskAltRoundedIcon/>
                        }

                        onClick={
                            onChangeStatus
                        }

                        sx={{
                            flex: 1,

                            minHeight: 52,

                            borderRadius: 2.5,

                            fontWeight: 600,

                            whiteSpace: "nowrap",
                        }}
                    >
                        تغییر وضعیت
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

                        startIcon={
                            <EditRoundedIcon/>
                        }

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

                            "&:hover": {
                                borderColor:
                                    "text.primary",
                            },
                        }}
                    >
                        ویرایش سفارش
                    </Button>

                )}

            </Stack>

        </DialogActions>

    );

}