import { createRouter } from "sv-router";
import MainPage from "./pages/MainPage.svelte";
import ClientAdmin from "./pages/ClientAdmin.svelte";
import RegisteredNodes from "./pages/RegisteredNodes.svelte";
import RegisteredNodeDetail from "./pages/RegisteredNodeDetail.svelte";
import ClientList from "./pages/ClientList.svelte";
import TagsSelector from "./lib/TagsSelector.svelte";

export const router = createRouter({
    '/': MainPage,
    '/admin/:id': ClientAdmin,
    '/nodes': RegisteredNodes,
    '/registered/:tag_id/:tag_str': RegisteredNodeDetail,
    '/clients': ClientList,
    '/dev-test': TagsSelector,
})
