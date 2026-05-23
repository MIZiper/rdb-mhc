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
  import { checkAuth, login, logout, setAuthContext, type KeycloakConfig } from "./lib/auth.js";

  setContext("mh_host", getConfig("MH_HOST"));
  setContext("router", router);

  registry.register(
    new BaseProcessor("Base.v00", "Base Item", BaseViewer, BaseEditor),
  );

  let auth = $state({ authenticated: false, user: null as { sub: string; name: string } | null, token: null as string | null });
  let kcConfig: KeycloakConfig | null = $state(null);

  onMount(async () => {
    const config = await fetch("/api/config").then(r => r.json());
    // setContext("mh_host", config.mh_host || getConfig("MH_HOST"));
    kcConfig = { url: config.kc_url, realm: config.kc_realm, clientId: config.kc_client_id };
    auth = await checkAuth(kcConfig);
    setAuthContext(auth);
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
