// src/presentation/components/form/FormTextarea.tsx

import { TextField } from "@mui/material";
import { useFormContext } from "react-hook-form";
import type { TextareaHTMLAttributes } from "react";
import get from "lodash/get";

interface FormTextareaProps
    extends TextareaHTMLAttributes<HTMLTextAreaElement> {
    name: string;
    label: string;
}

export const FormTextarea = ({
    name,
    label,
    rows = 3,
}: FormTextareaProps) => {
    const {
        register,
        formState: { errors },
    } = useFormContext();

    const error = get(errors, name)?.message as string | undefined;

    return (
        <TextField
            {...register(name)}
            label={label}
            multiline
            rows={rows}
            error={!!error}
            helperText={error}
        />
    );
};