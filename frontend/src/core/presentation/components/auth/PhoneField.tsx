// src/features/auth/presentation/components/PhoneField.tsx

import TextField from "@mui/material/TextField";

interface Props {
    value: string;
    onChange: (value: string) => void;
}

export const PhoneField = ({
                               value,
                               onChange,
                           }: Props) => {
    return (
        <TextField
            fullWidth
            label="شماره موبایل"
            placeholder="09123456789"
            type="tel"
            autoComplete="tel"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            sx={{
                "& .MuiOutlinedInput-root": {
                    height: 56,
                    dir: "ltr",
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

                "& .MuiInputBase-input": {
                    textAlign: "left",
                },

                "& .MuiInputLabel-root.Mui-focused": {
                    color: "#10281A",
                },
            }}
        />
    );
};