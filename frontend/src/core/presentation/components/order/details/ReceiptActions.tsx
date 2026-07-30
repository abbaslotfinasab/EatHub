import {
    Button,
    DialogActions,
    Divider,
    Stack,
} from "@mui/material";

import EditRoundedIcon from "@mui/icons-material/EditRounded";
import TaskAltRoundedIcon from "@mui/icons-material/TaskAltRounded";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";

interface ReceiptActionsProps {
    onClose(): void;

    onPrint?(): void;

    onEdit?(): void;

    onChangeStatus?(): void;

    onDownloadPdf?(): void;


}

function PictureAsPdfRoundedIcon() {
    return null;
}

export function ReceiptActions({
                                   onClose,
                                   onEdit,
                                   onChangeStatus,
                                   onDownloadPdf,

                               }: ReceiptActionsProps) {

    return (

        <DialogActions
            sx={{
                p: 3,
                borderTop: "1px solid",
                borderColor: "divider",
                bgcolor: "background.paper",
            }}
        >

            <Stack
                spacing={2}
                sx={{
                    width: "100%",
                }}
            >

                {/* Primary Action */}

                {/* Primary Action */}

                {onDownloadPdf && (

                    <Button
                        fullWidth
                        size="large"
                        variant="contained"
                        startIcon={<PictureAsPdfRoundedIcon/>}
                        onClick={onDownloadPdf}
                        sx={{
                            height: 56,
                            borderRadius: 3,
                            fontWeight: 700,
                            textTransform: "none",
                            boxShadow: 0,

                            "&:hover": {
                                boxShadow: 2,
                            },
                        }}
                    >
                        دانلود PDF رسید
                    </Button>

                )}
                {/* Secondary Actions */}

                {(onEdit || onChangeStatus) && (

                    <Stack
                        direction={{
                            xs: "column",
                            sm: "row",
                        }}
                        spacing={2}
                    >

                        {onChangeStatus && (

                            <Button
                                fullWidth
                                size="large"
                                variant="outlined"
                                color="primary"
                                startIcon={<TaskAltRoundedIcon/>}
                                onClick={onChangeStatus}
                                sx={{
                                    height: 48,
                                    borderRadius: 2.5,
                                }}
                            >
                                تغییر وضعیت
                            </Button>

                        )}

                        {onEdit && (

                            <Button
                                fullWidth
                                size="large"
                                variant="outlined"
                                color="inherit"
                                startIcon={<EditRoundedIcon/>}
                                onClick={onEdit}
                                sx={{
                                    height: 48,
                                    borderRadius: 2.5,
                                }}
                            >
                                ویرایش سفارش
                            </Button>

                        )}

                    </Stack>

                )}

                <Divider/>

                <Button
                    fullWidth
                    size="large"
                    color="inherit"
                    startIcon={<CloseRoundedIcon/>}
                    onClick={onClose}
                    sx={{
                        height: 46,
                        borderRadius: 2,
                    }}
                >
                    بستن
                </Button>

            </Stack>

        </DialogActions>

    );

}