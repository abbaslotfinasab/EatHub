// src/features/auth/presentation/components/FullNameField.tsx

import TextField from "@mui/material/TextField";

interface Props {
    value: string;
    onChange: (value: string) => void;
}

export const FullNameField = ({
                                  value,
                                  onChange,
                              }: Props) => {
    return (
        <TextField
            fullWidth
            label="نام و نام خانوادگی"
            placeholder="مثلاً عباس لطفی نسب"
            autoComplete="name"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            sx={{
                "& .MuiOutlinedInput-root": {
                    height: 56,
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