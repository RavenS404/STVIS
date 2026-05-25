import { useEffect, useState } from "react";

export function useDebouncedValue<T>(value: T, delay = 300): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
        const handle = window.setTimeout(() => setDebouncedValue(value), delay);
        return () => window.clearTimeout(handle);
    }, [value, delay]);

    return debouncedValue;
}
