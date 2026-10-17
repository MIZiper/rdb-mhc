<script lang="ts">
  import {
    Dropdown,
    DropdownItem,
    DropdownMenu,
    DropdownToggle,
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
  <Navbar color="primary" theme="dark">
    <NavbarBrand class="link-light">
      <img src="/tc-logo.png" alt="TC logo" height="36px" />
      Resource database
    </NavbarBrand>
    <Nav>
      <NavItem>
        <NavLink class="link-light" href="/new">New</NavLink>
      </NavItem>
      <Dropdown nav>
        <DropdownToggle nav caret class="link-light">Advanced Search</DropdownToggle>
        <DropdownMenu>
          <DropdownItem href="/query">Cross-type Query</DropdownItem>
          <DropdownItem href="/aggregate">Cross-type Aggregate</DropdownItem>
        </DropdownMenu>
      </Dropdown>
      {#if auth.authenticated}
        <NavItem>
          <NavLink class="link-light" href="/mine">My Workspace</NavLink>
        </NavItem>
      {/if}
      {#if auth.authenticated}
        <NavItem>
          <span class="nav-link text-warning">{auth.user?.name || auth.user?.sub}</span>
        </NavItem>
        <NavItem>
          <NavLink class="link-light" onclick={doLogout}>Logout</NavLink>
        </NavItem>
      {:else}
        <NavItem>
          <NavLink class="link-light" onclick={doLogin}>Login</NavLink>
        </NavItem>
      {/if}
    </Nav>
  </Navbar>

  <Router />
</main>
