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

  import { BaseProcessor, registry } from "./lib/processor.js";
  import BaseViewer from "./modules/BaseViewer.svelte";
  import BaseEditor from "./modules/BaseEditor.svelte";

  setContext("mh_host", getConfig("MH_HOST"));
  setContext("router", router);

  registry.register(
    new BaseProcessor("Base.v00", "Base Item", BaseViewer, BaseEditor),
  );
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
        <NavLink style="color: white;" href="/dev-test">Test</NavLink>
      </NavItem>
    </Nav>
  </Navbar>

  <Router />
</main>
