import {
    Divider,
    Stack,
    Typography,
} from "@mui/material";

import StickyNote2RoundedIcon from "@mui/icons-material/StickyNote2Rounded";

interface ReceiptNotesProps {
    notes?: string | null;
}

export function ReceiptNotes({
                                 notes,
                             }: ReceiptNotesProps) {

    return (

        <Stack
            sx={{
                gap: 2,
            }}
        >

            <Stack
                sx={{
                    flexDirection: "row",
                    gap: 1,
                    alignItems: "center",
                }}
            >

                <StickyNote2RoundedIcon
                    color="primary"
                />

                <Typography
                    variant="h6"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    توضیحات سفارش
                </Typography>

            </Stack>

            <Divider/>

            {notes ? (

                <Typography
                    sx={{
                        lineHeight: 2,
                        whiteSpace: "pre-wrap",
                    }}
                >
                    {notes}
                </Typography>

            ) : (

                <Typography
                    sx={{
                        color: "text.secondary",
                        fontStyle: "italic",
                    }}
                >
                    توضیحی برای این سفارش ثبت نشده است.
                </Typography>

            )}

        </Stack>

    );

}