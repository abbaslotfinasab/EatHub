import {
    TextField,
    InputAdornment,
    IconButton,
    Paper,
} from "@mui/material";

import SearchIcon from "@mui/icons-material/Search";
import CloseIcon from "@mui/icons-material/Close";

type MenuSearchProps = {
    value: string;
    onChange: (value: string) => void;
};

export const MenuSearch = ({
    value,
    onChange,
}: MenuSearchProps) => {
    return (
        <Paper
            elevation={0}
            sx={{
                position: "sticky",
                top: 0,
                zIndex: 100,

                py: 2,

                backgroundColor: "rgba(250,250,248,.92)",
                backdropFilter: "blur(12px)",

                borderBottom: "1px solid",
                borderColor: "divider",
            }}
        >
            <TextField
                fullWidth
                value={value}
                placeholder="جست و حو"
                onChange={(e) =>
                    onChange(e.target.value)
                }
                variant="outlined"
                size="small"
                InputProps={{
                    startAdornment: (
                        <InputAdornment position="start">
                            <SearchIcon />
                        </InputAdornment>
                    ),

                    endAdornment: value ? (
                        <InputAdornment position="end">
                            <IconButton
                                size="small"
                                onClick={() =>
                                    onChange("")
                                }
                            >
                                <CloseIcon
                                    fontSize="small"
                                />
                            </IconButton>
                        </InputAdornment>
                    ) : null,
                }}
                sx={{
                    "& .MuiOutlinedInput-root": {
                        borderRadius: 999,

                        backgroundColor: "#fff",

                        "& fieldset": {
                            borderColor: "#E5E7EB",
                        },

                        "&:hover fieldset": {
                            borderColor: "#D1D5DB",
                        },

                        "&.Mui-focused fieldset":
                            {
                                borderColor:
                                    "#10281A",
                            },
                    },
                }}
            />
        </Paper>
    );
};