// src/features/business/presentation/components/BusinessPhoneField.tsx

import {
    InputAdornment,
    Stack,
    TextField,
    Typography,
} from "@mui/material";

import PhoneRoundedIcon
    from "@mui/icons-material/PhoneRounded";

interface Props {
    value: string;
    onChange: (value: string) => void;
}

export const BusinessPhoneField = ({
    value,
    onChange,
}: Props) => {
    return (
        <Stack spacing={1}>
            <Typography
                fontWeight={700}
            >
                شماره تماس
            </Typography>

            <TextField
                fullWidth
                value={value}
                placeholder="09123456789"
                onChange={(e) =>
                    onChange(e.target.value)
                }
                slotProps={{
                    input: {
                        startAdornment: (
                            <InputAdornment position="start">
                                <PhoneRoundedIcon
                                    color="action"
                                />
                            </InputAdornment>
                        ),
                    },
                }}
                sx={{
                    "& .MuiOutlinedInput-root": {
                        height: 56,
                        borderRadius: 4,
                    },
                }}
            />

            <Typography
                variant="body2"
                color="text.secondary"
            >
                این شماره برای ارتباط با مشتریان و
                اطلاعات فاکتورها استفاده خواهد شد.
            </Typography>
        </Stack>
    );
};