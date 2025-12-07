import { createRouter } from "sv-router";
import MainPage from "./pages/MainPage.svelte";
import ClientAdmin from "./pages/ClientAdmin.svelte";

export const { p, navigate, isActive, route } = createRouter({
    '/': MainPage,
    '/admin/:id': ClientAdmin,
})
