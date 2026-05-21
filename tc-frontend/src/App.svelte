<script lang="ts">
  import {
    Button,
    Nav,
    Navbar,
    NavbarBrand,
    NavItem,
    NavLink,
    Styles,
  } from "@sveltestrap/sveltestrap";

  import { Router } from "sv-router";
  import { setContext, onMount } from "svelte";
  import { getConfig } from "./utils/GetRuntimeEnv.js";
  import { router } from "./router";

  import { BaseProcessor, registry } from "./lib/processor.js";
  import BaseViewer from "./modules/BaseViewer.svelte";
  import BaseEditor from "./modules/BaseEditor.svelte";
  import { checkAuth, login, logout, isAuthenticated, getAuthState, setAuthContext } from "./lib/auth.js";

  setContext("mh_host", getConfig("MH_HOST"));
  setContext("router", router);

  registry.register(
    new BaseProcessor("Base.v00", "Base Item", BaseViewer, BaseEditor),
  );

  let auth = $state({ authenticated: false, user: null as { sub: string; name: string } | null, token: null as string | null });

  onMount(async () => {
    auth = await checkAuth();
    setAuthContext(auth);
  });

  async function doLogin() { await login(); }
  async function doLogout() { await logout(); }
</script>

<Styles />

<main>
  <Navbar style="background-color:#49a9a7;">
    <NavbarBrand style="color: white;">
      <img src="/tc-logo.png" alt="TC logo" height="36px" />
      Resource database
    </NavbarBrand>
    <Nav>
      <NavItem>
        <NavLink style="color: white;" href="/new">New</NavLink>
      </NavItem>
      {#if auth.authenticated}
        <NavItem>
          <NavLink style="color: white;" href="/mine">My Workspace</NavLink>
        </NavItem>
      {/if}
      <NavItem>
        <NavLink style="color: white;" href="/dev-test">Test</NavLink>
      </NavItem>
    </Nav>
    <Nav style="margin-left: auto;">
      {#if auth.authenticated}
        <NavItem>
          <span class="nav-link" style="color: white; cursor: default;">
            {auth.user?.name || auth.user?.sub}
          </span>
        </NavItem>
        <NavItem>
          <Button size="sm" color="light" onclick={doLogout}>Logout</Button>
        </NavItem>
      {:else}
        <NavItem>
          <Button size="sm" color="light" onclick={doLogin}>Login</Button>
        </NavItem>
      {/if}
    </Nav>
  </Navbar>

  <Router />
</main>
