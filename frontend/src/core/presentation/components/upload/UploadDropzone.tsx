import {
    Box,
    Button,
    Stack,
    Typography,
    alpha,
    useTheme,
} from "@mui/material";

import {
    ImagePlus,
    UploadCloud,
} from "lucide-react";

import {
    useRef,
    useState,
    type ChangeEvent,
    type DragEvent,
} from "react";

interface UploadDropzoneProps {
    onSelect(file: File): void;

    disabled?: boolean;

    accept?: string;

    maxSize?: number;

    title?: string;

    subtitle?: string;
}

export function UploadDropzone({
                                   onSelect,
                                   disabled = false,
                                   accept = "image/*",
                                   maxSize = 5 * 1024 * 1024,
                                   title = "تصویر را انتخاب کنید",
                                   subtitle = "یا فایل را اینجا رها کنید",
                               }: UploadDropzoneProps) {

    const theme = useTheme();

    const inputRef = useRef<HTMLInputElement>(null);

    const [dragging, setDragging] = useState(false);

    const validate = (file: File) => {

        if (file.size > maxSize) {

            alert("حجم فایل بیشتر از حد مجاز است.");

            return;
        }

        onSelect(file);
    };

    const handleChange = (
        e: ChangeEvent<HTMLInputElement>,
    ) => {

        const file = e.target.files?.[0];

        if (!file) return;

        validate(file);

        e.target.value = "";
    };

    const handleDrop = (
        e: DragEvent<HTMLDivElement>,
    ) => {

        e.preventDefault();

        e.stopPropagation();

        setDragging(false);

        const file = e.dataTransfer.files?.[0];

        if (!file) return;

        validate(file);
    };

    return (
        <>
            <input
                hidden
                ref={inputRef}
                type="file"
                accept={accept}
                onChange={handleChange}
            />

            <Box
                onClick={() =>
                    !disabled &&
                    inputRef.current?.click()
                }
                onDragEnter={(e) => {
                    e.preventDefault();
                    setDragging(true);
                }}
                onDragOver={(e) => {
                    e.preventDefault();
                    setDragging(true);
                }}
                onDragLeave={(e) => {
                    e.preventDefault();
                    setDragging(false);
                }}
                onDrop={handleDrop}
                sx={{
                    cursor: disabled
                        ? "default"
                        : "pointer",

                    border: "2px dashed",

                    borderColor: dragging
                        ? "primary.main"
                        : "divider",

                    borderRadius: 3,

                    p: 4,

                    transition: ".25s",

                    bgcolor: dragging
                        ? alpha(
                            theme.palette.primary.main,
                            0.06,
                        )
                        : "background.paper",

                    "&:hover": {
                        borderColor:
                        theme.palette.primary.main,

                        bgcolor: alpha(
                            theme.palette.primary.main,
                            0.04,
                        ),
                    },
                }}
            >
                <Stack
                    sx={{
                        gap: 2,
                        alignItems: "center",
                    }}
                >
                    <Box
                        sx={{
                            width: 70,
                            height: 70,

                            borderRadius: "50%",

                            bgcolor: alpha(
                                theme.palette.primary.main,
                                0.08,
                            ),

                            display: "flex",

                            alignItems: "center",

                            justifyContent: "center",
                        }}
                    >
                        {dragging ? (
                            <UploadCloud
                                size={34}
                                color={
                                    theme.palette.primary.main
                                }
                            />
                        ) : (
                            <ImagePlus
                                size={34}
                                color={
                                    theme.palette.primary.main
                                }
                            />
                        )}
                    </Box>

                    <Stack
                        sx={{
                            gap: 1,
                            alignItems: "center",
                        }}
                    >
                        <Typography
                            variant="subtitle1"
                            sx={{
                                fontWeight: 700,
                            }}
                        >
                            {title}
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                                textAlign: "center",
                            }}
                        >
                            {subtitle}
                        </Typography>

                        <Typography
                            variant="caption"
                            color="text.disabled"
                        >
                            PNG • JPG • WEBP
                        </Typography>
                    </Stack>

                    <Button
                        variant="contained"
                        disableElevation
                        disabled={disabled}
                    >
                        انتخاب فایل
                    </Button>
                </Stack>
            </Box>
        </>
    );
}