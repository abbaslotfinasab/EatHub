import {
    Box,
    Fade,
    IconButton,
    Skeleton,
    Stack,
    Typography,
    alpha,
    useTheme,
} from "@mui/material";

import {
    Pencil,
    Trash2,
    ImageOff,
} from "lucide-react";


import {useState} from "react";

interface UploadPreviewProps {
    src: string;

    filename?: string;

    onReplace(): void;

    onDelete(): void;

    disabled?: boolean;
}

export function UploadPreview({
                                  src,
                                  filename,
                                  onReplace,
                                  onDelete,
                                  disabled = false,
                              }: UploadPreviewProps) {

    const theme = useTheme();

    const [loaded, setLoaded] = useState(false);

    const [error, setError] = useState(false);

    const [hover, setHover] = useState(false);


    return (
        <Stack spacing={2}>
            <Box
                onMouseEnter={() => setHover(true)}
                onMouseLeave={() => setHover(false)}
                sx={{
                    position: "relative",

                    borderRadius: 3,

                    overflow: "hidden",

                    border: "1px solid",

                    borderColor: "divider",

                    aspectRatio: "1",

                    bgcolor: "grey.100",
                }}
            >
                {!loaded && !error && (
                    <Skeleton
                        variant="rectangular"
                        width="100%"
                        height="100%"
                    />
                )}

                {error ? (
                    <Stack
                        sx={{
                            gap: 2,
                            alignItems: "center",
                            justifyContent: "center",
                            position: "absolute",
                            inset: 0,
                        }}
                    >
                        <ImageOff
                            size={42}
                            color={theme.palette.text.disabled}
                        />

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            پیش نمایش موجود نیست
                        </Typography>
                    </Stack>
                ) : (
                    <Box
                        component="img"
                        src={src}
                        alt={filename}
                        loading="lazy"
                        onLoad={() => setLoaded(true)}
                        onError={() => setError(true)}
                        sx={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                            opacity: loaded ? 1 : 0,
                            transition: "opacity .3s ease",
                        }}
                    />
                )}

                <Fade in={hover && !disabled}>
                    <Stack
                        direction="row"
                        spacing={1}
                        sx={{
                            position: "absolute",

                            inset: 0,

                            alignItems: "center",

                            justifyContent: "center",

                            bgcolor: alpha("#000", .45),
                        }}
                    >
                        <IconButton
                            onClick={onReplace}
                            sx={{
                                bgcolor: "white",

                                "&:hover": {
                                    bgcolor: "grey.100",
                                },
                            }}
                        >
                            <Pencil size={18}/>
                        </IconButton>

                        <IconButton
                            color="error"
                            onClick={onDelete}
                            sx={{
                                bgcolor: "white",

                                "&:hover": {
                                    bgcolor: "grey.100",
                                },
                            }}
                        >
                            <Trash2 size={18}/>
                        </IconButton>
                    </Stack>
                </Fade>
            </Box>

            {filename && (
                <Typography
                    variant="body2"
                    color="text.secondary"
                    noWrap
                >
                    {filename}
                </Typography>
            )}
        </Stack>
    );
}