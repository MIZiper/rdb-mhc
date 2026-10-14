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
  import { getConfig } from "./lib/utils/env";
  import { router } from "./router";
  import "./modules";
  import {
    checkAuth,
    login,
    logout,
    setAuthContext,
    type KeycloakConfig,
    type AuthState,
  } from "./lib/auth";

  setContext("mh_host", getConfig("MH_HOST"));
  setContext("router", router);

  let auth: AuthState = $state({
    authenticated: false,
    user: null,
    token: null,
    roles: [],
  });
  setAuthContext(() => auth);
  let kcConfig: KeycloakConfig | null = $state(null);

  onMount(async () => {
    const config = await fetch("/api/config").then(r => r.json());
    kcConfig = { url: config.kc_url, realm: config.kc_realm, clientId: config.kc_client_id };
    auth = await checkAuth(kcConfig);
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
      <NavItem>
        <NavLink style="color: white;" href="/query">Query</NavLink>
      </NavItem>
      <NavItem>
        <NavLink style="color: white;" href="/aggregate">Aggregate</NavLink>
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
