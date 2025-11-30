<script lang="ts">
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
  import ClientAdmin from "./pages/ClientAdmin.svelte";
  let isOpen: boolean = $state(false);
</script>

<Styles />

<main>
  <Navbar>
    <NavbarBrand href="/">MetaHub</NavbarBrand>

    <Nav>
      <NavItem>
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
      </Dropdown>
      <NavItem>
        <NavLink href="#">Link</NavLink>
      </NavItem>
      <NavItem>
        <NavLink href="#">Another Link</NavLink>
      </NavItem>
      <NavItem>
        <NavLink disabled href="#">Disabled Link</NavLink>
      </NavItem>
    </Nav>
  </Navbar>

  <ClientAdmin clientId={1} />
</main>

<style>
</style>
