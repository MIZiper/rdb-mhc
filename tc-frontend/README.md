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

## Scripts

- `pnpm dev` — Vite dev server
- `pnpm build` — production build to `dist/`
- `pnpm build:svelte` — library build to `dist-lib/`
- `pnpm check` — svelte-check + tsc
