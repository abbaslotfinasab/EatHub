// src/features/auth/presentation/components/IdentifierField.tsx

import TextField from "@mui/material/TextField";

type Props = {
    value: string;
    onChange: (value: string) => void;
};

export const IdentifierField = ({
    value,
    onChange,
}: Props) => {
    return (
        <TextField
            fullWidth
            label="ایمیل یا شماره موبایل"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="09123456789 یا example@email.com"
            variant="outlined"
            autoComplete="username"
            sx={{
                "& .MuiOutlinedInput-root": {
                    borderRadius: 3,
                    bgcolor: "#FFFFFF",

                    "& fieldset": {
                        borderColor: "#E5E7EB",
                    },

                    "&:hover fieldset": {
                        borderColor: "#CBD5E1",
                    },

                    "&.Mui-focused fieldset": {
                        borderColor: "#10281A",
                        borderWidth: 2,
                    },
                },

                "& .MuiInputLabel-root.Mui-focused": {
                    color: "#10281A",
                },
            }}
        />
    );
};