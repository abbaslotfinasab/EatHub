// presentation/components/order/OrderMenuPicker/MenuSearch.tsx

import SearchRoundedIcon from "@mui/icons-material/SearchRounded";

import {
    InputAdornment,
    TextField,
} from "@mui/material";

interface MenuSearchProps {
    value: string;

    onChange: (value: string) => void;
}

export const MenuSearch = ({
    value,
    onChange,
}: MenuSearchProps) => {
    return (
        <TextField
            fullWidth
            placeholder="جستجوی غذا..."
            value={value}
            onChange={(e) =>
                onChange(
                    e.target.value,
                )
            }
            slotProps={{
                input: {
                    startAdornment: (
                        <InputAdornment position="start">
                            <SearchRoundedIcon />
                        </InputAdornment>
                    ),
                },
            }}
            sx={{
                "& .MuiOutlinedInput-root": {
                    borderRadius: 3,
                },
            }}
        />
    );
};