// src/features/auth/presentation/components/OtpField.tsx

import { Box, TextField } from "@mui/material";
import { useState } from "react";

export const OtpField = () => {
    const [otp, setOtp] = useState([
        "",
        "",
        "",
        "",
        "",
        "",
    ]);

    const handleChange = (
        value: string,
        index: number
    ) => {
        if (!/^\d?$/.test(value)) {
            return;
        }

        const newOtp = [...otp];

        newOtp[index] = value;

        setOtp(newOtp);

        if (
            value &&
            index < 5
        ) {
            const nextInput =
                document.getElementById(
                    `otp-${index + 1}`
                );

            nextInput?.focus();
        }
    };

    return (
        <Box
            sx={{
                display: "flex",
                justifyContent: "center",
                gap: 1.5,
            }}
        >
            {otp.map((digit, index) => (
                <TextField
                    key={index}
                    id={`otp-${index}`}
                    value={digit}
                    onChange={(e) =>
                        handleChange(
                            e.target.value,
                            index
                        )
                    }
                    inputProps={{
                        maxLength: 1,
                        style: {
                            textAlign: "center",
                            fontSize: "22px",
                            fontWeight: 700,
                        },
                    }}
                    sx={{
                        width: 56,

                        "& .MuiOutlinedInput-root": {
                            height: 56,

                            borderRadius: 3,

                            bgcolor: "#FFFFFF",

                            "& fieldset": {
                                borderColor:
                                    "#E5E7EB",
                            },

                            "&.Mui-focused fieldset": {
                                borderColor:
                                    "#10281A",
                                borderWidth: 2,
                            },
                        },
                    }}
                />
            ))}
        </Box>
    );
};