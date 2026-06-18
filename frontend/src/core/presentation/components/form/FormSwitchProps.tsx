// src/presentation/components/form/FormSwitch.tsx
import { useFormContext } from 'react-hook-form';
import get from 'lodash/get';

interface FormSwitchProps {
    name: string;
    label: string;
    description?: string;
}

export const FormSwitch = ({ name, label, description }: FormSwitchProps) => {
    const { register, formState: { errors } } = useFormContext();
    const error = get(errors, name)?.message as string | undefined;

    return (
        <div className="flex items-center justify-between">
            <div>
                <label className="text-sm font-medium text-gray-700">{label}</label>
                {description && <p className="text-xs text-gray-500">{description}</p>}
            </div>
            <label className="relative inline-flex cursor-pointer items-center">
                <input type="checkbox" {...register(name)} className="peer sr-only" />
                <div className="h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all after:content-[''] peer-checked:bg-red-600 peer-checked:after:translate-x-full"></div>
            </label>
            {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
        </div>
    );
};