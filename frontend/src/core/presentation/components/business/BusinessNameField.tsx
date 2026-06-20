// src/features/business/presentation/components/BusinessNameField.tsx

import {
    Stack,
    TextField,
    Typography,
} from "@mui/material";

interface Props {
    value: string;
    onChange: (value: string) => void;
}

export const BusinessNameField = ({
    value,
    onChange,
}: Props) => {
    return (
        <Stack spacing={1}>
            <Typography
                fontWeight={700}
            >
                نام کسب‌وکار
            </Typography>

            <TextField
                fullWidth
                value={value}
                placeholder="مثلاً رستوران آریا"
                onChange={(e) =>
                    onChange(e.target.value)
                }
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
                این نام در داشبورد و فاکتورها نمایش داده خواهد شد.
            </Typography>
        </Stack>
    );
};