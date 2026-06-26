import TextField from "@mui/material/TextField";

type Props = { value: string; onChange: (value: string) => void; };
export const EmailField = ({value, onChange}: Props) => {
    return (<TextField fullWidth label="ایمیل" value={value} onChange={(e) => onChange(e.target.value)}
                       placeholder="example@email.com" type="email" variant="outlined" autoComplete="email" sx={{
        "& .MuiOutlinedInput-root": {
            borderRadius: 3,
            bgcolor: "#FFFFFF",
            "& fieldset": {borderColor: "#E5E7EB",},
            "&:hover fieldset": {borderColor: "#CBD5E1",},
            "&.Mui-focused fieldset": {borderColor: "#10281A", borderWidth: 2,},
        }, "& .MuiInputLabel-root.Mui-focused": {color: "#10281A",},
    }}/>);
};