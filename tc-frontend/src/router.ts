import { createRouter } from "sv-router";
import MainPage from "./pages/MainPage.svelte";
import ResourceDetailPage from "./pages/ResourceDetail.svelte";
import NewResource from "./lib/NewResource.svelte";
import TagSearchPage from "./pages/TagSearchResult.svelte";
import PushDialogSvelte from "./interop/PushDialog.svelte";
import TypeProcPage from "./pages/TypeProcPage.svelte";


export const router = createRouter({
    '/': MainPage,
    '/items/:id': ResourceDetailPage,
    '/dev-test': PushDialogSvelte,
    '/new': NewResource,
    '/tags/:tag_id/:tag_str': TagSearchPage,
    "/type/:type_name": TypeProcPage,
})
