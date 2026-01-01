import { createRouter } from "sv-router";
import MainPage from "./pages/MainPage.svelte";
import ResourcePage from "./pages/ResourceDetail.svelte";
import Searchbar from "./lib/Searchbar.svelte";


export const { p, navigate, isActive, route } = createRouter({
    '/': MainPage,
    '/items/:id': ResourcePage,
    '/dev-test': Searchbar,
})
