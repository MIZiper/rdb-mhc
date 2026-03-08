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
  import { setContext } from "svelte";
  import { getConfig } from "./utils/GetRuntimeEnv.js";
  import { router } from "./router";

  setContext("mh_host", getConfig("MH_HOST"));
  setContext("router", router);
</script>

<Styles />

<main>
  <Navbar style="background-color:whitesmoke;">
    <NavbarBrand>
      <img src="/tc-logo.png" alt="TC logo" height="36px" />
      Resource database
    </NavbarBrand>
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
