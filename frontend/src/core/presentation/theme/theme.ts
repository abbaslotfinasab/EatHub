// src/presentation/theme/theme.ts

import {createTheme} from "@mui/material/styles";

export const theme = createTheme({

    palette: {
        primary: {
            main: "#10281A",
        },
    },

    shape: {
        borderRadius: 12,
    },

    components: {
        MuiOutlinedInput: {
            styleOverrides: {
                root: {
                    borderRadius: 12,

                    "&:hover .MuiOutlinedInput-notchedOutline": {
                        borderColor: "#10281A",
                    },

                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                        borderColor: "#10281A",
                        borderWidth: 2,
                    },
                },
            },
        },

        MuiInputLabel: {
            styleOverrides: {
                root: {
                    "&.Mui-focused": {
                        color: "#10281A",
                    },
                },
            },
        },

        MuiTextField: {
            defaultProps: {
                fullWidth: true,
                variant: "outlined",
            },
        },
    },
});