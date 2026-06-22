// src/features/business/presentation/components/BusinessLogoUploader.tsx

import {useRef} from "react";

import {
    Avatar,
    Box,
    IconButton,
    Stack,
    Typography,
} from "@mui/material";

import PhotoCameraRoundedIcon
    from "@mui/icons-material/PhotoCameraRounded";

interface Props {
    logo: File | null;
    previewUrl?: string;
    onChange: (file: File | null) => void;
}

export const BusinessLogoUploader = ({
                                         previewUrl,
                                         onChange,
                                     }: Props) => {
    const inputRef =
        useRef<HTMLInputElement>(null);

    const handleSelectImage = (
        e: React.ChangeEvent<HTMLInputElement>
    ) => {
        const file = e.target.files?.[0];

        if (!file) return;

        onChange(file);
    };

    return (
        <Stack
            sx={{
                spacing: 2,
                alignItems: "center",
            }}
        >
            <Box
                sx={{
                    position: "relative",
                }}
            >
                <Avatar
                    src={previewUrl}
                    sx={{
                        width: 120,
                        height: 120,

                        bgcolor: "#F3F4F6",

                        border: "2px dashed",
                        borderColor: "divider",

                        fontSize: 40,
                    }}
                />

                <IconButton
                    onClick={() =>
                        inputRef.current?.click()
                    }
                    sx={{
                        position: "absolute",

                        bottom: 0,
                        right: 0,

                        bgcolor: "background.paper",

                        border: "1px solid",

                        borderColor: "divider",

                        boxShadow:
                            "0px 4px 12px rgba(0,0,0,.08)",

                        "&:hover": {
                            bgcolor: "grey.100",
                        },
                    }}
                >
                    <PhotoCameraRoundedIcon/>
                </IconButton>

                <input
                    ref={inputRef}
                    hidden
                    type="file"
                    accept="image/*"
                    onChange={handleSelectImage}
                />
            </Box>

            <Box sx={{
                textAlign: "center",
            }}>
                <Typography
                    sx={{
                        fontWeight: 600
                    }}
                >
                    لوگوی کسب‌وکار
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    PNG یا JPG تا ۵ مگابایت
                </Typography>
            </Box>
        </Stack>
    );
};