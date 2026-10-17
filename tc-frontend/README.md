# TC frontend (TemplateClient)

Svelte 5 + TypeScript single-page app for the Resource Database. It also
publishes a small component/library surface (`src/index.ts`).

## Project layout

```
src/
  main.ts           # app entry: mounts App, loads styles + module registry
  App.svelte        # shell, auth bootstrap, navigation
  router.ts         # routes
  index.ts          # library exports (npm package surface)
  types/            # shared types (ItemMeta, descriptors, query DTOs)
  lib/
    auth.ts         # Keycloak integration + authFetch
    api/            # typed backend clients (client, nodes, types, files, metahub)
    utils/          # env runtime config, formula engine, image helpers
    useNodeList.svelte.ts  # shared list loading/pagination state
  components/       # shared widgets (ResourceItem, NewResource, Pagination, ...)
  modules/          # content-type renderers + registry
    registry.ts     # processor registry (type -> viewer/editor/typeViewer)
    index.ts        # built-in registrations
    base/ tabular/ formula/ image/
  pages/            # route pages
  dev/              # development-only widgets
  styles/           # global styles
```

## Runtime configuration

The container entrypoint rewrites `public/env.js` from `FRONTEND_*` env vars.
Currently exposed:

- `MH_HOST` — MetaHub base URL (used to resolve tag names)

## Styling

The UI is built on Bootstrap 5 via `@sveltestrap/sveltestrap`. Bootstrap and
Bootstrap Icons are loaded by the `<Styles />` component in `App.svelte` (CDN),
so downstream consumers must render `<Styles />` or provide the same styles.

- Prefer sveltestrap components (`Card`, `Button`, `Input`, `Table`, …) and
  Bootstrap utility classes over one-off CSS.
- Use Bootstrap semantic colors and CSS variables (`var(--bs-body-color)`,
  `var(--bs-border-color)`, `var(--bs-primary)`, …) instead of hard-coded
  values.
- Scoped `<style>` blocks are reserved for unique layouts such as the image
  lightbox, slide-over panel, galleries and charts.
- The teal brand color is defined in `src/styles/app.css` by overriding
  `--bs-primary`, the link colors, and the few Bootstrap components whose
  primary colors are compiled into the stylesheet. Downstream apps can override
  the same variables to re-theme the exported components.
- Exported components accept a `class` prop where an outer wrapper exists.

## Scripts

- `pnpm dev` — Vite dev server
- `pnpm build` — production build to `dist/`
- `pnpm build:svelte` — library build to `dist-lib/`
- `pnpm check` — svelte-check + tsc
