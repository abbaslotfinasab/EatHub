// src/presentation/components/form/FormInput.tsx
import { useFormContext } from 'react-hook-form';
import type {InputHTMLAttributes} from 'react';
import get from 'lodash/get';

interface FormInputProps extends InputHTMLAttributes<HTMLInputElement> {
    name: string;
    label: string;
}

export const FormInput = ({ name, label, className = '', ...props }: FormInputProps) => {
    const { register, formState: { errors } } = useFormContext();
    const error = get(errors, name)?.message as string | undefined;

    return (
        <div className="w-full">
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
                {label}
            </label>
            <input
                {...register(name)}
                {...props}
                className={`
                    w-full rounded-lg border border-gray-300 bg-white px-4 py-3 
                    text-base text-gray-900 shadow-sm transition duration-200
                    placeholder:text-gray-400
                    focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20
                    disabled:bg-gray-100 disabled:text-gray-500
                    ${error ? 'border-red-500 focus:border-red-500' : ''}
                    ${className}
                `}
            />
            {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
        </div>
    );
};