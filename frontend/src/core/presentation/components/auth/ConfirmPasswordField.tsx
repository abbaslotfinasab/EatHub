// src/features/auth/presentation/components/ConfirmPasswordField.tsx

import { useState } from "react";

import {
    TextField,
    InputAdornment,
    IconButton,
} from "@mui/material";

import VisibilityRoundedIcon
    from "@mui/icons-material/VisibilityRounded";

import VisibilityOffRoundedIcon
    from "@mui/icons-material/VisibilityOffRounded";

interface Props {
    value: string;
    onChange: (value: string) => void;
}

export const ConfirmPasswordField = ({
                                         value,
                                         onChange,
                                     }: Props) => {
    const [showPassword, setShowPassword] =
        useState(false);

    return (
        <TextField
            fullWidth
            label="تکرار رمز عبور"
            placeholder="••••••••"
            value={value}
            onChange={(e) =>
                onChange(e.target.value)
            }
            type={
                showPassword
                    ? "text"
                    : "password"
            }
            autoComplete="new-password"
            InputProps={{
                endAdornment: (
                    <InputAdornment position="end">
                        <IconButton
                            edge="end"
                            onClick={() =>
                                setShowPassword(
                                    (prev) => !prev
                                )
                            }
                        >
                            {showPassword ? (
                                <VisibilityOffRoundedIcon />
                            ) : (
                                <VisibilityRoundedIcon />
                            )}
                        </IconButton>
                    </InputAdornment>
                ),
            }}
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