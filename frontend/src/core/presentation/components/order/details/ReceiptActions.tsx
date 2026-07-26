import {
    Button,
    DialogActions,
    Stack,
} from "@mui/material";

import PrintRoundedIcon from "@mui/icons-material/PrintRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import TaskAltRoundedIcon from "@mui/icons-material/TaskAltRounded";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";

interface ReceiptActionsProps {

    onClose(): void;

    onPrint?(): void;

    onEdit?(): void;

    onChangeStatus?(): void;

}

export function ReceiptActions({

    onClose,

    onPrint,

    onEdit,

    onChangeStatus,

}: ReceiptActionsProps) {

    return (

        <DialogActions
            sx={{
                px: 3,
                py: 2,
                borderTop: "1px solid",
                borderColor: "divider",
            }}
        >

            <Stack
                direction="row"
                spacing={1}
                sx={{
                    width: "100%",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: 1,
                }}
            >

                <Stack
                    direction="row"
                    spacing={1}
                >

                    {onPrint && (

                        <Button
                            variant="outlined"
                            startIcon={<PrintRoundedIcon />}
                            onClick={onPrint}
                        >
                            چاپ فاکتور
                        </Button>

                    )}

                    {onEdit && (

                        <Button
                            variant="outlined"
                            startIcon={<EditRoundedIcon />}
                            onClick={onEdit}
                        >
                            ویرایش سفارش
                        </Button>

                    )}

                    {onChangeStatus && (

                        <Button
                            variant="contained"
                            startIcon={<TaskAltRoundedIcon />}
                            onClick={onChangeStatus}
                        >
                            تغییر وضعیت
                        </Button>

                    )}

                </Stack>

                <Button
                    color="inherit"
                    startIcon={<CloseRoundedIcon />}
                    onClick={onClose}
                >
                    بستن
                </Button>

            </Stack>

        </DialogActions>

    );

}