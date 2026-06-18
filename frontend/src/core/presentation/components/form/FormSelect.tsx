// src/presentation/components/form/FormSelect.tsx
import { useFormContext } from 'react-hook-form';
import get from 'lodash/get';

interface Option {
    value: string;
    label: string;
}

interface FormSelectProps {
    name: string;
    label: string;
    options: Option[];
    className?: string;
}

export const FormSelect = ({ name, label, options, className = '' }: FormSelectProps) => {
    const { register, formState: { errors } } = useFormContext();
    const error = get(errors, name)?.message as string | undefined;

    return (
        <div className="w-full">
            <label className="mb-1.5 block text-sm font-medium text-gray-700">{label}</label>
            <select
                {...register(name)}
                className={`w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-base shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 ${
                    error ? 'border-red-500' : ''
                } ${className}`}
            >
                {options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                        {opt.label}
                    </option>
                ))}
            </select>
            {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
        </div>
    );
};