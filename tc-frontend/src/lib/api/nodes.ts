import type {
    AggregateRequest,
    AggregateResult,
    NodeQuery,
    NodeQueryResult,
} from "../../types";
import { postJson, request } from "./client";

export function queryNodes(body: NodeQuery): Promise<NodeQueryResult> {
    return postJson<NodeQueryResult>("/api/nodes/query", body);
}

export function aggregateNodes(body: AggregateRequest): Promise<AggregateResult> {
    return postJson<AggregateResult>("/api/nodes/aggregate", body);
}

export async function batchNodeData(ids: string[]): Promise<{ items: any[] }> {
    if (ids.length === 0) return { items: [] };
    return request<{ items: any[] }>(
        `/api/nodes/data?ids=${encodeURIComponent(ids.join(","))}`,
    );
}
