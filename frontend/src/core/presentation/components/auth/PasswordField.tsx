// src/features/auth/presentation/components/PasswordField.tsx

import {useState} from "react";

import {
    TextField,
    InputAdornment,
    IconButton,
} from "@mui/material";

import VisibilityRoundedIcon
    from "@mui/icons-material/VisibilityRounded";

import VisibilityOffRoundedIcon
    from "@mui/icons-material/VisibilityOffRounded";

type Props = {
    value: string;
    onChange: (value: string) => void;
};


export const PasswordField = ({value, onChange}: Props) => {

    const [showPassword, setShowPassword] =
        useState(false);

    return (
        <TextField
            fullWidth
            label="رمز عبور"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="••••••••"
            type={
                showPassword
                    ? "text"
                    : "password"
            }
            autoComplete="current-password"
            slotProps={{
                input: {
                    endAdornment: (
                        <InputAdornment position="end">
                            <IconButton
                                edge="end"
                                onClick={() =>
                                    setShowPassword((prev) => !prev)
                                }
                            >
                                {showPassword ? (
                                    <VisibilityOffRoundedIcon/>
                                ) : (
                                    <VisibilityRoundedIcon/>
                                )}
                            </IconButton>
                        </InputAdornment>
                    ),
                },
            }}
            sx={{
                "& .MuiOutlinedInput-root": {
                    height: 56,

                    borderRadius: 3,

                    bgcolor: "#FFFFFF",

                    "& fieldset": {
                        borderColor:
                            "#E5E7EB",
                    },

                    "&:hover fieldset": {
                        borderColor:
                            "#CBD5E1",
                    },

                    "&.Mui-focused fieldset": {
                        borderColor:
                            "#10281A",

                        borderWidth: 2,
                    },
                },

                "& .MuiInputLabel-root.Mui-focused":
                    {
                        color: "#10281A",
                    },
            }}
        />
    );
};