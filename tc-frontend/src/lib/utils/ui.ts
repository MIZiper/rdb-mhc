/** Shared visual helpers that stay on the Bootstrap palette. */

export const CHART_COLORS = [
    "var(--bs-primary)",
    "var(--bs-danger)",
    "var(--bs-warning)",
    "var(--bs-success)",
    "var(--bs-info)",
    "var(--bs-indigo)",
    "var(--bs-orange)",
    "var(--bs-teal)",
    "var(--bs-purple)",
    "var(--bs-secondary)",
];

export function chartColor(index: number): string {
    return CHART_COLORS[index % CHART_COLORS.length];
}

export function hashString(value: string): number {
    let hash = 0;
    for (let i = 0; i < value.length; i++) {
        hash = (hash << 5) - hash + value.charCodeAt(i);
        hash |= 0;
    }
    return Math.abs(hash);
}

/** Stable, hash-derived color for a data type. */
export function typeColor(dataType: string): string {
    const key = dataType.split(".")[0] || dataType;
    return `hsl(${hashString(key) % 360} 65% 45%)`;
}

export function statusColor(status: string): string {
    switch (status) {
        case "draft": return "secondary";
        case "pending_review": return "warning";
        case "published": return "success";
        case "archived": return "dark";
        default: return "secondary";
    }
}

export function statusLabel(status: string): string {
    switch (status) {
        case "draft": return "Draft";
        case "pending_review": return "In Review";
        case "published": return "Published";
        case "archived": return "Archived";
        default: return status;
    }
}

export function visibilityColor(visibility: string): string {
    switch (visibility) {
        case "internal": return "info";
        case "confidential": return "danger";
        default: return "secondary";
    }
}
