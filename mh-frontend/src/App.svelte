<script lang="ts">
  import { Router } from "sv-router";

  import { Styles } from "@sveltestrap/sveltestrap";
  import {
    Navbar,
    NavbarBrand,
    Nav,
    NavItem,
    NavLink,
  } from "@sveltestrap/sveltestrap";
  import { router } from "./router";
  import { setContext } from "svelte";

  setContext("router", router);
</script>

<Styles />

<main>
  <Navbar style="background-color:whitesmoke;">
    <NavbarBrand>
      <img src="/mh-logo.png" alt="MetaHub logo" height="36px" />
      MetaHub
    </NavbarBrand>

    <Nav>
      <NavItem>
        <NavLink href="/clients">Clients</NavLink>
      </NavItem>
      <NavItem>
        <NavLink href="/nodes">Registered Nodes</NavLink>
      </NavItem>
      <NavItem>
        <NavLink href="/dev-test">Test Page</NavLink>
      </NavItem>
    </Nav>
  </Navbar>

  <Router />
</main>

<style>
</style>
