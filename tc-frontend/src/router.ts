import { createRouter } from "sv-router";
import MainPage from "./pages/MainPage.svelte";
import ResourcePage from "./pages/ResourceDetail.svelte";
import Searchbar from "./lib/Searchbar.svelte";
import NewResource from "./pages/NewResource.svelte";
import SearchResult from "./pages/SearchResult.svelte";


export const { p, navigate, isActive, route } = createRouter({
    '/': MainPage,
    '/items/:id': ResourcePage,
    '/dev-test': Searchbar,
    '/new': NewResource,
    '/tags/:tag_id/:tag_str': SearchResult,
})
