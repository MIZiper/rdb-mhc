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

export interface NodeState {
    id: string;
    title: string;
    description: string | null;
    data_type?: string | null;
    status: string;
    updated_at: string;
    tag_ids: number[];
    source_system: string | null;
    source_id: string | null;
    source_part: string | null;
    source_url: string | null;
    source_linked_at: string | null;
    source_linked_by: string | null;
}

export function getNodeState(id: string): Promise<NodeState> {
    return request<NodeState>(`/api/nodes/${id}/state`);
}

export function updateNodeState(id: string, status: string): Promise<NodeState> {
    return request<NodeState>(`/api/nodes/${id}/state`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
    });
}

export function attachNodeSource(
    id: string,
    source: {
        source_system: string;
        source_id: string;
        source_part: string;
        source_url: string;
    },
): Promise<NodeState> {
    return request<NodeState>(`/api/nodes/${id}/source`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(source),
    });
}

export function detachNodeSource(id: string): Promise<NodeState> {
    return request<NodeState>(`/api/nodes/${id}/source`, { method: "DELETE" });
}
