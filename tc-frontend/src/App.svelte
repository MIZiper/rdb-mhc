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
  import { route } from "./router";
  import { setContext } from "svelte";
  import { getConfig } from "./utils/GetRuntimeEnv.js";

  setContext("mh_host", getConfig("MH_HOST"));
  setContext("route", route);
</script>

<Styles />

<main>
  <Navbar style="background-color:whitesmoke;">
    <NavbarBrand>Resource database</NavbarBrand>
    <Nav>
      <NavItem>
        <NavLink href="/new">New</NavLink>
      </NavItem>
      <NavItem>
        <NavLink href="/dev-test">Test</NavLink>
      </NavItem>
    </Nav>
  </Navbar>

  <Router />
</main>
