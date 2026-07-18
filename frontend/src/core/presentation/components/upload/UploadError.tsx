import {
    Alert,
    Button,
    Stack,
    Typography,
} from "@mui/material";

import {
    RefreshCcw,
    Trash2,
} from "lucide-react";


interface UploadErrorProps {

    message?: string;

    filename?: string;

    onRetry?: () => void;

    onDelete?: () => void;

}


export function UploadError({
                                message = "خطایی هنگام آپلود فایل رخ داد.",
                                filename,
                                onRetry,
                                onDelete,
                            }: UploadErrorProps) {


    return (

        <Alert
            severity="error"
            sx={{
                borderRadius: 3,
                mt: 2,
            }}
        >

            <Stack spacing={1.5}>


                <Typography
                    variant="subtitle2"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    آپلود فایل انجام نشد
                </Typography>


                {
                    filename && (

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {filename}
                        </Typography>

                    )
                }


                <Typography
                    variant="body2"
                >
                    {message}
                </Typography>


                <Stack
                    direction="row"
                    spacing={1}
                >

                    {
                        onRetry && (

                            <Button
                                size="small"
                                variant="outlined"
                                startIcon={
                                    <RefreshCcw size={16}/>
                                }
                                onClick={onRetry}
                            >
                                تلاش مجدد
                            </Button>

                        )
                    }


                    {
                        onDelete && (

                            <Button
                                size="small"
                                color="error"
                                variant="outlined"
                                startIcon={
                                    <Trash2 size={16}/>
                                }
                                onClick={onDelete}
                            >
                                حذف فایل
                            </Button>

                        )
                    }


                </Stack>


            </Stack>


        </Alert>

    );
}