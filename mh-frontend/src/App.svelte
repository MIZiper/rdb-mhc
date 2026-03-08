<script lang="ts">
  import { Router } from "sv-router";

  import { Styles } from "@sveltestrap/sveltestrap";
  import {
    Navbar,
    NavbarBrand,
    Collapse,
    Nav,
    NavItem,
    NavLink,
    NavbarToggler,
    Dropdown,
    DropdownToggle,
    DropdownMenu,
    DropdownItem,
  } from "@sveltestrap/sveltestrap";
  import { router } from "./router";
  import { setContext } from "svelte";

  setContext("router", router);
  let isOpen: boolean = $state(false);
</script>

<Styles />

<main>
  <Navbar style="background-color:whitesmoke;">
    <NavbarBrand>
      <img src="/mh-logo.png" alt="MetaHub logo" height="36px" />
      MetaHub
    </NavbarBrand>

    <Nav>
      <!-- <NavItem>
        <NavLink href="#">Link</NavLink>
      </NavItem>
      <Dropdown nav {isOpen} toggle={() => (isOpen = !isOpen)}>
        <DropdownToggle nav caret>Dropdown</DropdownToggle>
        <DropdownMenu>
          <DropdownItem header>Header</DropdownItem>
          <DropdownItem disabled>Action</DropdownItem>
          <DropdownItem>Another Action</DropdownItem>
          <DropdownItem divider />
          <DropdownItem>Another Action</DropdownItem>
        </DropdownMenu>
      </Dropdown> -->
      <NavItem>
        <NavLink href="/admin/">Admin</NavLink>
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
