# TC backend (TemplateClient)

FastAPI + PostgreSQL backend for the Resource Database. Stores lightweight,
typed node content, projects it into a cross-type search index, and exposes a
REST API plus optional static hosting of the built frontend.

## Project layout

```
tc/
  app.py            # create_app(): CORS, routers, SPA static mount, lifespan
  main.py           # uvicorn entrypoint (tc.main:app)
  settings.py       # all environment configuration
  auth/
    provider.py     # Keycloak JWT verification
    permissions.py   # roles + visibility/ownership rules + FastAPI deps
  models/           # pydantic API schemas (node, content, file, query)
  content_types/    # per-type descriptors + field extraction + DB seed
  services/
    nodes.py        # content write path, projection, query SQL builder
    files.py        # upload storage + node file linking
    metahub.py      # MetaHub HTTP client
  routes/
    nodes/          # meta.py, content.py, push.py, query.py
    files.py  types.py  config.py  permissions.py  admin.py
  db/
    connection.py   # asyncpg pool
    schema.sql      # single idempotent schema, applied on startup
```

## Environment variables

- `TC_METAHUB` — MetaHub service host (default: `localhost:8033`)
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` / `POSTGRES_HOST` / `POSTGRES_PORT`
- `KEYCLOAK_URL` / `KEYCLOAK_URL_PUBLIC` / `KEYCLOAK_REALM` / `KEYCLOAK_CLIENT_ID` — Keycloak
  (`KEYCLOAK_URL_PUBLIC` is the browser-reachable URL used as the token issuer;
  local development uses realm `master` and client `miz`)
- `TC_STORAGE_ROOT` — directory for uploaded file bytes (default: `./storage`)
- `TC_MAX_UPLOAD_MB` — maximum upload size in MB (default: `25`)
- `FRONTEND_DIST` — when set to a directory, serve it as the SPA at `/`

The schema is applied automatically on startup (`db/schema.sql`, idempotent).

### External source links

Nodes may represent metadata-only resources owned by another application. The source application creates the TC node first, then attaches itself through:

- `GET /api/nodes/{id}/state`
- `PATCH /api/nodes/{id}/state` (`nodes:review`)
- `GET/PUT/DELETE /api/nodes/{id}/source`

`source_system`, `source_id`, `source_part` and `source_url` are stored on the node; the unique source tuple prevents two TC nodes from representing the same app resource part. Status remains TC-owned; applications map statuses to their own frozen set. `dac_web.project`, `tpl.plan` and `tpl.log` are metadata-only built-in types;
they are intended to be created in TC by the user, then linked from the source app.

---

## Stored files

Uploads are written under `TC_STORAGE_ROOT` in a per-type subfolder
(`{TC_STORAGE_ROOT}/{data_type}/...`), with metadata in the `files` table.
Use `POST /api/files?data_type=...` (multipart `file`), then reference the
returned id from node content via a `file_id` field; files are linked to the
node on save and inherit its visibility. `GET /api/files/{id}` and
`GET /api/files/{id}/thumb` serve the bytes.

---

## Cross-type retrieval & aggregation

Content stays in `nodes.content` (JSONB) untouched, but every write also
projects declared fields into the `node_fields` index. Declared fields are
described per type in `tc/content_types/registry.py` and mapped onto
canonical, shareable keys so values from different types can be compared.

- `GET /api/types` — registered type descriptors (fields, preview, ui).
- `GET /api/nodes/fields` — the shared field-key vocabulary.
- `GET /api/nodes/fields/{key}/values` — facets for a keyword key, or
  min/max/count for a numeric key.
- `POST /api/nodes/query` — cross-type search/filter over text, tags,
  types and field conditions.
- `POST /api/nodes/aggregate` — group numeric metrics by field keys and/or tags.
- `GET /api/nodes/data?ids=a,b,c` — batch content fetch.
- `POST /api/admin/reindex` — rebuild projections (and upcast content)
  for all nodes; requires `nodes:edit_any`.

Adding a type is code-only: define a `TypeDescriptor` in
`tc/content_types/registry.py` and (optionally) register a frontend renderer
via `ui.component`.

---

## Role-based access control

All authorization is driven by Keycloak roles. The backend reads roles from
both **Realm roles** and **Client roles** under `resource_access.{KEYCLOAK_CLIENT_ID}`,
merging them into a single set.

### Built-in action roles

| Role | Effect |
|---|---|
| `nodes:create` | Create new nodes |
| `nodes:read_all` | See all nodes regardless of visibility |
| `nodes:edit_any` | Edit any node (bypasses creator check) |
| `nodes:review` | Change node status (draft / pending_review / published / archived) |

**Owner fallback:** a node's creator can always edit and see their own nodes,
even without the roles above.

### Visibility roles

Each node has a `visibility` field (default: `"public"`). To control who can
see non-public nodes, create roles following the pattern `nodes:visibility:{name}`:

| Role | Effect |
|---|---|
| `nodes:visibility:internal` | See nodes with `visibility: "internal"` |
| `nodes:visibility:proj_a` | See nodes with `visibility: "proj_a"` |
| `nodes:visibility:proj_b` | See nodes with `visibility: "proj_b"` |

**Visibility rules** for read endpoints (list, search, get single node):

1. `nodes:read_all` → sees everything
2. `visibility == "public"` → everyone sees
3. `nodes:visibility:{x}` in user's roles → sees nodes with `visibility: "{x}"`
4. Creator of the node → always sees their own

Unauthenticated users can only see `public` nodes.

### Setting up in Keycloak

**Realm roles** (Realm → Roles): `nodes:create`, `nodes:visibility:proj_a`, `nodes:visibility:proj_b`.

**Client roles** (Clients → your-app → Roles):
- `admin` — associate: `nodes:read_all`, `nodes:create`, `nodes:edit_any`, `nodes:review`
- `member_proj_a` — associate: `nodes:create`, `nodes:visibility:proj_a`

### Downstream customization

If you run your own instance with a different Keycloak client, create the same
role names. The backend does not have a hardcoded role list — any role matching
the pattern `nodes:*` or `nodes:visibility:*` is honored.
