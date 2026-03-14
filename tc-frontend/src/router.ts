import { createRouter } from "sv-router";
import MainPage from "./pages/MainPage.svelte";
import ResourcePage from "./pages/ResourceDetail.svelte";
import NewResource from "./pages/NewResource.svelte";
import SearchResult from "./pages/TagSearchResult.svelte";
import PushDialogSvelte from "./interop/PushDialog.svelte";
import TypeProcPage from "./pages/TypeProcPage.svelte";


export const router = createRouter({
    '/': MainPage,
    '/items/:id': ResourcePage,
    '/dev-test': PushDialogSvelte,
    '/new': NewResource,
    '/tags/:tag_id/:tag_str': SearchResult,
    "/type/:name": TypeProcPage,
})
