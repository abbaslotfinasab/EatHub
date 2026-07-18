import {
    Box,
    LinearProgress,
    Stack,
    Typography,
    alpha,
    useTheme,
} from "@mui/material";

import {
    CheckCircle2,
    LoaderCircle,
    XCircle,
} from "lucide-react";


interface UploadProgressProps {

    progress: number;

    filename?: string;

    size?: number;

    status:
        | "idle"
        | "uploading"
        | "success"
        | "error";

    errorMessage?: string;

}


export function UploadProgress({
                                   progress,
                                   filename,
                                   size,
                                   status,
                                   errorMessage,
                               }: UploadProgressProps) {


    const theme = useTheme();


    const formatSize = (
        bytes?: number,
    ) => {

        if (!bytes) {
            return "";
        }

        if (bytes < 1024) {
            return `${bytes} B`;
        }


        if (bytes < 1024 * 1024) {
            return `${(
                bytes / 1024
            ).toFixed(1)} KB`;
        }


        return `${(
            bytes /
            (1024 * 1024)
        ).toFixed(1)} MB`;

    };


    const getStatusColor = () => {

        switch (status) {

            case "success":
                return theme.palette.success.main;


            case "error":
                return theme.palette.error.main;


            default:
                return theme.palette.primary.main;
        }
    };


    return (

        <Box
            sx={{
                mt: 2,

                p: 2,

                borderRadius: 2,

                bgcolor: alpha(
                    getStatusColor(),
                    .06,
                ),

                border: "1px solid",

                borderColor: alpha(
                    getStatusColor(),
                    .2,
                ),
            }}
        >

            <Stack spacing={1.5}>


                {/* Header */}

                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >
                    <Stack
                        sx={{
                            flexDirection: "row",
                            gap: 1,
                            alignItems: "center",
                        }}
                    >

                        {
                            status === "uploading" && (

                                <LoaderCircle
                                    size={18}
                                    className="spin"
                                />

                            )
                        }


                        {
                            status === "success" && (

                                <CheckCircle2
                                    size={18}
                                    color={
                                        theme.palette.success.main
                                    }
                                />

                            )
                        }


                        {
                            status === "error" && (

                                <XCircle
                                    size={18}
                                    color={
                                        theme.palette.error.main
                                    }
                                />

                            )
                        }


                        <Typography
                            variant="body2"
                            noWrap
                            sx={{
                                fontWeight: 600,
                            }}
                        >
                            {
                                filename ??
                                "در حال پردازش فایل"
                            }
                        </Typography>


                    </Stack>


                    <Typography
                        variant="caption"
                        color="text.secondary"
                    >

                        {
                            status === "uploading"
                                ? `${progress}%`
                                : formatSize(size)

                        }

                    </Typography>


                </Stack>


                {/* Progress Bar */}

                {
                    status === "uploading" && (

                        <LinearProgress

                            variant="determinate"

                            value={progress}

                            sx={{

                                height: 8,

                                borderRadius: 10,

                            }}

                        />

                    )
                }


                {/* Success */}

                {
                    status === "success" && (

                        <Typography
                            variant="caption"
                            color="success.main"
                        >
                            آپلود با موفقیت انجام شد
                        </Typography>

                    )
                }


                {/* Error */}

                {
                    status === "error" && (

                        <Typography
                            variant="caption"
                            color="error.main"
                        >
                            {
                                errorMessage ??
                                "خطا در آپلود فایل"
                            }
                        </Typography>

                    )
                }


            </Stack>


        </Box>

    );
}