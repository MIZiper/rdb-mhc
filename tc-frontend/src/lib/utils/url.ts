import type { QueryFilter } from "../../types";

export function parseCsv(value: unknown): string[] {
    if (value === null || value === undefined) return [];
    return String(value)
        .split(",")
        .map((part) => part.trim())
        .filter(Boolean);
}

export function parseIdCsv(value: unknown): number[] {
    const ids = parseCsv(value)
        .map((part) => Number(part))
        .filter((id): id is number => Number.isInteger(id));
    return [...new Set(ids)];
}

export function encodeCsv(values: Iterable<string>): string | null {
    const parts = [...values].filter(Boolean);
    return parts.length > 0 ? parts.join(",") : null;
}

export function encodeIdCsv(values: Iterable<number | null>): string | null {
    const ids = [...new Set([...values].filter((id): id is number => Number.isInteger(id)))];
    return ids.length > 0 ? ids.join(",") : null;
}

export function encodeFilters(filters: Array<{ key: string; op: string; value: any }>): string | null {
    if (filters.length === 0) return null;
    return JSON.stringify(
        filters.map((filter) => ({
            key: filter.key,
            op: filter.op,
            value: filter.value === null || filter.value === undefined
                ? ""
                : String(filter.value),
        })),
    );
}

export function parseFilters(value: unknown): QueryFilter[] {
    if (value === null || value === undefined || value === "") return [];
    try {
        const parsed: unknown = JSON.parse(String(value));
        if (!Array.isArray(parsed)) return [];
        return parsed.flatMap((item) => {
            if (item === null || typeof item !== "object") return [];
            const { key, op, value } = item as Record<string, unknown>;
            if (typeof key !== "string" || key === "") return [];
            if (typeof op !== "string" || op === "") return [];
            return [{
                key,
                op: op as QueryFilter["op"],
                value: value === null || value === undefined ? "" : String(value),
            }];
        });
    } catch {
        return [];
    }
}

export function canonicalSearch(search: string): string {
    const params = new URLSearchParams(search);
    params.sort();
    return params.toString();
}

export function stringParam(params: URLSearchParams, key: string): string | undefined {
    if (!params.has(key)) return undefined;
    return params.get(key) ?? "";
}

export function boolParam(value: unknown): boolean {
    return value === true || value === 1 || value === "1" || value === "true";
}
