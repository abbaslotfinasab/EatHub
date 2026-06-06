// src/presentation/components/form/FormFile.tsx
import { useFormContext } from 'react-hook-form';
import type {ChangeEvent} from 'react';

interface FormFileProps {
    name: string;
    label: string;
    accept?: string;
}

export const FormFile = ({ name, label, accept = 'image/*' }: FormFileProps) => {
    const { setValue} = useFormContext();

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        setValue(name, file, { shouldValidate: true });
    };

    return (
        <div className="w-full">
            <label className="mb-1.5 block text-sm font-medium text-gray-700">{label}</label>
            <input
                type="file"
                accept={accept}
                onChange={handleChange}
                className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none"
            />
        </div>
    );
};