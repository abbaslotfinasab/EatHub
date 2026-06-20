// src/features/business/presentation/components/BusinessAddressField.tsx

import {
    InputAdornment,
    Stack,
    TextField,
    Typography,
} from "@mui/material";

import LocationOnRoundedIcon
    from "@mui/icons-material/LocationOnRounded";

interface Props {
    value: string;
    onChange: (value: string) => void;
}

export const BusinessAddressField = ({
    value,
    onChange,
}: Props) => {
    return (
        <Stack spacing={1}>
            <Typography
                fontWeight={700}
            >
                آدرس
            </Typography>

            <TextField
                fullWidth
                multiline
                minRows={4}
                value={value}
                placeholder="خیابان، کوچه، پلاک، واحد ..."
                onChange={(e) =>
                    onChange(e.target.value)
                }
                slotProps={{
                    input: {
                        startAdornment: (
                            <InputAdornment
                                position="start"
                                sx={{
                                    alignSelf: "flex-start",
                                    mt: 1.5,
                                }}
                            >
                                <LocationOnRoundedIcon
                                    color="action"
                                />
                            </InputAdornment>
                        ),
                    },
                }}
                sx={{
                    "& .MuiOutlinedInput-root": {
                        borderRadius: 4,
                        alignItems: "flex-start",

                        py: 1,
                    },
                }}
            />

            <Typography
                variant="body2"
                color="text.secondary"
            >
                این آدرس در پروفایل و اطلاعات
                کسب‌وکار نمایش داده خواهد شد.
            </Typography>
        </Stack>
    );
};