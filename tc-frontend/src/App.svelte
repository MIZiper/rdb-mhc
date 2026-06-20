<script lang="ts">
  import {
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
  import BaseTypeViewer from "./modules/BaseTypeViewer.svelte";
  import TabularEditor from "./modules/TabularEditor.svelte";
  import TabularViewer from "./modules/TabularViewer.svelte";
  import TabularTypeViewer from "./modules/TabularTypeViewer.svelte";
  import {
    checkAuth,
    login,
    logout,
    setAuthContext,
    type KeycloakConfig,
    type AuthState,
  } from "./lib/auth.js";

  setContext("mh_host", getConfig("MH_HOST"));
  setContext("router", router);

  registry.register(
    new BaseProcessor("Base.v00", "Base Item", BaseViewer, BaseEditor, BaseTypeViewer),
  );
  registry.register(
    new BaseProcessor("Tabular.v00", "Tabular Data", TabularViewer, TabularEditor, TabularTypeViewer),
  );

  let auth: AuthState = $state({
    authenticated: false,
    user: null,
    token: null,
    roles: [],
  });
  setAuthContext({ authenticated: false, user: null, token: null, roles: [] });
  let kcConfig: KeycloakConfig | null = $state(null);

  onMount(async () => {
    const config = await fetch("/api/config").then(r => r.json());
    kcConfig = { url: config.kc_url, realm: config.kc_realm, clientId: config.kc_client_id };
    auth = await checkAuth(kcConfig);
    setAuthContext($state.snapshot(auth));
  });

  async function doLogin() { if (kcConfig) await login(kcConfig); }
  async function doLogout() { if (kcConfig) await logout(kcConfig); }
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
      {#if auth.authenticated}
        <NavItem>
          <span class="nav-link username">{auth.user?.name || auth.user?.sub}</span>
        </NavItem>
        <NavItem>
          <NavLink style="color: white;" onclick={doLogout}>Logout</NavLink>
        </NavItem>
      {:else}
        <NavItem>
          <NavLink style="color: white;" onclick={doLogin}>Login</NavLink>
        </NavItem>
      {/if}
    </Nav>
  </Navbar>

  <Router />
</main>

<style>
  .username {
    color: #ffeaa7;
  }
</style>
