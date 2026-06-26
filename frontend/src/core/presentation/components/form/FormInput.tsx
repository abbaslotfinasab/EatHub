import { TextField } from "@mui/material";
import type { TextFieldProps } from "@mui/material/TextField";
import { useFormContext } from "react-hook-form";
import get from "lodash/get";

interface FormInputProps extends Omit<TextFieldProps, "name"> {
    name: string;
}

export const FormInput = ({
    name,
    type,
    ...props
}: FormInputProps) => {
    const {
        register,
        formState: { errors },
    } = useFormContext();

    const error = get(errors, name)?.message as string | undefined;

    return (
        <TextField
            {...register(name, {
                valueAsNumber: type === "number",
            })}
            type={type}
            error={!!error}
            helperText={error}
            fullWidth
            {...props}
        />
    );
};