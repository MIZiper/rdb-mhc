export {
    checkAuth,
    login,
    logout,
    getToken,
    getAuthState,
    isAuthenticated,
    authFetch,
    setAuthContext,
    getAuthContext,
    hasRole,
    hasAnyRole,
    getRoles,
    authReady,
} from "./lib/auth";
export type { KeycloakConfig, AuthState } from "./lib/auth";

export type {
    ItemMeta,
    ItemDetail,
    TypeDescriptor,
    FieldSpec,
    FieldKey,
    QueryFilter,
    NodeQuery,
    AggregateRequest,
    AggregateGroup,
} from "./types";

export { getConfig } from "./lib/utils/env";

export {
    fetchTypes,
    fetchType,
    fetchFieldKeys,
    fetchFieldValues,
    queryNodes,
    aggregateNodes,
    batchNodeData,
    fetchTagsInfo,
    constructTagsById,
} from "./lib/api";

export {
    registry,
    BaseProcessor,
    type ViewerProps,
    type EditorProps,
    type EditorExports,
    type TypeViewerProps,
} from "./modules/registry";

export { default as NewResource } from "./components/NewResource.svelte";
export { default as ResourceItem } from "./components/ResourceItem.svelte";
export { default as Pagination } from "./components/Pagination.svelte";
export { default as Stack } from "./components/ui/Stack.svelte";
export { default as Legend } from "./components/ui/Legend.svelte";
export { default as ImageTile } from "./components/ui/ImageTile.svelte";
export { default as TagChip } from "./components/ui/TagChip.svelte";
export { default as ResourceDetail } from "./pages/ResourceDetail.svelte";
export { default as MainPage } from "./pages/MainPage.svelte";
export { default as TagSearchResult } from "./pages/TagSearchResult.svelte";
export { default as NewTypedResource } from "./pages/NewTypedResource.svelte";
export { default as QueryPage } from "./pages/QueryPage.svelte";
export { default as AggregatePage } from "./pages/AggregatePage.svelte";
